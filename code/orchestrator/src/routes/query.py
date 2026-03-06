from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from logic.orchestrator import orchestrate
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    """Optional. When provided, forwarded to agents for their conversation memory."""


class QueryResponse(BaseModel):
    response: str
    session_id: Optional[str] = None
    """Pass-through from request, or the one returned by an agent when it created a new session."""


@router.post("")
def _query(request: QueryRequest) -> QueryResponse:
    session_id = (request.session_id or "").strip() or None
    logger.info(
        "Query received: session_id=%s query=%s",
        session_id,
        request.query[:80],
    )
    result, effective_session_id = orchestrate(
        query=request.query,
        session_id=session_id,
    )
    logger.info("Query response: %s", result[:80] if len(result) > 80 else result)

    if effective_session_id and effective_session_id != session_id:
        logger.info("Received new session_id %s from agent", effective_session_id)
    return QueryResponse(
        response=result,
        session_id=effective_session_id or session_id,
    )
