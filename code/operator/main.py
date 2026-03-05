"""
Kopf operator for Agent CRs (ai.juliusharing.com).
Reconciles Agent spec into a Deployment (+ optional skills ConfigMap)
and tears them down on deletion.
"""

from __future__ import annotations

import copy
import logging.config

import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from shared.logging import LOGGING_CONFIG, get_logger

from models import AgentSpec
from reconcile import CRD_GROUP, build_deployment, deployment_name, ensure_skills_cm

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


# ── Kopf handlers ────────────────────────────────────────────────────────────


@kopf.on.create(CRD_GROUP)
def create_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_skills_cm(name, namespace, agent, body)
    deployment = build_deployment(name, namespace, agent, body, has_inline_cm)
    client.AppsV1Api().create_namespaced_deployment(
        namespace=namespace, body=deployment
    )
    logger.info("Deployment created: %s", deployment.metadata.name)


@kopf.on.update(CRD_GROUP)
def update_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_skills_cm(name, namespace, agent, body)
    deployment = build_deployment(name, namespace, agent, body, has_inline_cm)
    dep_name = deployment_name(name)
    client.AppsV1Api().patch_namespaced_deployment(dep_name, namespace, deployment)
    logger.info("Deployment updated: %s", dep_name)


@kopf.on.delete(CRD_GROUP)
def delete_agent(name: str, namespace: str, **_) -> None:
    dep_name = deployment_name(name)
    try:
        client.AppsV1Api().delete_namespaced_deployment(dep_name, namespace)
        logger.info("Deployment deleted: %s", dep_name)
    except ApiException as e:
        if e.status == 404:
            logger.debug("Deployment already gone: %s", dep_name)
        else:
            raise
