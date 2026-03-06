"""HTTP client for calling agent /query endpoints."""

import httpx

from shared.logging import get_logger

logger = get_logger(__name__)

DEFAULT_TIMEOUT = 300.0


async def query_agent(
    url: str,
    query: str,
    session_id: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[str, str | None]:
    """Call agent /query. Returns (response_text, session_id_from_agent or None)."""
    body: dict = {"query": query}
    if session_id:
        body["session_id"] = session_id
    async with httpx.AsyncClient(timeout=timeout) as client:
        logger.info("Calling agent at %s", url)
        resp = await client.post(url, json=body)
        resp.raise_for_status()
        data = resp.json()
        return (data["response"], data.get("session_id"))
