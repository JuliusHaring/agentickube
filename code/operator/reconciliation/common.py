"""
Shared helpers for reconciling Agent specs into
Kubernetes resources.  Imported by reconciliation.agent.
"""

from __future__ import annotations

from kubernetes import client

from models import (
    AgentSpec,
    APIKeyConfig,
    AuthConfig,
    EnvVar,
    LLMConfig,
    OpenTelemetryConfig,
)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_PULL_POLICY = "IfNotPresent"
CLI_COMMAND = ["python", "app/cli.py"]


# ── Shared environment variable builders ─────────────────────────────────────

_SpecType = AgentSpec


def _api_key_to_env(name: str, key: APIKeyConfig | None) -> list[client.V1EnvVar]:
    """One env var from APIKeyConfig (raw or secretKeyRef). Empty if key is None or empty."""
    if not key:
        return []
    if key.raw:
        return [client.V1EnvVar(name=name, value=key.raw)]
    if key.secret_name and key.secret_key:
        return [
            client.V1EnvVar(
                name=name,
                value_from=client.V1EnvVarSource(
                    secret_key_ref=client.V1SecretKeySelector(
                        name=key.secret_name, key=key.secret_key
                    )
                ),
            )
        ]
    return []


def auth_env(auth: AuthConfig | None) -> list[client.V1EnvVar]:
    """AUTH_* env vars for agent HTTP auth (basic, api_key, oauth2)."""
    if not auth or not auth.type:
        return []
    env: list[client.V1EnvVar] = [
        client.V1EnvVar(name="AUTH_TYPE", value=auth.type.strip().lower()),
    ]
    if auth.type == "basic" and auth.basic:
        env.extend(_api_key_to_env("AUTH_USERNAME", auth.basic.username))
        env.extend(_api_key_to_env("AUTH_PASSWORD", auth.basic.password))
    elif auth.type == "api_key" and auth.api_key:
        env.extend(_api_key_to_env("AUTH_API_KEY", auth.api_key.api_key))
    elif auth.type == "oauth2" and auth.oauth2:
        env.extend(
            _api_key_to_env("AUTH_OAUTH2_BEARER_TOKEN", auth.oauth2.bearer_token)
        )
        if auth.oauth2.client_id:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_CLIENT_ID", value=auth.oauth2.client_id
                )
            )
        if auth.oauth2.client_secret:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_CLIENT_SECRET", value=auth.oauth2.client_secret
                )
            )
        if auth.oauth2.authorization_url:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_AUTHORIZATION_URL",
                    value=auth.oauth2.authorization_url,
                )
            )
        if auth.oauth2.token_url:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_TOKEN_URL", value=auth.oauth2.token_url
                )
            )
        if auth.oauth2.introspection_url:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_INTROSPECTION_URL",
                    value=auth.oauth2.introspection_url,
                )
            )
        if auth.oauth2.issuer_url:
            env.append(
                client.V1EnvVar(
                    name="AUTH_OAUTH2_ISSUER_URL", value=auth.oauth2.issuer_url
                )
            )
        if auth.oauth2.audience:
            env.append(
                client.V1EnvVar(name="AUTH_OAUTH2_AUDIENCE", value=auth.oauth2.audience)
            )
    return env


def llm_env(llm: LLMConfig | None) -> list[client.V1EnvVar]:
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
        env.append(client.V1EnvVar(name="LLM_PROVIDER", value=llm.provider))
    return env


def otel_env(
    otel: OpenTelemetryConfig | None, resource_name: str
) -> list[client.V1EnvVar]:
    if not otel or not otel.enabled or not otel.endpoint:
        return []
    endpoint = otel.endpoint.strip().rstrip("/")
    svc = (otel.service_name or "").strip() or resource_name
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


def extra_env(env_vars: list[EnvVar]) -> list[client.V1EnvVar]:
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


def trigger_env(query: str | None) -> list[client.V1EnvVar]:
    if not query:
        return []
    return [client.V1EnvVar(name="AGENT_QUERY", value=query)]


# ── Shared K8s object converters ─────────────────────────────────────────────


def build_resources(spec: _SpecType) -> client.V1ResourceRequirements | None:
    r = spec.resources
    if not r or (not r.requests and not r.limits):
        return None
    return client.V1ResourceRequirements(
        requests=r.requests or None, limits=r.limits or None
    )


def build_container_sc(spec: _SpecType) -> client.V1SecurityContext | None:
    sc = spec.security_context
    if not sc:
        return None
    caps = None
    if sc.capabilities:
        caps = client.V1SecurityCapabilities(  # type: ignore[unresolved-attribute]
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


def build_pod_sc(spec: _SpecType) -> client.V1PodSecurityContext | None:
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


def build_tolerations(spec: _SpecType) -> list[client.V1Toleration] | None:
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
