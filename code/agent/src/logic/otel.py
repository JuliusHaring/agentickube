import os
from typing import Optional

from fastapi import FastAPI
from pydantic_settings import BaseSettings
from shared.logging import get_logger

logger = get_logger(__name__)


class OtelConfig(BaseSettings):
    otel_exporter_otlp_endpoint: str = ""
    otel_service_name: str = "agent"


_otel_config: Optional[OtelConfig] = None


def _get_otel_config() -> OtelConfig:
    global _otel_config
    if _otel_config is None:
        _otel_config = OtelConfig()
    return _otel_config


def _configure_otlp_urls(base: str) -> None:
    """Derive full OTLP URLs from the base endpoint and propagate them via env vars
    for the OpenTelemetry SDK (standard OTEL convention, no Python API alternative)."""
    os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"{base}/v1/traces")
    os.environ.setdefault("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", f"{base}/v1/metrics")


def setup_fastapi_opentelemetry(app: FastAPI) -> None:
    """Configure OTLP tracing when OTEL_EXPORTER_OTLP_ENDPOINT is set (from CRD spec.openTelemetry).
    Uses Logfire SDK so both FastAPI and Pydantic AI use the same tracer and export to our collector.
    See: https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/
    """
    cfg = _get_otel_config()
    base = cfg.otel_exporter_otlp_endpoint.strip().rstrip("/")
    if not base:
        return
    try:
        import logfire

        _configure_otlp_urls(base)
        logfire.configure(
            service_name=cfg.otel_service_name,
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


def setup_cli_opentelemetry() -> None:
    """Lightweight OTel setup for CLI mode (no FastAPI instrumentation)."""
    cfg = _get_otel_config()
    base = cfg.otel_exporter_otlp_endpoint.strip().rstrip("/")
    if not base:
        return
    try:
        import logfire

        _configure_otlp_urls(base)
        logfire.configure(service_name=cfg.otel_service_name, send_to_logfire=False)
        logfire.instrument_pydantic_ai()
        logger.info("OpenTelemetry enabled (CLI mode -> %s)", base)
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT set but logfire not installed; tracing disabled"
        )
