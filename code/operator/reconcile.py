"""
Reconcile Agent spec into Kubernetes resources (Deployment, optional skills ConfigMap).
Used by the Kopf handlers in main.py.
"""

from __future__ import annotations

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

from models import (
    AgentSpec,
    ConversationConfig,
    EnvVar,
    LLMConfig,
    MCPServerConfig,
    OpenTelemetryConfig,
    SkillsConfig,
    WorkspaceConfig,
)

# ── Constants ────────────────────────────────────────────────────────────────

CRD_GROUP = "agents.ai.juliusharing.com"
DEPLOYMENT_PREFIX = "agent-"
WORKSPACE_VOL = "workspace"
SKILLS_VOL = "custom-skills"
SKILLS_MOUNT = "/skills/bootstrap"

DEFAULT_IMAGE = "ghcr.io/juliusharing/agentickube/agent:latest"
DEFAULT_PULL_POLICY = "IfNotPresent"


# ── Naming ────────────────────────────────────────────────────────────────────


def deployment_name(agent: str) -> str:
    return f"{DEPLOYMENT_PREFIX}{agent}"


def _skills_cm_name(agent: str) -> str:
    return f"agent-{agent}-skills"


# ── Environment variable builders ─────────────────────────────────────────────


def _llm_env(llm: LLMConfig | None) -> list[client.V1EnvVar]:
    llm = llm or LLMConfig()
    env = [
        client.V1EnvVar(name="LLM_MODEL_NAME", value=llm.model_name or ""),
        client.V1EnvVar(name="LLM_BASE_URL", value=llm.base_url or ""),
    ]
    if llm.api_key:
        key = llm.api_key
        if key.raw:
            env.append(client.V1EnvVar(name="LLM_API_KEY", value=key.raw))
        elif key.secret_name and key.secret_key:
            env.append(
                client.V1EnvVar(
                    name="LLM_API_KEY",
                    value_from=client.V1EnvVarSource(
                        secret_key_ref=client.V1SecretKeySelector(
                            name=key.secret_name, key=key.secret_key
                        )
                    ),
                )
            )
    if llm.provider:
        env.append(client.V1EnvVar(name="LLM_TYPE", value=llm.provider))
    return env


def _mcp_env(servers: list[MCPServerConfig]) -> list[client.V1EnvVar]:
    env: list[client.V1EnvVar] = []
    for i, srv in enumerate(servers, start=1):
        transport = srv.type.strip().lower()
        if transport not in ("sse", "streamable_http"):
            transport = "streamable_http"
        env.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_URL", value=srv.url.strip()))
        env.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_TYPE", value=transport))
    return env


def _conversation_env(conv: ConversationConfig | None) -> list[client.V1EnvVar]:
    if not conv or not conv.enabled:
        return []
    n = max(1, min(1000, conv.max_history))
    return [
        client.V1EnvVar(name="CONVERSATION_MEMORY_ENABLED", value="true"),
        client.V1EnvVar(name="CONVERSATION_MAX_HISTORY", value=str(n)),
    ]


def _otel_env(
    otel: OpenTelemetryConfig | None, agent_name: str
) -> list[client.V1EnvVar]:
    if not otel or not otel.enabled or not otel.endpoint:
        return []
    endpoint = otel.endpoint.strip().rstrip("/")
    svc = (otel.service_name or "").strip() or f"agent-{agent_name}"
    env = [
        client.V1EnvVar(name="OTEL_EXPORTER_OTLP_ENDPOINT", value=endpoint),
        client.V1EnvVar(name="OTEL_SERVICE_NAME", value=svc),
        client.V1EnvVar(name="OTEL_RESOURCE_ATTRIBUTES", value=f"service.name={svc}"),
    ]
    if otel.sampling_ratio is not None:
        ratio = max(0.0, min(1.0, otel.sampling_ratio))
        env.append(
            client.V1EnvVar(
                name="OTEL_TRACES_SAMPLER", value="parentbased_traceidratio"
            )
        )
        env.append(client.V1EnvVar(name="OTEL_TRACES_SAMPLER_ARG", value=str(ratio)))
    return env


def _skills_env(
    skills: SkillsConfig | None, has_inline_cm: bool
) -> list[client.V1EnvVar]:
    skills = skills or SkillsConfig()
    items = skills.items or []
    env: list[client.V1EnvVar] = []

    bootstrap_cm = skills.bootstrap.config_map_ref if skills.bootstrap else None
    has_cm_folder = bootstrap_cm is not None and bootstrap_cm.name is not None
    has_item_refs = any(s.config_map_ref for s in items)

    if has_inline_cm or has_cm_folder or has_item_refs:
        env.append(client.V1EnvVar(name="SKILLS_BOOTSTRAP_DIR", value=SKILLS_MOUNT))

    if skills.builtin_skills is not None:
        env.append(
            client.V1EnvVar(
                name="SKILLS_BUILTINS", value=",".join(skills.builtin_skills)
            )
        )
    return env


def _extra_env(env_vars: list[EnvVar]) -> list[client.V1EnvVar]:
    out: list[client.V1EnvVar] = []
    for ev in env_vars:
        if ev.value_from:
            src = ev.value_from
            if src.secret_key_ref and src.secret_key_ref.name:
                out.append(
                    client.V1EnvVar(
                        name=ev.name,
                        value_from=client.V1EnvVarSource(
                            secret_key_ref=client.V1SecretKeySelector(
                                name=src.secret_key_ref.name,
                                key=src.secret_key_ref.key,
                            )
                        ),
                    )
                )
            elif src.config_map_key_ref and src.config_map_key_ref.name:
                out.append(
                    client.V1EnvVar(
                        name=ev.name,
                        value_from=client.V1EnvVarSource(
                            config_map_key_ref=client.V1ConfigMapKeySelector(
                                name=src.config_map_key_ref.name,
                                key=src.config_map_key_ref.key,
                            )
                        ),
                    )
                )
        elif ev.value is not None:
            out.append(client.V1EnvVar(name=ev.name, value=str(ev.value)))
    return out


def _build_env_vars(
    spec: AgentSpec, agent_name: str, has_inline_cm: bool
) -> list[client.V1EnvVar]:
    ws = spec.workspace or WorkspaceConfig()
    return [
        *_llm_env(spec.llm),
        *_mcp_env(spec.mcp_servers or []),
        client.V1EnvVar(name="WORKSPACE_DIR", value=ws.path),
        *_conversation_env(spec.conversation),
        *_otel_env(spec.open_telemetry, agent_name),
        *_skills_env(spec.skills, has_inline_cm),
        *_extra_env(spec.env or []),
    ]


# ── Volume builders ───────────────────────────────────────────────────────────


def _workspace_volume(workspace: WorkspaceConfig) -> tuple[str, client.V1Volume]:
    pvc = workspace.persistent_volume_claim
    if pvc and pvc.claim_name:
        vol = client.V1Volume(
            name=WORKSPACE_VOL,
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name=pvc.claim_name
            ),
        )
    else:
        vol = client.V1Volume(
            name=WORKSPACE_VOL, empty_dir=client.V1EmptyDirVolumeSource()
        )
    return workspace.path, vol


def _skills_volumes(
    agent_name: str, spec: AgentSpec, has_inline_cm: bool
) -> tuple[list[client.V1Volume], list[client.V1VolumeMount]]:
    """Build a projected volume from all operator-provided skill sources."""
    skills = spec.skills or SkillsConfig()
    items = skills.items or []
    sources: list[client.V1VolumeProjection] = []

    if has_inline_cm:
        sources.append(
            client.V1VolumeProjection(
                config_map=client.V1ConfigMapProjection(
                    name=_skills_cm_name(agent_name)
                )
            )
        )

    bootstrap_cm = skills.bootstrap.config_map_ref if skills.bootstrap else None
    if bootstrap_cm and bootstrap_cm.name:
        sources.append(
            client.V1VolumeProjection(
                config_map=client.V1ConfigMapProjection(name=bootstrap_cm.name)
            )
        )

    for item in items:
        ref = item.config_map_ref
        if ref and ref.name:
            sources.append(
                client.V1VolumeProjection(
                    config_map=client.V1ConfigMapProjection(
                        name=ref.name,
                        items=[client.V1KeyToPath(key=ref.key, path=f"{item.name}.md")],
                    )
                )
            )

    if not sources:
        return [], []

    vol = client.V1Volume(
        name=SKILLS_VOL,
        projected=client.V1ProjectedVolumeSource(sources=sources),
    )
    mount = client.V1VolumeMount(
        name=SKILLS_VOL, mount_path=SKILLS_MOUNT, read_only=True
    )
    return [vol], [mount]


# ── K8s object converters ──────────────────────────────────────────────────────


def _build_resources(
    spec: AgentSpec,
) -> client.V1ResourceRequirements | None:
    r = spec.resources
    if not r or (not r.requests and not r.limits):
        return None
    return client.V1ResourceRequirements(
        requests=r.requests or None, limits=r.limits or None
    )


def _build_container_sc(
    spec: AgentSpec,
) -> client.V1SecurityContext | None:
    sc = spec.security_context
    if not sc:
        return None
    caps = None
    if sc.capabilities:
        caps = client.V1SecurityCapabilities(
            add=sc.capabilities.add or [], drop=sc.capabilities.drop or []
        )
    return client.V1SecurityContext(
        run_as_user=sc.run_as_user,
        run_as_group=sc.run_as_group,
        run_as_non_root=sc.run_as_non_root,
        allow_privilege_escalation=sc.allow_privilege_escalation,
        read_only_root_filesystem=sc.read_only_root_filesystem,
        capabilities=caps,
    )


def _build_pod_sc(spec: AgentSpec) -> client.V1PodSecurityContext | None:
    psc = spec.pod_security_context
    if not psc:
        return None
    seccomp = None
    if psc.seccomp_profile:
        seccomp = client.V1SeccompProfile(
            type=psc.seccomp_profile.type,
            localhost_profile=psc.seccomp_profile.localhost_profile,
        )
    return client.V1PodSecurityContext(
        run_as_user=psc.run_as_user,
        run_as_group=psc.run_as_group,
        run_as_non_root=psc.run_as_non_root,
        fs_group=psc.fs_group,
        seccomp_profile=seccomp,
    )


def _build_tolerations(
    spec: AgentSpec,
) -> list[client.V1Toleration] | None:
    if not spec.tolerations:
        return None
    return [
        client.V1Toleration(
            key=t.key,
            operator=t.operator,
            value=t.value,
            effect=t.effect,
            toleration_seconds=t.toleration_seconds,
        )
        for t in spec.tolerations
    ]


# ── Skills ConfigMap lifecycle ────────────────────────────────────────────────


def ensure_skills_cm(
    agent_name: str, namespace: str, spec: AgentSpec, body: dict
) -> bool:
    """Create/update a ConfigMap for inline skills. Returns True if it exists."""
    items = (spec.skills.items if spec.skills else None) or []
    inline = {s.name: s.content for s in items if s.content}

    if not inline:
        _delete_skills_cm(agent_name, namespace)
        return False

    cm_name = _skills_cm_name(agent_name)
    cm = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=cm_name,
            namespace=namespace,
            labels={"app.kubernetes.io/name": "agent", "agent": agent_name},
        ),
        data={f"{k}.md": v for k, v in inline.items()},
    )
    kopf.append_owner_reference(cm, body)

    core = client.CoreV1Api()
    try:
        core.read_namespaced_config_map(cm_name, namespace)
        core.patch_namespaced_config_map(cm_name, namespace, cm)
    except ApiException as e:
        if e.status == 404:
            core.create_namespaced_config_map(namespace, cm)
        else:
            raise
    return True


def _delete_skills_cm(agent_name: str, namespace: str) -> None:
    try:
        client.CoreV1Api().delete_namespaced_config_map(
            _skills_cm_name(agent_name), namespace
        )
    except ApiException as e:
        if e.status != 404:
            raise


# ── Deployment builder ───────────────────────────────────────────────────────


def build_deployment(
    name: str,
    namespace: str,
    spec: AgentSpec,
    body: dict,
    has_inline_cm: bool,
) -> client.V1Deployment:
    workspace = spec.workspace or WorkspaceConfig()
    ws_path, ws_vol = _workspace_volume(workspace)
    sk_vols, sk_mounts = _skills_volumes(name, spec, has_inline_cm)

    container = client.V1Container(
        name="agent",
        image=(spec.image or "").strip() or DEFAULT_IMAGE,
        image_pull_policy=(spec.image_pull_policy or "").strip() or DEFAULT_PULL_POLICY,
        env=_build_env_vars(spec, name, has_inline_cm),
        ports=[client.V1ContainerPort(container_port=80)],
        volume_mounts=[
            client.V1VolumeMount(name=WORKSPACE_VOL, mount_path=ws_path),
            *sk_mounts,
        ],
        resources=_build_resources(spec),
        security_context=_build_container_sc(spec),
    )

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=deployment_name(name),
            namespace=namespace,
            labels={"app.kubernetes.io/name": "agent", "agent": name},
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"agent": name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"agent": name}),
                spec=client.V1PodSpec(
                    containers=[container],
                    volumes=[ws_vol, *sk_vols],
                    security_context=_build_pod_sc(spec),
                    node_selector=spec.node_selector,
                    tolerations=_build_tolerations(spec),
                    service_account_name=(spec.service_account_name or "").strip()
                    or None,
                ),
            ),
        ),
    )
    kopf.append_owner_reference(deployment, body)
    kopf.label(deployment, nested="spec.template")
    return deployment
