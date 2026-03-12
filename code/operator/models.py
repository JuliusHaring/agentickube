"""Pydantic models mirroring the Agent CRD spec (ai.juliusharing.com/v1)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


def _to_camel(name: str) -> str:
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


class _Base(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=_to_camel)


# ── Kubernetes core v1–compatible types (env/valueFrom) ─────────────────────


class SecretKeySelector(_Base):
    """Selects a key of a Secret in the pod's namespace (core.v1.SecretKeySelector)."""

    name: str
    key: str


class ConfigMapKeySelector(_Base):
    """Selects a key of a ConfigMap (core.v1.ConfigMapKeySelector)."""

    name: str
    key: str


class EnvVarSource(_Base):
    """Source for the value of an env var (core.v1.EnvVarSource)."""

    secret_key_ref: SecretKeySelector | None = None
    config_map_key_ref: ConfigMapKeySelector | None = None


# ── LLM ─────────────────────────────────────────────────────────────────────


class APIKeyConfig(_Base):
    """Secretable string: value (literal) or valueFrom (core.v1.EnvVarSource)."""

    value: str | None = None
    value_from: EnvVarSource | None = None


class LLMConfig(_Base):
    provider: str | None = None
    model_name: str | None = None
    base_url: str | None = None
    api_key: APIKeyConfig | None = None


# ── Prompts & Functions ──────────────────────────────────────────────────────


class PromptsConfig(_Base):
    system_prompt: str | None = None


class FunctionConfig(_Base):
    name: str


# ── Skills ───────────────────────────────────────────────────────────────────


class ConfigMapRef(_Base):
    name: str
    key: str = "SKILL.md"


class SkillItem(_Base):
    name: str
    content: str | None = None
    config_map_ref: ConfigMapRef | None = None


class BootstrapConfig(_Base):
    config_map_ref: ConfigMapRef | None = None


class SkillsConfig(_Base):
    """Skill configuration. builtin_skills: only these skills are kept in workspace/skills/ (allowlist)."""

    builtin_skills: list[str] | None = None
    items: list[SkillItem] | None = None
    bootstrap: BootstrapConfig | None = None


# ── MCP ──────────────────────────────────────────────────────────────────────


class MCPServerConfig(_Base):
    url: str
    type: str = "streamable_http"


# ── Workspace ────────────────────────────────────────────────────────────────


class PVCConfig(_Base):
    claim_name: str | None = None


class WorkspaceConfig(_Base):
    path: str = "/workspace"
    persistent_volume_claim: PVCConfig | None = None


# ── Conversation ─────────────────────────────────────────────────────────────


class ConversationConfig(_Base):
    enabled: bool = False
    max_history: int = 20


# ── Resources ────────────────────────────────────────────────────────────────


class ResourcesConfig(_Base):
    requests: dict[str, str] | None = None
    limits: dict[str, str] | None = None


# ── Security ─────────────────────────────────────────────────────────────────


class Capabilities(_Base):
    add: list[str] | None = None
    drop: list[str] | None = None


class ContainerSecurityContext(_Base):
    run_as_user: int | None = None
    run_as_group: int | None = None
    run_as_non_root: bool | None = None
    allow_privilege_escalation: bool | None = None
    read_only_root_filesystem: bool | None = None
    capabilities: Capabilities | None = None


class SeccompProfile(_Base):
    type: str | None = None
    localhost_profile: str | None = None


class PodSecurityContext(_Base):
    run_as_user: int | None = None
    run_as_group: int | None = None
    run_as_non_root: bool | None = None
    fs_group: int | None = None
    seccomp_profile: SeccompProfile | None = None


# ── Scheduling ───────────────────────────────────────────────────────────────


class Toleration(_Base):
    key: str | None = None
    operator: str | None = None
    value: str | None = None
    effect: str | None = None
    toleration_seconds: int | None = None


# ── Extra env / envFrom (core.v1.EnvVar, EnvFromSource) ──────────────────────


class EnvVar(_Base):
    """Environment variable (core.v1.EnvVar): name + value or valueFrom."""

    name: str
    value: str | None = None
    value_from: EnvVarSource | None = None


class LocalObjectReference(_Base):
    """Reference to a Secret or ConfigMap by name (core.v1.LocalObjectReference)."""

    name: str


class EnvFromSource(_Base):
    """Source for env vars from a whole Secret or ConfigMap (core.v1.EnvFromSource)."""

    secret_ref: LocalObjectReference | None = None
    config_map_ref: LocalObjectReference | None = None
    prefix: str | None = None
    optional: bool | None = None


# ── Auth (agent HTTP auth: basic, api_key, oauth2) ───────────────────────────


class AuthBasicConfig(_Base):
    """Credentials for AUTH_TYPE=basic. Use valueFrom.secretKeyRef in CR for secrets."""

    username: APIKeyConfig | None = None
    password: APIKeyConfig | None = None


class AuthApiKeyConfig(_Base):
    """API key for AUTH_TYPE=api_key."""

    api_key: APIKeyConfig | None = None


class AuthOAuth2Config(_Base):
    """OAuth2 Bearer token and optional IdP URLs. bearer_token required when type=oauth2. Use valueFrom for client_secret."""

    bearer_token: APIKeyConfig | None = None
    client_id: str | None = None
    client_secret: APIKeyConfig | None = None
    authorization_url: str | None = None
    token_url: str | None = None
    introspection_url: str | None = None
    issuer_url: str | None = None
    audience: str | None = None


class AuthConfig(_Base):
    """HTTP auth for the agent API (basic, api_key, oauth2). Injected as AUTH_* env vars."""

    type: str | None = None  # "basic" | "api_key" | "oauth2"
    basic: AuthBasicConfig | None = None
    api_key: AuthApiKeyConfig | None = None
    oauth2: AuthOAuth2Config | None = None


# ── OpenTelemetry ────────────────────────────────────────────────────────────


class OpenTelemetryConfig(_Base):
    enabled: bool = False
    endpoint: str | None = None
    service_name: str | None = None
    sampling_ratio: float | None = None


# ── Trigger ──────────────────────────────────────────────────────────────────


class TriggerConfig(_Base):
    type: str = "http"
    query: str | None = None
    schedule: str | None = None
    backoff_limit: int = 3
    ttl_seconds_after_finished: int | None = None


# ── Root ─────────────────────────────────────────────────────────────────────


class AgentSpec(_Base):
    image: str | None = None
    image_pull_policy: str | None = None
    description: str | None = None
    auth: AuthConfig | None = None
    llm: LLMConfig | None = None
    prompts: PromptsConfig | None = None
    functions: list[FunctionConfig] | None = None
    skills: SkillsConfig | None = None
    mcp_servers: list[MCPServerConfig] | None = None
    workspace: WorkspaceConfig | None = None
    conversation: ConversationConfig | None = None
    resources: ResourcesConfig | None = None
    security_context: ContainerSecurityContext | None = None
    pod_security_context: PodSecurityContext | None = None
    node_selector: dict[str, str] | None = None
    tolerations: list[Toleration] | None = None
    service_account_name: str | None = None
    env: list[EnvVar] | None = None
    env_from: list[EnvFromSource] | None = None
    open_telemetry: OpenTelemetryConfig | None = None
    trigger: TriggerConfig | None = None
