"""
Kopf operator for Agent and Orchestrator CRs (ai.juliusharing.com).
Reconciles specs into Deployments, Jobs, or CronJobs
(+ optional skills ConfigMaps and Services) and tears them down on deletion.
"""

from __future__ import annotations

import copy
import logging.config

import kopf
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from shared.logging import LOGGING_CONFIG, get_logger

from models import AgentSpec, OrchestratorSpec, TriggerConfig
from reconciliation.agent import (
    AGENT_CRD_GROUP,
    agent_cronjob_name,
    agent_deployment_name,
    agent_job_name,
    build_agent_cronjob,
    build_agent_deployment,
    build_agent_job,
    delete_agent_service,
    ensure_agent_service,
    ensure_agent_skills_cm,
)
from reconciliation.orchestrator import (
    ORCHESTRATOR_CRD_GROUP,
    build_orchestrator_cronjob,
    build_orchestrator_deployment,
    build_orchestrator_job,
    delete_orchestrator_service,
    ensure_orchestrator_service,
    orchestrator_cronjob_name,
    orchestrator_deployment_name,
    orchestrator_job_name,
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


# ── Agent helpers ────────────────────────────────────────────────────────────


def _agent_trigger_type(spec: AgentSpec) -> str:
    return (spec.trigger or TriggerConfig()).type.strip().lower()


def _delete_agent_resource(name: str, namespace: str, kind: str) -> None:
    """Delete a single agent resource by kind, ignoring 404."""
    try:
        if kind == "deployment":
            client.AppsV1Api().delete_namespaced_deployment(
                agent_deployment_name(name), namespace
            )
        elif kind == "job":
            client.BatchV1Api().delete_namespaced_job(
                agent_job_name(name), namespace, propagation_policy="Background"
            )
        elif kind == "cronjob":
            client.BatchV1Api().delete_namespaced_cron_job(
                agent_cronjob_name(name), namespace
            )
    except ApiException as e:
        if e.status != 404:
            raise


def _cleanup_agent_other_kinds(name: str, namespace: str, keep: str) -> None:
    """Remove agent resources from trigger types that are no longer active."""
    for kind in ("deployment", "job", "cronjob"):
        if kind != keep:
            _delete_agent_resource(name, namespace, kind)


# ── Agent Kopf handlers ─────────────────────────────────────────────────────


@kopf.on.create(AGENT_CRD_GROUP)
def create_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_agent_skills_cm(name, namespace, agent, body)
    ttype = _agent_trigger_type(agent)

    if ttype == "job":
        obj = build_agent_job(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Job created: %s", obj.metadata.name)
    elif ttype == "cron":
        obj = build_agent_cronjob(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_cron_job(namespace=namespace, body=obj)
        logger.info("CronJob created: %s", obj.metadata.name)
    else:
        obj = build_agent_deployment(name, namespace, agent, body, has_inline_cm)
        client.AppsV1Api().create_namespaced_deployment(namespace=namespace, body=obj)
        ensure_agent_service(name, namespace, body)
        logger.info("Deployment + Service created: %s", obj.metadata.name)


@kopf.on.update(AGENT_CRD_GROUP)
def update_agent(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    agent = AgentSpec.model_validate(spec)
    has_inline_cm = ensure_agent_skills_cm(name, namespace, agent, body)
    ttype = _agent_trigger_type(agent)

    _cleanup_agent_other_kinds(name, namespace, keep=ttype)

    if ttype == "job":
        delete_agent_service(name, namespace)
        _delete_agent_resource(name, namespace, "job")
        obj = build_agent_job(name, namespace, agent, body, has_inline_cm)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Job recreated: %s", obj.metadata.name)
    elif ttype == "cron":
        delete_agent_service(name, namespace)
        obj = build_agent_cronjob(name, namespace, agent, body, has_inline_cm)
        cj_name = agent_cronjob_name(name)
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
        obj = build_agent_deployment(name, namespace, agent, body, has_inline_cm)
        dep_name = agent_deployment_name(name)
        try:
            client.AppsV1Api().patch_namespaced_deployment(dep_name, namespace, obj)
            logger.info("Deployment updated: %s", dep_name)
        except ApiException as e:
            if e.status == 404:
                client.AppsV1Api().create_namespaced_deployment(
                    namespace=namespace, body=obj
                )
                logger.info("Deployment created: %s", dep_name)
            else:
                raise
        ensure_agent_service(name, namespace, body)


@kopf.on.delete(AGENT_CRD_GROUP)
def delete_agent(name: str, namespace: str, **_) -> None:
    for kind in ("deployment", "job", "cronjob"):
        _delete_agent_resource(name, namespace, kind)
    delete_agent_service(name, namespace)
    logger.info("Resources deleted for agent: %s", name)


# ── Orchestrator helpers ─────────────────────────────────────────────────────


def _orch_trigger_type(spec: OrchestratorSpec) -> str:
    return (spec.trigger or TriggerConfig()).type.strip().lower()


def _delete_orch_resource(name: str, namespace: str, kind: str) -> None:
    try:
        if kind == "deployment":
            client.AppsV1Api().delete_namespaced_deployment(
                orchestrator_deployment_name(name), namespace
            )
        elif kind == "job":
            client.BatchV1Api().delete_namespaced_job(
                orchestrator_job_name(name), namespace, propagation_policy="Background"
            )
        elif kind == "cronjob":
            client.BatchV1Api().delete_namespaced_cron_job(
                orchestrator_cronjob_name(name), namespace
            )
    except ApiException as e:
        if e.status != 404:
            raise


def _cleanup_orch_other_kinds(name: str, namespace: str, keep: str) -> None:
    for kind in ("deployment", "job", "cronjob"):
        if kind != keep:
            _delete_orch_resource(name, namespace, kind)


# ── Orchestrator Kopf handlers ──────────────────────────────────────────────


@kopf.on.create(ORCHESTRATOR_CRD_GROUP)
def create_orchestrator(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    orch = OrchestratorSpec.model_validate(spec)
    ttype = _orch_trigger_type(orch)

    if ttype == "job":
        obj = build_orchestrator_job(name, namespace, orch, body)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Orchestrator Job created: %s", obj.metadata.name)
    elif ttype == "cron":
        obj = build_orchestrator_cronjob(name, namespace, orch, body)
        client.BatchV1Api().create_namespaced_cron_job(namespace=namespace, body=obj)
        logger.info("Orchestrator CronJob created: %s", obj.metadata.name)
    else:
        obj = build_orchestrator_deployment(name, namespace, orch, body)
        client.AppsV1Api().create_namespaced_deployment(namespace=namespace, body=obj)
        ensure_orchestrator_service(name, namespace, body)
        logger.info("Orchestrator Deployment + Service created: %s", obj.metadata.name)


@kopf.on.update(ORCHESTRATOR_CRD_GROUP)
def update_orchestrator(spec: dict, name: str, namespace: str, body: dict, **_) -> None:
    orch = OrchestratorSpec.model_validate(spec)
    ttype = _orch_trigger_type(orch)

    _cleanup_orch_other_kinds(name, namespace, keep=ttype)

    if ttype == "job":
        delete_orchestrator_service(name, namespace)
        _delete_orch_resource(name, namespace, "job")
        obj = build_orchestrator_job(name, namespace, orch, body)
        client.BatchV1Api().create_namespaced_job(namespace=namespace, body=obj)
        logger.info("Orchestrator Job recreated: %s", obj.metadata.name)
    elif ttype == "cron":
        delete_orchestrator_service(name, namespace)
        obj = build_orchestrator_cronjob(name, namespace, orch, body)
        cj = orchestrator_cronjob_name(name)
        try:
            client.BatchV1Api().patch_namespaced_cron_job(cj, namespace, obj)
            logger.info("Orchestrator CronJob updated: %s", cj)
        except ApiException as e:
            if e.status == 404:
                client.BatchV1Api().create_namespaced_cron_job(
                    namespace=namespace, body=obj
                )
                logger.info("Orchestrator CronJob created: %s", cj)
            else:
                raise
    else:
        obj = build_orchestrator_deployment(name, namespace, orch, body)
        dep = orchestrator_deployment_name(name)
        try:
            client.AppsV1Api().patch_namespaced_deployment(dep, namespace, obj)
            logger.info("Orchestrator Deployment updated: %s", dep)
        except ApiException as e:
            if e.status == 404:
                client.AppsV1Api().create_namespaced_deployment(
                    namespace=namespace, body=obj
                )
                logger.info("Orchestrator Deployment created: %s", dep)
            else:
                raise
        ensure_orchestrator_service(name, namespace, body)


@kopf.on.delete(ORCHESTRATOR_CRD_GROUP)
def delete_orchestrator(name: str, namespace: str, **_) -> None:
    for kind in ("deployment", "job", "cronjob"):
        _delete_orch_resource(name, namespace, kind)
    delete_orchestrator_service(name, namespace)
    logger.info("Resources deleted for orchestrator: %s", name)
