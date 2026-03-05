import os
from fastapi import FastAPI
from shared.logging import get_logger

logger = get_logger(__name__)


def setup_opentelemetry(app: FastAPI) -> None:
    """Configure OTLP tracing when OTEL_EXPORTER_OTLP_ENDPOINT is set (from CRD spec.openTelemetry).
    Uses Logfire SDK so both FastAPI and Pydantic AI use the same tracer and export to our collector.
    See: https://logfire.pydantic.dev/docs/how-to-guides/alternative-backends/
    """
    base = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip().rstrip("/")
    if not base:
        return
    try:
        import logfire

        # Single place for OTLP path convention: derive full URLs from base (operator or env only sets base).
        # Logfire uses HTTP + Protobuf; collector expects /v1/traces and /v1/metrics.
        os.environ.setdefault("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", f"{base}/v1/traces")
        os.environ.setdefault(
            "OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", f"{base}/v1/metrics"
        )
        service_name = os.environ.get("OTEL_SERVICE_NAME", "agent")
        logfire.configure(
            service_name=service_name,
            send_to_logfire=False,
        )
        logfire.instrument_fastapi(app)
        logfire.instrument_pydantic_ai()

        # Flush spans after each request so they reach Jaeger quickly (default batch is ~5s)
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

        logger.info(
            "OpenTelemetry enabled (Logfire SDK -> %s)",
            os.environ.get("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", base),
        )
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT set but logfire not installed; tracing disabled"
        )
