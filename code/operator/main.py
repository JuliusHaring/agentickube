"""
Kopf operator for Agent CRs (ai.juliusharing.com).
Reconciles Agent spec into a Deployment, Job, or CronJob
(+ optional skills ConfigMap) and tears them down on deletion.
"""

from __future__ import annotations

import copy
import logging.config

import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from shared.logging import LOGGING_CONFIG, get_logger

from models import AgentSpec, TriggerConfig
from reconcile import (
    CRD_GROUP,
    build_cronjob,
    build_deployment,
    build_job,
    cronjob_name,
    deployment_name,
    ensure_skills_cm,
    job_name,
)

# ── Logging ──────────────────────────────────────────────────────────────────

operator_logging = copy.deepcopy(LOGGING_CONFIG)
operator_logging.setdefault("loggers", {})["kopf"] = {
    "level": operator_logging["root"]["level"],
    "handlers": ["console"],
    "propagate": False,
}
logging.config.dictConfig(operator_logging)
logger = get_logger(__name__)

# ── Kubernetes client ────────────────────────────────────────────────────────

try:
    config.load_incluster_config()
except config.ConfigException:
    config.load_kube_config()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _trigger_type(agent: AgentSpec) -> str:
    return (agent.trigger or TriggerConfig()).type.strip().lower()


def _delete_resource(name: str, namespace: str, kind: str) -> None:
    """Delete a single resource by kind, ignoring 404."""
    try:
        if kind == "deployment":
            client.AppsV1Api().delete_namespaced_deployment(
                deployment_name(name), namespace
            )
        elif kind == "job":
            client.BatchV1Api().delete_namespaced_job(
                job_name(name), namespace, propagation_policy="Background"
            )
        elif kind == "cronjob":
            client.BatchV1Api().delete_namespaced_cron_job(
                cronjob_name(name), namespace
            )
    except ApiException as e:
        if e.status != 404:
            raise


def _cleanup_other_kinds(name: str, namespace: str, keep: str) -> None:
    """Remove resources from trigger types that are no longer active."""
    for kind in ("deployment", "job", "cronjob"):
        if kind != keep:
            _delete_resource(name, namespace, kind)


# ── Kopf handlers ────────────────────────────────────────────────────────────


@kopf.on.create(CRD_GROUP)
def create_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_skills_cm(name, namespace, agent, body)
    ttype = _trigger_type(agent)

    if ttype == "job":
        obj = build_job(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Job created: %s", obj.metadata.name)
    elif ttype == "cron":
        obj = build_cronjob(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_cron_job(namespace=namespace, body=obj)
        logger.info("CronJob created: %s", obj.metadata.name)
    else:
        obj = build_deployment(name, namespace, agent, body, has_inline_cm)
        client.AppsV1Api().create_namespaced_deployment(namespace=namespace, body=obj)
        logger.info("Deployment created: %s", obj.metadata.name)


@kopf.on.update(CRD_GROUP)
def update_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_skills_cm(name, namespace, agent, body)
    ttype = _trigger_type(agent)

    _cleanup_other_kinds(name, namespace, keep=ttype)

    if ttype == "job":
        _delete_resource(name, namespace, "job")
        obj = build_job(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Job recreated: %s", obj.metadata.name)
    elif ttype == "cron":
        obj = build_cronjob(name, namespace, agent, body, has_inline_cm)
        cj_name = cronjob_name(name)
        try:
            client.BatchV1Api().patch_namespaced_cron_job(cj_name, namespace, obj)
            logger.info("CronJob updated: %s", cj_name)
        except ApiException as e:
            if e.status == 404:
                client.BatchV1Api().create_namespaced_cron_job(
                    namespace=namespace, body=obj
                )
                logger.info("CronJob created: %s", cj_name)
            else:
                raise
    else:
        obj = build_deployment(name, namespace, agent, body, has_inline_cm)
        dep_name = deployment_name(name)
        client.AppsV1Api().patch_namespaced_deployment(dep_name, namespace, obj)
        logger.info("Deployment updated: %s", dep_name)


@kopf.on.delete(CRD_GROUP)
def delete_agent(name: str, namespace: str, **_) -> None:
    for kind in ("deployment", "job", "cronjob"):
        _delete_resource(name, namespace, kind)
    logger.info("Resources deleted for agent: %s", name)
