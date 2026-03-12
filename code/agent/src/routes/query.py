import uuid
from opentelemetry import trace
from fastapi import APIRouter
from fastapi.params import Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import agent_config
from logic.agent import agent_loop
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")

SESSION_HEADER = "X-Session-Id"
MAX_RESPONSE_LOG_CHARS = 200


def _log_response(result: str) -> None:
    """Log response length and a short prefix to avoid leaking full content."""
    if len(result) <= MAX_RESPONSE_LOG_CHARS:
        logger.info("Query response length=%d: %s", len(result), result)
    else:
        logger.info(
            "Query response length=%d: %s... [truncated]",
            len(result),
            result[:MAX_RESPONSE_LOG_CHARS],
        )


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


@router.post("")
def _query(
    request: QueryRequest,
    session_id: str | None = Header(  # type:ignore[invalid-parameter-default]
        default_factory=lambda: (
            uuid.uuid4().hex if agent_config.conversation_memory_enabled else None
        ),
        alias=SESSION_HEADER,
        description="Session ID. Optional. Only used when conversation_memory is enabled.",
    ),
) -> JSONResponse:
    logger.info(
        "Query received: query=%s and session_id=%s", request.query[:80], session_id
    )
    span = trace.get_current_span()
    if span.is_recording() and session_id:
        span.set_attribute("session.id", session_id)
    result = agent_loop(query=request.query, session_id=session_id)
    _log_response(result)
    body = QueryResponse(response=result).model_dump()
    headers = {SESSION_HEADER: session_id} if session_id else {}
    return JSONResponse(content=body, headers=headers)
