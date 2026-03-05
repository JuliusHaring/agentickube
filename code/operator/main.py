"""
Kopf operator for Agent CRs (ai.juliusharing.com).
Reconciles Agent spec into a Deployment and deletes it on Agent deletion.
"""

import copy
import logging.config
import os

import kopf
from shared.logging import get_logger, LOGGING_CONFIG

from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Apply shared logging so operator and kopf use the same format (colored, level, name).
operator_logging = copy.deepcopy(LOGGING_CONFIG)
operator_logging.setdefault("loggers", {})["kopf"] = {
    "level": operator_logging["root"]["level"],
    "handlers": ["console"],
    "propagate": False,
}
logging.config.dictConfig(operator_logging)
logger = get_logger(__name__)

# Prefer in-cluster config when running in a pod; fall back to kubeconfig for local dev.
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

AGENT_CRD_GROUP = "agents.ai.juliusharing.com"
DEPLOYMENT_NAME_PREFIX = "agent-"
WORKSPACE_VOLUME_NAME = "workspace"
CUSTOM_SKILLS_VOLUME_NAME = "custom-skills"
DEFAULT_WORKSPACE_PATH = "/workspace"
SKILLS_BOOTSTRAP_PATH = "/skills/bootstrap"

# Agent container image and pull policy (set via env in operator Deployment for production).
DEFAULT_AGENT_IMAGE = "ghcr.io/juliusharing/agentickube/agent:latest"
AGENT_IMAGE = os.environ.get("AGENT_IMAGE", DEFAULT_AGENT_IMAGE)
AGENT_IMAGE_PULL_POLICY = os.environ.get("AGENT_IMAGE_PULL_POLICY", "IfNotPresent")


def _workspace_from_spec(spec: dict) -> tuple[str, client.V1Volume]:
    """Return (mount_path, volume). Uses PVC if spec.workspace.persistentVolumeClaim.claimName set, else emptyDir."""
    workspace = spec.get("workspace") or {}
    path = (
        workspace.get("path") or DEFAULT_WORKSPACE_PATH
    ).strip() or DEFAULT_WORKSPACE_PATH
    pvc = workspace.get("persistentVolumeClaim") or {}
    claim_name = (pvc.get("claimName") or "").strip()

    if claim_name:
        volume = client.V1Volume(
            name=WORKSPACE_VOLUME_NAME,
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name=claim_name
            ),
        )
    else:
        volume = client.V1Volume(
            name=WORKSPACE_VOLUME_NAME,
            empty_dir=client.V1EmptyDirVolumeSource(),
        )
    return path, volume


def _env_from_spec(spec: dict, agent_name: str = "agent") -> list[client.V1EnvVar]:
    """Build container env vars from Agent spec (LLM + MCP)."""
    llm = spec.get("llm") or {}
    api_key_cfg = llm.get("apiKey") or {}
    api_key = api_key_cfg.get("raw")
    secret_name = api_key_cfg.get("secretName")
    secret_key = api_key_cfg.get("secretKey")

    env_vars = [
        client.V1EnvVar(name="LLM_MODEL_NAME", value=llm.get("modelName", "")),
        client.V1EnvVar(name="LLM_BASE_URL", value=llm.get("baseUrl", "")),
    ]
    if api_key:
        env_vars.append(client.V1EnvVar(name="LLM_API_KEY", value=api_key))
    elif secret_name and secret_key:
        env_vars.append(
            client.V1EnvVar(
                name="LLM_API_KEY",
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=secret_name, key=secret_key
                    )
                ),
            )
        )

    if llm.get("type"):
        env_vars.append(client.V1EnvVar(name="LLM_TYPE", value=llm.get("type")))

    for i, s in enumerate(spec.get("mcpServers") or [], start=1):
        url = (s.get("url") or "").strip()
        transport = (s.get("type") or "streamable_http").strip().lower()
        if transport not in ("sse", "streamable_http"):
            transport = "streamable_http"
        env_vars.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_URL", value=url))
        env_vars.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_TYPE", value=transport))

    workspace_path, _ = _workspace_from_spec(spec)
    env_vars.append(client.V1EnvVar(name="WORKSPACE_DIR", value=workspace_path))

    # Optional conversation memory (per-session history in workspace).
    conv = spec.get("conversation") or {}
    if conv.get("enabled"):
        env_vars.append(
            client.V1EnvVar(name="CONVERSATION_MEMORY_ENABLED", value="true")
        )
        max_hist = conv.get("maxHistory")
        if max_hist is not None:
            n = max(1, min(1000, int(max_hist)))
            env_vars.append(
                client.V1EnvVar(name="CONVERSATION_MAX_HISTORY", value=str(n))
            )

    # Optional OpenTelemetry (OTLP). Agent derives /v1/traces and /v1/metrics from base endpoint.
    otel = spec.get("openTelemetry") or {}
    if otel.get("enabled") and otel.get("endpoint"):
        endpoint = (otel.get("endpoint") or "").strip().rstrip("/")
        env_vars.append(
            client.V1EnvVar(name="OTEL_EXPORTER_OTLP_ENDPOINT", value=endpoint)
        )
        svc_name = otel.get("serviceName", "").strip() or f"agent-{agent_name}"
        env_vars.append(client.V1EnvVar(name="OTEL_SERVICE_NAME", value=svc_name))
        # Ensure resource has service.name for Jaeger/backends (OTEL_SERVICE_NAME takes precedence)
        env_vars.append(
            client.V1EnvVar(
                name="OTEL_RESOURCE_ATTRIBUTES",
                value=f"service.name={svc_name}",
            )
        )
        ratio = otel.get("samplingRatio")
        if ratio is not None:
            r = max(0.0, min(1.0, float(ratio)))
            env_vars.append(
                client.V1EnvVar(
                    name="OTEL_TRACES_SAMPLER", value="parentbased_traceidratio"
                )
            )
            env_vars.append(
                client.V1EnvVar(name="OTEL_TRACES_SAMPLER_ARG", value=str(r))
            )

    return env_vars


def _deployment_name(agent_name: str) -> str:
    return f"{DEPLOYMENT_NAME_PREFIX}{agent_name}"


def _image_from_spec(spec: dict) -> str:
    """Agent container image: spec.image or operator default."""
    return (spec.get("image") or "").strip() or AGENT_IMAGE


def _image_pull_policy_from_spec(spec: dict) -> str:
    """Agent image pull policy: spec.imagePullPolicy or operator default."""
    return (spec.get("imagePullPolicy") or "").strip() or AGENT_IMAGE_PULL_POLICY


def _resources_from_spec(spec: dict) -> client.V1ResourceRequirements | None:
    """Build container resources from spec.resources (requests/limits)."""
    r = spec.get("resources") or {}
    if not r:
        return None
    requests = r.get("requests") or {}
    limits = r.get("limits") or {}
    if not requests and not limits:
        return None
    return client.V1ResourceRequirements(requests=requests, limits=limits)


def _container_security_context_from_spec(
    spec: dict,
) -> client.V1SecurityContext | None:
    """Build container security context from spec.securityContext."""
    sc = spec.get("securityContext") or {}
    if not sc:
        return None
    caps = sc.get("capabilities") or {}
    add = caps.get("add")
    drop = caps.get("drop")
    capabilities = None
    if add is not None or drop is not None:
        capabilities = client.V1SecurityCapabilities(add=add or [], drop=drop or [])
    return client.V1SecurityContext(
        run_as_user=sc.get("runAsUser"),
        run_as_group=sc.get("runAsGroup"),
        run_as_non_root=sc.get("runAsNonRoot"),
        allow_privilege_escalation=sc.get("allowPrivilegeEscalation"),
        read_only_root_filesystem=sc.get("readOnlyRootFilesystem"),
        capabilities=capabilities,
    )


def _pod_security_context_from_spec(spec: dict) -> client.V1PodSecurityContext | None:
    """Build pod security context from spec.podSecurityContext."""
    psc = spec.get("podSecurityContext") or {}
    if not psc:
        return None
    seccomp = psc.get("seccompProfile") or {}
    seccomp_profile = None
    if seccomp:
        seccomp_profile = client.V1SeccompProfile(
            type=seccomp.get("type"),
            localhost_profile=seccomp.get("localhostProfile"),
        )
    return client.V1PodSecurityContext(
        run_as_user=psc.get("runAsUser"),
        run_as_group=psc.get("runAsGroup"),
        run_as_non_root=psc.get("runAsNonRoot"),
        fs_group=psc.get("fsGroup"),
        seccomp_profile=seccomp_profile,
    )


def _tolerations_from_spec(spec: dict) -> list[client.V1Toleration] | None:
    """Build tolerations from spec.tolerations."""
    items = spec.get("tolerations")
    if not items:
        return None
    out = []
    for t in items:
        out.append(
            client.V1Toleration(
                key=t.get("key"),
                operator=t.get("operator"),
                value=t.get("value"),
                effect=t.get("effect"),
                toleration_seconds=t.get("tolerationSeconds"),
            )
        )
    return out


def _skills_configmap_name(agent_name: str) -> str:
    return f"agent-{agent_name}-skills"


def _skills_env_from_spec(
    spec: dict, has_inline_cm: bool = False
) -> list[client.V1EnvVar]:
    """Build SKILLS_* env vars from spec.skills."""
    skills = spec.get("skills") or {}
    env_vars: list[client.V1EnvVar] = []

    # Tell the agent where to find operator-provided skills to seed into workspace on startup.
    items = skills.get("items") or []
    folder = skills.get("bootstrap") or {}
    has_cm_folder = bool((folder.get("configMapRef") or {}).get("name"))
    has_item_refs = any(s.get("configMapRef") for s in items)
    if has_inline_cm or has_cm_folder or has_item_refs:
        env_vars.append(
            client.V1EnvVar(name="SKILLS_BOOTSTRAP_DIR", value=SKILLS_BOOTSTRAP_PATH)
        )

    builtins = skills.get("builtinSkills")
    if builtins is not None:
        env_vars.append(
            client.V1EnvVar(name="SKILLS_BUILTINS", value=",".join(builtins))
        )

    return env_vars


def _ensure_skills_configmap(name: str, namespace: str, spec: dict, body: dict) -> bool:
    """Create/update a ConfigMap for inline custom skills. Returns True if ConfigMap exists."""
    skills = spec.get("skills") or {}
    custom = skills.get("items") or []
    inline_skills = {
        s["name"]: s["content"] for s in custom if s.get("content") and s.get("name")
    }
    if not inline_skills:
        _delete_skills_configmap(name, namespace)
        return False

    cm_name = _skills_configmap_name(name)
    data = {f"{k}.md": v for k, v in inline_skills.items()}
    cm = client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name=cm_name,
            namespace=namespace,
            labels={"app.kubernetes.io/name": "agent", "agent": name},
        ),
        data=data,
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


def _delete_skills_configmap(name: str, namespace: str) -> None:
    core = client.CoreV1Api()
    try:
        core.delete_namespaced_config_map(_skills_configmap_name(name), namespace)
    except ApiException as e:
        if e.status != 404:
            raise


def _skills_volumes_and_mounts(
    agent_name: str, spec: dict, has_inline_cm: bool
) -> tuple[list[client.V1Volume], list[client.V1VolumeMount]]:
    """Build a projected bootstrap volume from operator-provided skills.

    All sources are merged into /skills/bootstrap (read-only). The agent seeds
    these into the workspace on startup; skills are read/written from there.
    """
    skills = spec.get("skills") or {}
    custom = skills.get("items") or []
    folder = skills.get("bootstrap") or {}

    sources: list[client.V1VolumeProjection] = []

    if has_inline_cm:
        sources.append(
            client.V1VolumeProjection(
                config_map=client.V1ConfigMapProjection(
                    name=_skills_configmap_name(agent_name),
                )
            )
        )

    cm_ref = folder.get("configMapRef") or {}
    if cm_ref.get("name"):
        sources.append(
            client.V1VolumeProjection(
                config_map=client.V1ConfigMapProjection(name=cm_ref["name"])
            )
        )

    for s in custom:
        ref = s.get("configMapRef")
        if ref and ref.get("name"):
            key = ref.get("key") or "SKILL.md"
            skill_name = s.get("name") or ref["name"]
            sources.append(
                client.V1VolumeProjection(
                    config_map=client.V1ConfigMapProjection(
                        name=ref["name"],
                        items=[client.V1KeyToPath(key=key, path=f"{skill_name}.md")],
                    )
                )
            )

    if not sources:
        return [], []

    volume = client.V1Volume(
        name=CUSTOM_SKILLS_VOLUME_NAME,
        projected=client.V1ProjectedVolumeSource(sources=sources),
    )
    mount = client.V1VolumeMount(
        name=CUSTOM_SKILLS_VOLUME_NAME,
        mount_path=SKILLS_BOOTSTRAP_PATH,
        read_only=True,
    )
    return [volume], [mount]


def _extra_env_from_spec(spec: dict) -> list[client.V1EnvVar]:
    """Build extra env vars from spec.env (name/value or valueFrom)."""
    env_spec = spec.get("env") or []
    out = []
    for e in env_spec:
        name = (e.get("name") or "").strip()
        if not name:
            continue
        value = e.get("value")
        value_from = e.get("valueFrom")
        if value_from:
            secret_ref = value_from.get("secretKeyRef")
            cm_ref = value_from.get("configMapKeyRef")
            src = None
            if secret_ref:
                src = client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=secret_ref.get("name"),
                        key=secret_ref.get("key"),
                    )
                )
            elif cm_ref:
                src = client.V1EnvVarSource(
                    config_map_key_ref=client.V1ConfigMapKeySelector(
                        name=cm_ref.get("name"),
                        key=cm_ref.get("key"),
                    )
                )
            if src:
                out.append(client.V1EnvVar(name=name, value_from=src))
        elif value is not None:
            out.append(client.V1EnvVar(name=name, value=str(value)))
    return out


def _make_deployment(
    name: str,
    namespace: str,
    spec: dict,
    body: dict,
    has_inline_skills_cm: bool = False,
) -> client.V1Deployment:
    deployment_name = _deployment_name(name)
    env_vars = (
        _env_from_spec(spec, agent_name=name)
        + _skills_env_from_spec(spec, has_inline_cm=has_inline_skills_cm)
        + _extra_env_from_spec(spec)
    )
    workspace_path, workspace_volume = _workspace_from_spec(spec)
    skills_volumes, skills_mounts = _skills_volumes_and_mounts(
        name, spec, has_inline_skills_cm
    )
    image = _image_from_spec(spec)
    image_pull_policy = _image_pull_policy_from_spec(spec)
    resources = _resources_from_spec(spec)
    container_security_context = _container_security_context_from_spec(spec)
    pod_security_context = _pod_security_context_from_spec(spec)
    node_selector = spec.get("nodeSelector")
    tolerations = _tolerations_from_spec(spec)
    service_account = (spec.get("serviceAccountName") or "").strip() or None

    volume_mounts = [
        client.V1VolumeMount(
            name=WORKSPACE_VOLUME_NAME,
            mount_path=workspace_path,
        )
    ] + skills_mounts

    container = client.V1Container(
        name="agent",
        image=image,
        env=env_vars,
        image_pull_policy=image_pull_policy,
        ports=[client.V1ContainerPort(container_port=80)],
        volume_mounts=volume_mounts,
        resources=resources,
        security_context=container_security_context,
    )

    pod_spec = client.V1PodSpec(
        volumes=[workspace_volume] + skills_volumes,
        containers=[container],
        security_context=pod_security_context,
        node_selector=node_selector,
        tolerations=tolerations,
        service_account_name=service_account,
    )

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=deployment_name,
            namespace=namespace,
            labels={"app.kubernetes.io/name": "agent", "agent": name},
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"agent": name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"agent": name}),
                spec=pod_spec,
            ),
        ),
    )
    kopf.append_owner_reference(deployment, body)
    kopf.label(deployment, nested="spec.template")
    return deployment


@kopf.on.create(AGENT_CRD_GROUP)
def create_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> dict:
    has_inline_cm = _ensure_skills_configmap(name, namespace, spec, body)
    deployment = _make_deployment(
        name, namespace, spec, body, has_inline_skills_cm=has_inline_cm
    )
    apps = client.AppsV1Api()
    apps.create_namespaced_deployment(namespace=namespace, body=deployment)
    logger.info("Deployment created: %s", deployment.metadata.name)
    return {"deployment": deployment.metadata.name}


@kopf.on.update(AGENT_CRD_GROUP)
def update_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    has_inline_cm = _ensure_skills_configmap(name, namespace, spec, body)
    deployment_name = _deployment_name(name)
    env_vars = (
        _env_from_spec(spec, agent_name=name)
        + _skills_env_from_spec(spec, has_inline_cm=has_inline_cm)
        + _extra_env_from_spec(spec)
    )
    workspace_path, workspace_volume = _workspace_from_spec(spec)
    skills_volumes, skills_mounts = _skills_volumes_and_mounts(
        name, spec, has_inline_cm
    )
    image = _image_from_spec(spec)
    image_pull_policy = _image_pull_policy_from_spec(spec)
    apps = client.AppsV1Api()
    deployment = apps.read_namespaced_deployment(deployment_name, namespace)

    pod_spec = deployment.spec.template.spec
    pod_spec.volumes = [workspace_volume] + skills_volumes
    pod_spec.security_context = _pod_security_context_from_spec(spec)
    pod_spec.node_selector = spec.get("nodeSelector")
    pod_spec.tolerations = _tolerations_from_spec(spec)
    pod_spec.service_account_name = (
        spec.get("serviceAccountName") or ""
    ).strip() or None

    container = deployment.spec.template.spec.containers[0]
    container.image = image
    container.image_pull_policy = image_pull_policy
    container.env = env_vars
    container.volume_mounts = [
        client.V1VolumeMount(name=WORKSPACE_VOLUME_NAME, mount_path=workspace_path)
    ] + skills_mounts
    container.resources = _resources_from_spec(spec)
    container.security_context = _container_security_context_from_spec(spec)

    apps.patch_namespaced_deployment(deployment_name, namespace, deployment)
    logger.info("Deployment updated: %s", deployment_name)


@kopf.on.delete(AGENT_CRD_GROUP)
def delete_agent(name: str, namespace: str, **_) -> None:
    deployment_name = _deployment_name(name)
    apps = client.AppsV1Api()
    try:
        apps.delete_namespaced_deployment(deployment_name, namespace)
        logger.info("Deployment deleted: %s", deployment_name)
    except ApiException as e:
        if e.status == 404:
            logger.debug("Deployment already gone: %s", deployment_name)
        else:
            raise
