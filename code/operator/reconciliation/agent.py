"""
Reconcile Agent spec into Kubernetes resources (Deployment, Job, CronJob,
optional skills ConfigMap, and Service).  Used by the Kopf handlers in main.py.
"""

from __future__ import annotations

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

from models import (
    AgentSpec,
    ConversationConfig,
    MCPServerConfig,
    SkillsConfig,
    TriggerConfig,
    WorkspaceConfig,
)
from .common import (
    CLI_COMMAND,
    DEFAULT_PULL_POLICY,
    build_container_sc,
    build_pod_sc,
    build_resources,
    build_tolerations,
    extra_env,
    llm_env,
    otel_env,
    trigger_env,
)

# ── Constants ────────────────────────────────────────────────────────────────

AGENT_CRD_GROUP = "agents.ai.juliusharing.com"
AGENT_PREFIX = "agent-"
WORKSPACE_VOL = "workspace"
SKILLS_VOL = "custom-skills"
SKILLS_MOUNT = "/skills/bootstrap"

DEFAULT_AGENT_IMAGE = "ghcr.io/juliusharing/agentickube/agent:latest"

# Recommended labels (https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
APP_PART_OF = "agentickube"
APP_MANAGED_BY = "agentickube-operator"


# ── Naming ────────────────────────────────────────────────────────────────────


def agent_deployment_name(name: str) -> str:
    return f"{AGENT_PREFIX}{name}"


def agent_job_name(name: str) -> str:
    return f"{AGENT_PREFIX}{name}"


def agent_cronjob_name(name: str) -> str:
    return f"{AGENT_PREFIX}{name}"


def agent_service_name(name: str) -> str:
    return f"{AGENT_PREFIX}{name}"


def _skills_cm_name(name: str) -> str:
    return f"agent-{name}-skills"


def _agent_recommended_labels(name: str) -> dict[str, str]:
    """Recommended labels for Agent-created resources (Deployment, Job, CronJob, Service, Pod)."""
    return {
        "app.kubernetes.io/name": "agent",
        "app.kubernetes.io/instance": agent_deployment_name(name),
        "app.kubernetes.io/part-of": APP_PART_OF,
        "app.kubernetes.io/managed-by": APP_MANAGED_BY,
        "agent": name,
    }


# ── Agent-specific environment variable builders ─────────────────────────────


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


def _skills_env(
    skills: SkillsConfig | None, has_inline_cm: bool
) -> list[client.V1EnvVar]:
    skills = skills or SkillsConfig()
    env: list[client.V1EnvVar] = []
    if skills.builtin_skills is not None:
        env.append(
            client.V1EnvVar(
                name="BUILTIN_SKILLS", value=",".join(skills.builtin_skills)
            )
        )
    return env


def _prompts_env(spec: AgentSpec) -> list[client.V1EnvVar]:
    """Inject spec.prompts.system_prompt as SYSTEM_PROMPT so the agent uses it."""
    if not spec.prompts or not spec.prompts.system_prompt:
        return []
    return [
        client.V1EnvVar(name="SYSTEM_PROMPT", value=spec.prompts.system_prompt.strip())
    ]


def _build_agent_env(
    spec: AgentSpec, name: str, has_inline_cm: bool
) -> list[client.V1EnvVar]:
    ws = spec.workspace or WorkspaceConfig()
    env = [
        client.V1EnvVar(name="AGENT_NAME", value=name),
        *llm_env(spec.llm),
        *_mcp_env(spec.mcp_servers or []),
        client.V1EnvVar(name="WORKSPACE_DIR", value=ws.path),
        *_conversation_env(spec.conversation),
        *otel_env(spec.open_telemetry, name),
        *_skills_env(spec.skills, has_inline_cm),
        *_prompts_env(spec),
        *extra_env(spec.env or []),
    ]
    return env


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
    name: str, spec: AgentSpec, has_inline_cm: bool
) -> tuple[list[client.V1Volume], list[client.V1VolumeMount]]:
    """Build a projected volume from all operator-provided skill sources."""
    skills = spec.skills or SkillsConfig()
    items = skills.items or []
    sources: list[client.V1VolumeProjection] = []

    if has_inline_cm:
        sources.append(
            client.V1VolumeProjection(
                config_map=client.V1ConfigMapProjection(name=_skills_cm_name(name))
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


# ── Skills ConfigMap lifecycle ────────────────────────────────────────────────


def ensure_agent_skills_cm(
    name: str, namespace: str, spec: AgentSpec, body: dict
) -> bool:
    """Create/update a ConfigMap for inline skills. Returns True if it exists."""
    items = (spec.skills.items if spec.skills else None) or []
    inline = {s.name: s.content for s in items if s.content}

    if not inline:
        _delete_skills_cm(name, namespace)
        return False

    cm_name = _skills_cm_name(name)
    cm = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=cm_name,
            namespace=namespace,
            labels={"app.kubernetes.io/name": "agent", "agent": name},
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


def _delete_skills_cm(name: str, namespace: str) -> None:
    try:
        client.CoreV1Api().delete_namespaced_config_map(
            _skills_cm_name(name), namespace
        )
    except ApiException as e:
        if e.status != 404:
            raise


# ── Agent pod template builder ───────────────────────────────────────────────


def _build_agent_pod_template(
    name: str,
    spec: AgentSpec,
    has_inline_cm: bool,
    *,
    command: list[str] | None = None,
    extra_env_vars: list[client.V1EnvVar] | None = None,
    restart_policy: str | None = None,
) -> client.V1PodTemplateSpec:
    workspace = spec.workspace or WorkspaceConfig()
    ws_path, ws_vol = _workspace_volume(workspace)
    sk_vols, sk_mounts = _skills_volumes(name, spec, has_inline_cm)

    env = _build_agent_env(spec, name, has_inline_cm)
    if extra_env_vars:
        env = [*env, *extra_env_vars]

    ports = None if command else [client.V1ContainerPort(container_port=80)]

    container = client.V1Container(
        name="agent",
        image=(spec.image or "").strip() or DEFAULT_AGENT_IMAGE,
        image_pull_policy=(spec.image_pull_policy or "").strip() or DEFAULT_PULL_POLICY,
        command=command,
        env=env,
        ports=ports,
        volume_mounts=[
            client.V1VolumeMount(name=WORKSPACE_VOL, mount_path=ws_path),
            *sk_mounts,
        ],
        resources=build_resources(spec),
        security_context=build_container_sc(spec),
    )

    return client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=_agent_recommended_labels(name)),
        spec=client.V1PodSpec(
            containers=[container],
            volumes=[ws_vol, *sk_vols],
            restart_policy=restart_policy,
            security_context=build_pod_sc(spec),
            node_selector=spec.node_selector,
            tolerations=build_tolerations(spec),
            service_account_name=(spec.service_account_name or "").strip() or None,
        ),
    )


# ── Agent resource builders ─────────────────────────────────────────────────


def build_agent_deployment(
    name: str,
    namespace: str,
    spec: AgentSpec,
    body: dict,
    has_inline_cm: bool,
) -> client.V1Deployment:
    template = _build_agent_pod_template(name, spec, has_inline_cm)

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=agent_deployment_name(name),
            namespace=namespace,
            labels=_agent_recommended_labels(name),
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"agent": name}),
            template=template,
        ),
    )
    kopf.append_owner_reference(deployment, body)
    kopf.label(deployment, nested="spec.template")
    return deployment


def build_agent_job(
    name: str,
    namespace: str,
    spec: AgentSpec,
    body: dict,
    has_inline_cm: bool,
) -> client.V1Job:
    trigger = spec.trigger or TriggerConfig()
    template = _build_agent_pod_template(
        name,
        spec,
        has_inline_cm,
        command=CLI_COMMAND,
        extra_env_vars=trigger_env(trigger.query),
        restart_policy="Never",
    )

    job = client.V1Job(
        metadata=client.V1ObjectMeta(
            name=agent_job_name(name),
            namespace=namespace,
            labels=_agent_recommended_labels(name),
        ),
        spec=client.V1JobSpec(
            template=template,
            backoff_limit=trigger.backoff_limit,
            ttl_seconds_after_finished=trigger.ttl_seconds_after_finished,
        ),
    )
    kopf.append_owner_reference(job, body)
    return job


def build_agent_cronjob(
    name: str,
    namespace: str,
    spec: AgentSpec,
    body: dict,
    has_inline_cm: bool,
) -> client.V1CronJob:
    trigger = spec.trigger or TriggerConfig()
    template = _build_agent_pod_template(
        name,
        spec,
        has_inline_cm,
        command=CLI_COMMAND,
        extra_env_vars=trigger_env(trigger.query),
        restart_policy="Never",
    )

    cronjob = client.V1CronJob(
        metadata=client.V1ObjectMeta(
            name=agent_cronjob_name(name),
            namespace=namespace,
            labels=_agent_recommended_labels(name),
        ),
        spec=client.V1CronJobSpec(
            schedule=trigger.schedule or "0 * * * *",
            concurrency_policy="Forbid",
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    template=template,
                    backoff_limit=trigger.backoff_limit,
                    ttl_seconds_after_finished=trigger.ttl_seconds_after_finished,
                ),
            ),
        ),
    )
    kopf.append_owner_reference(cronjob, body)
    return cronjob


# ── Agent Service ────────────────────────────────────────────────────────────


def _build_agent_service(name: str, namespace: str, body: dict) -> client.V1Service:
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=agent_service_name(name),
            namespace=namespace,
            labels=_agent_recommended_labels(name),
        ),
        spec=client.V1ServiceSpec(
            selector={"agent": name},
            ports=[client.V1ServicePort(port=80, target_port=80)],
        ),
    )
    kopf.append_owner_reference(svc, body)
    return svc


def ensure_agent_service(name: str, namespace: str, body: dict) -> None:
    svc = _build_agent_service(name, namespace, body)
    svc_name = svc.metadata.name
    core = client.CoreV1Api()
    try:
        core.read_namespaced_service(svc_name, namespace)
        core.patch_namespaced_service(svc_name, namespace, svc)
    except ApiException as e:
        if e.status == 404:
            core.create_namespaced_service(namespace, svc)
        else:
            raise


def delete_agent_service(name: str, namespace: str) -> None:
    try:
        client.CoreV1Api().delete_namespaced_service(
            agent_service_name(name), namespace
        )
    except ApiException as e:
        if e.status != 404:
            raise
