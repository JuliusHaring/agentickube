"""
Kopf operator for Agent CRs (ai.juliusharing.com).
Reconciles Agent spec into a Deployment and deletes it on Agent deletion.
"""

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


def _env_from_spec(spec: dict) -> list[client.V1EnvVar]:
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

    return env_vars


def _deployment_name(agent_name: str) -> str:
    return f"{DEPLOYMENT_NAME_PREFIX}{agent_name}"


def _make_deployment(
    name: str, namespace: str, spec: dict, body: dict
) -> client.V1Deployment:
    deployment_name = _deployment_name(name)
    env_vars = _env_from_spec(spec)

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
                    containers=[
                        client.V1Container(
                            name="agent",
                            image="agentickube:latest",
                            env=env_vars,
                            image_pull_policy="Never",
                            ports=[client.V1ContainerPort(container_port=80)],
                        )
                    ]
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
    logger.info("Deployment created", deployment=deployment.metadata.name)
    return {"deployment": deployment.metadata.name}


@kopf.on.update(AGENT_CRD_GROUP)
def update_agent(
    spec: dict, name: str, namespace: str, logger: kopf.Logger, **_
) -> None:
    deployment_name = _deployment_name(name)
    env_vars = _env_from_spec(spec)
    apps = client.AppsV1Api()
    deployment = apps.read_namespaced_deployment(deployment_name, namespace)
    deployment.spec.template.spec.containers[0].env = env_vars
    apps.patch_namespaced_deployment(deployment_name, namespace, deployment)
    logger.info("Deployment updated", deployment=deployment_name)


@kopf.on.delete(AGENT_CRD_GROUP)
def delete_agent(name: str, namespace: str, logger: kopf.Logger, **_) -> None:
    deployment_name = _deployment_name(name)
    apps = client.AppsV1Api()
    try:
        apps.delete_namespaced_deployment(deployment_name, namespace)
        logger.info("Deployment deleted", deployment=deployment_name)
    except ApiException as e:
        if e.status == 404:
            logger.debug("Deployment already gone", deployment=deployment_name)
        else:
            raise
