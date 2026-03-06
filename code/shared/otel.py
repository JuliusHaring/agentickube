"""
Shared OpenTelemetry setup for agent and orchestrator.

When OTEL_EXPORTER_OTLP_ENDPOINT is set (e.g. by the operator from CRD spec.openTelemetry),
configures the Logfire SDK to export traces/metrics to that endpoint so FastAPI and
Pydantic AI use the same tracer.
"""

import os
from typing import Optional

from fastapi import FastAPI
from pydantic import Field
from pydantic_settings import BaseSettings

from shared.logging import get_logger

logger = get_logger(__name__)


class OtelConfig(BaseSettings):
    """OTEL settings from env (OTEL_EXPORTER_OTLP_ENDPOINT, OTEL_SERVICE_NAME)."""

    otel_exporter_otlp_endpoint: str = Field(
        default="",
        validation_alias="OTEL_EXPORTER_OTLP_ENDPOINT",
    )
    otel_service_name: str = Field(
        default="",
        validation_alias="OTEL_SERVICE_NAME",
    )


_config: Optional[OtelConfig] = None


def _get_config() -> OtelConfig:
    global _config
    if _config is None:
        _config = OtelConfig()
    return _config


def _configure_otlp_urls(base: str) -> None:
    """Set OTLP trace/metric endpoints in env for the OpenTelemetry SDK."""
    base = base.strip().rstrip("/")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"{base}/v1/traces")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", f"{base}/v1/metrics")


def setup_fastapi_opentelemetry(
    app: FastAPI,
    *,
    default_service_name: str = "agent",
) -> None:
    """Configure OTLP tracing when OTEL_EXPORTER_OTLP_ENDPOINT is set.

    Uses Logfire SDK; instruments FastAPI and Pydantic AI.
    default_service_name is used when OTEL_SERVICE_NAME is not set (e.g. local dev).
    """
    cfg = _get_config()
    base = (cfg.otel_exporter_otlp_endpoint or "").strip().rstrip("/")
    if not base:
        return
    service_name = (cfg.otel_service_name or "").strip() or default_service_name
    try:
        import logfire

        _configure_otlp_urls(base)
        logfire.configure(
            service_name=service_name,
            send_to_logfire=False,
        )
        logfire.instrument_fastapi(app)
        logfire.instrument_pydantic_ai()

        from opentelemetry import trace

        @app.middleware("http")
        async def _flush_otel_after_request(request, call_next):
            response = await call_next(request)
            try:
                provider = trace.get_tracer_provider()
                if hasattr(provider, "force_flush"):
                    provider.force_flush(timeout_millis=3000)
            except Exception:
                pass
            return response

        logger.info("OpenTelemetry enabled (Logfire SDK -> %s)", f"{base}/v1/traces")
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT set but logfire not installed; tracing disabled"
        )


def setup_cli_opentelemetry(
    *,
    default_service_name: str = "agent",
) -> None:
    """Lightweight OTEL setup for CLI/Job mode (no FastAPI instrumentation)."""
    cfg = _get_config()
    base = (cfg.otel_exporter_otlp_endpoint or "").strip().rstrip("/")
    if not base:
        return
    service_name = (cfg.otel_service_name or "").strip() or default_service_name
    try:
        import logfire

        _configure_otlp_urls(base)
        logfire.configure(service_name=service_name, send_to_logfire=False)
        logfire.instrument_pydantic_ai()
        logger.info("OpenTelemetry enabled (CLI mode -> %s)", base)
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT set but logfire not installed; tracing disabled"
        )
