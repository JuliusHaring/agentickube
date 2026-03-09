"""
Reconcile Orchestrator spec into Kubernetes resources (Deployment, Job, CronJob,
and Service for http mode).  Used by the Kopf handlers in main.py.
"""

from __future__ import annotations

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

from models import (
    OrchestratorSpec,
    StrategyConfig,
    TriggerConfig,
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

ORCHESTRATOR_CRD_GROUP = "orchestrators.ai.juliusharing.com"
ORCHESTRATOR_PREFIX = "orchestrator-"

DEFAULT_ORCHESTRATOR_IMAGE = "ghcr.io/juliusharing/agentickube/orchestrator:latest"

# Recommended labels (https://kubernetes.io/docs/concepts/overview/working-with-objects/common-labels/)
APP_PART_OF = "agentickube"
APP_MANAGED_BY = "agentickube-operator"


# ── Naming ───────────────────────────────────────────────────────────────────


def orchestrator_deployment_name(name: str) -> str:
    return f"{ORCHESTRATOR_PREFIX}{name}"


def orchestrator_job_name(name: str) -> str:
    return f"{ORCHESTRATOR_PREFIX}{name}"


def orchestrator_cronjob_name(name: str) -> str:
    return f"{ORCHESTRATOR_PREFIX}{name}"


def orchestrator_service_name(name: str) -> str:
    return f"{ORCHESTRATOR_PREFIX}{name}"


def _orchestrator_recommended_labels(name: str) -> dict[str, str]:
    """Recommended labels for Orchestrator-created resources (Deployment, Job, CronJob, Service, Pod)."""
    return {
        "app.kubernetes.io/name": "orchestrator",
        "app.kubernetes.io/instance": orchestrator_deployment_name(name),
        "app.kubernetes.io/part-of": APP_PART_OF,
        "app.kubernetes.io/managed-by": APP_MANAGED_BY,
        "orchestrator": name,
    }


# ── Orchestrator-specific environment variable builders ──────────────────────


def _orchestrator_env(spec: OrchestratorSpec, name: str) -> list[client.V1EnvVar]:
    strategy = spec.strategy or StrategyConfig()
    env: list[client.V1EnvVar] = [
        client.V1EnvVar(name="ORCHESTRATOR_NAME", value=name),
        client.V1EnvVar(name="ORCHESTRATOR_STRATEGY", value=strategy.type),
        client.V1EnvVar(name="ORCHESTRATOR_MAX_ROUNDS", value=str(strategy.max_rounds)),
    ]
    return env


def _agent_ref_env(spec: OrchestratorSpec, namespace: str) -> list[client.V1EnvVar]:
    env: list[client.V1EnvVar] = []
    for i, agent in enumerate(spec.agents, start=1):
        env.append(
            client.V1EnvVar(name=f"ORCHESTRATOR_AGENT_{i}_NAME", value=agent.name)
        )
        url = (
            agent.url
            or f"http://agent-{agent.name}.{namespace}.svc.cluster.local/query"
        )
        env.append(client.V1EnvVar(name=f"ORCHESTRATOR_AGENT_{i}_URL", value=url))
        if agent.description:
            env.append(
                client.V1EnvVar(
                    name=f"ORCHESTRATOR_AGENT_{i}_DESCRIPTION",
                    value=agent.description,
                )
            )
    return env


def _build_orchestrator_env(
    spec: OrchestratorSpec, name: str, namespace: str
) -> list[client.V1EnvVar]:
    return [
        *_orchestrator_env(spec, name),
        *llm_env(spec.llm),
        *_agent_ref_env(spec, namespace),
        *otel_env(spec.open_telemetry, name),
        *extra_env(spec.env or []),
    ]


# ── Orchestrator pod template builder ───────────────────────────────────────


def _build_orchestrator_pod_template(
    name: str,
    namespace: str,
    spec: OrchestratorSpec,
    *,
    command: list[str] | None = None,
    extra_env_vars: list[client.V1EnvVar] | None = None,
    restart_policy: str | None = None,
) -> client.V1PodTemplateSpec:
    env = _build_orchestrator_env(spec, name, namespace)
    if extra_env_vars:
        env = [*env, *extra_env_vars]

    ports = None if command else [client.V1ContainerPort(container_port=80)]

    container = client.V1Container(
        name="orchestrator",
        image=(spec.image or "").strip() or DEFAULT_ORCHESTRATOR_IMAGE,
        image_pull_policy=(spec.image_pull_policy or "").strip() or DEFAULT_PULL_POLICY,
        command=command,
        env=env,
        ports=ports,
        resources=build_resources(spec),
        security_context=build_container_sc(spec),
    )

    return client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels=_orchestrator_recommended_labels(name)),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy=restart_policy,
            security_context=build_pod_sc(spec),
            node_selector=spec.node_selector,
            tolerations=build_tolerations(spec),
            service_account_name=(spec.service_account_name or "").strip() or None,
        ),
    )


# ── Orchestrator resource builders ──────────────────────────────────────────


def build_orchestrator_deployment(
    name: str,
    namespace: str,
    spec: OrchestratorSpec,
    body: dict,
) -> client.V1Deployment:
    template = _build_orchestrator_pod_template(name, namespace, spec)

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name=orchestrator_deployment_name(name),
            namespace=namespace,
            labels=_orchestrator_recommended_labels(name),
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(match_labels={"orchestrator": name}),
            template=template,
        ),
    )
    kopf.append_owner_reference(deployment, body)  # type: ignore[invalid-argument-type]
    kopf.label(deployment, nested="spec.template")
    return deployment


def build_orchestrator_job(
    name: str,
    namespace: str,
    spec: OrchestratorSpec,
    body: dict,
) -> client.V1Job:
    trigger = spec.trigger or TriggerConfig()
    template = _build_orchestrator_pod_template(
        name,
        namespace,
        spec,
        command=CLI_COMMAND,
        extra_env_vars=trigger_env(trigger.query),
        restart_policy="Never",
    )

    job = client.V1Job(
        metadata=client.V1ObjectMeta(
            name=orchestrator_job_name(name),
            namespace=namespace,
            labels=_orchestrator_recommended_labels(name),
        ),
        spec=client.V1JobSpec(
            template=template,
            backoff_limit=trigger.backoff_limit,
            ttl_seconds_after_finished=trigger.ttl_seconds_after_finished,
        ),
    )
    kopf.append_owner_reference(job, body)  # type: ignore[invalid-argument-type]
    return job


def build_orchestrator_cronjob(
    name: str,
    namespace: str,
    spec: OrchestratorSpec,
    body: dict,
) -> client.V1CronJob:
    trigger = spec.trigger or TriggerConfig()
    template = _build_orchestrator_pod_template(
        name,
        namespace,
        spec,
        command=CLI_COMMAND,
        extra_env_vars=trigger_env(trigger.query),
        restart_policy="Never",
    )

    cronjob = client.V1CronJob(
        metadata=client.V1ObjectMeta(
            name=orchestrator_cronjob_name(name),
            namespace=namespace,
            labels=_orchestrator_recommended_labels(name),
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
    kopf.append_owner_reference(cronjob, body)  # type: ignore[invalid-argument-type]
    return cronjob


# ── Orchestrator Service ─────────────────────────────────────────────────────


def _build_orchestrator_service(
    name: str, namespace: str, body: dict
) -> client.V1Service:
    svc = client.V1Service(
        metadata=client.V1ObjectMeta(
            name=orchestrator_service_name(name),
            namespace=namespace,
            labels=_orchestrator_recommended_labels(name),
        ),
        spec=client.V1ServiceSpec(
            selector={"orchestrator": name},
            ports=[client.V1ServicePort(port=80, target_port=80)],
        ),
    )
    kopf.append_owner_reference(svc, body)  # type: ignore[invalid-argument-type]
    return svc


def ensure_orchestrator_service(name: str, namespace: str, body: dict) -> None:
    svc = _build_orchestrator_service(name, namespace, body)
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


def delete_orchestrator_service(name: str, namespace: str) -> None:
    try:
        client.CoreV1Api().delete_namespaced_service(
            orchestrator_service_name(name), namespace
        )
    except ApiException as e:
        if e.status != 404:
            raise
