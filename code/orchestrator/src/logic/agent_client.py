"""HTTP client for calling agent /query endpoints."""

import httpx
from opentelemetry import trace
from opentelemetry.propagate import inject

from shared.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 300.0
SESSION_HEADER = "X-Session-Id"

_tracer = trace.get_tracer(__name__)


async def query_agent(
    url: str,
    query: str,
    session_id: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    agent_name: str | None = None,
) -> tuple[str, str | None]:
    """Call agent /query. Returns (response_text, session_id_from_agent or None).

    Sends and receives session ID via the X-Session-Id header, same as the agent API.
    When OTEL is configured, creates a span for the call and propagates
    W3C trace context (traceparent) so the agent's spans become children.
    """
    span_name = f"call_agent {agent_name}" if agent_name else "call_agent"
    attrs: dict[str, str | int] = {
        "agent.name": agent_name or "",
        "agent.url": url,
    }
    if session_id:
        attrs["session.id"] = session_id
    with _tracer.start_as_current_span(span_name, attributes=attrs) as span:
        body: dict = {"query": query}
        headers: dict[str, str] = {}
        inject(headers)
        if session_id:
            headers[SESSION_HEADER] = session_id

        async with httpx.AsyncClient(timeout=timeout) as client:
            logger.info("Calling agent at %s", url)
            resp = await client.post(url, json=body, headers=headers)
            span.set_attribute("http.status_code", resp.status_code)
            if not resp.is_success:
                body_preview = (resp.text or "")[:2000]
                logger.error(
                    "Agent %s returned %s: %s",
                    agent_name or url,
                    resp.status_code,
                    body_preview,
                )
                resp.raise_for_status()
            data = resp.json()

        session_from_agent = resp.headers.get(SESSION_HEADER)
        return (data["response"], session_from_agent)
