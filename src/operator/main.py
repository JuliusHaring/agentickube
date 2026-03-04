"""
Kopf operator for Agent CRs (ai.juliusharing.com).
Reconciles Agent spec into a Deployment and deletes it on Agent deletion.
"""

import os

import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Prefer in-cluster config when running in a pod; fall back to kubeconfig for local dev.
try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()

AGENT_CRD_GROUP = "agents.ai.juliusharing.com"
DEPLOYMENT_NAME_PREFIX = "agent-"
WORKSPACE_VOLUME_NAME = "workspace"
DEFAULT_WORKSPACE_PATH = "/workspace"

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
        client.V1EnvVar(name="MODEL_NAME", value=llm.get("modelName", "")),
        client.V1EnvVar(name="BASE_URL", value=llm.get("baseUrl", "")),
    ]
    if api_key:
        env_vars.append(client.V1EnvVar(name="API_KEY", value=api_key))
    elif secret_name and secret_key:
        env_vars.append(
            client.V1EnvVar(
                name="API_KEY",
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=secret_name, key=secret_key
                    )
                ),
            )
        )

    for i, s in enumerate(spec.get("mcpServers") or [], start=1):
        url = (s.get("url") or "").strip()
        transport = (s.get("type") or "streamable_http").strip().lower()
        if transport not in ("sse", "streamable_http"):
            transport = "streamable_http"
        env_vars.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_URL", value=url))
        env_vars.append(client.V1EnvVar(name=f"MCP_SERVER_{i}_TYPE", value=transport))

    workspace_path, _ = _workspace_from_spec(spec)
    env_vars.append(client.V1EnvVar(name="WORKSPACE_DIR", value=workspace_path))

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


def _make_deployment(
    name: str, namespace: str, spec: dict, body: dict
) -> client.V1Deployment:
    deployment_name = _deployment_name(name)
    env_vars = _env_from_spec(spec, agent_name=name)
    workspace_path, workspace_volume = _workspace_from_spec(spec)
    image = _image_from_spec(spec)
    image_pull_policy = _image_pull_policy_from_spec(spec)

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
                spec=client.V1PodSpec(
                    volumes=[workspace_volume],
                    containers=[
                        client.V1Container(
                            name="agent",
                            image=image,
                            env=env_vars,
                            image_pull_policy=image_pull_policy,
                            ports=[client.V1ContainerPort(container_port=80)],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name=WORKSPACE_VOLUME_NAME,
                                    mount_path=workspace_path,
                                )
                            ],
                        )
                    ],
                ),
            ),
        ),
    )
    kopf.append_owner_reference(deployment, body)
    kopf.label(deployment, nested="spec.template")
    return deployment


@kopf.on.create(AGENT_CRD_GROUP)
def create_agent(
    spec: dict, name: str, namespace: str, body: dict, logger: kopf.Logger, **_
) -> dict:
    deployment = _make_deployment(name, namespace, spec, body)
    apps = client.AppsV1Api()
    apps.create_namespaced_deployment(namespace=namespace, body=deployment)
    logger.info("Deployment created: %s", deployment.metadata.name)
    return {"deployment": deployment.metadata.name}


@kopf.on.update(AGENT_CRD_GROUP)
def update_agent(
    spec: dict, name: str, namespace: str, logger: kopf.Logger, **_
) -> None:
    deployment_name = _deployment_name(name)
    env_vars = _env_from_spec(spec, agent_name=name)
    workspace_path, workspace_volume = _workspace_from_spec(spec)
    image = _image_from_spec(spec)
    image_pull_policy = _image_pull_policy_from_spec(spec)
    apps = client.AppsV1Api()
    deployment = apps.read_namespaced_deployment(deployment_name, namespace)
    deployment.spec.template.spec.volumes = [workspace_volume]
    deployment.spec.template.spec.containers[0].image = image
    deployment.spec.template.spec.containers[0].image_pull_policy = image_pull_policy
    deployment.spec.template.spec.containers[0].env = env_vars
    deployment.spec.template.spec.containers[0].volume_mounts = [
        client.V1VolumeMount(name=WORKSPACE_VOLUME_NAME, mount_path=workspace_path)
    ]
    apps.patch_namespaced_deployment(deployment_name, namespace, deployment)
    logger.info("Deployment updated: %s", deployment_name)


@kopf.on.delete(AGENT_CRD_GROUP)
def delete_agent(name: str, namespace: str, logger: kopf.Logger, **_) -> None:
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
