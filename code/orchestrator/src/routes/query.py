from typing import Optional

from fastapi import APIRouter
from fastapi.params import Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from logic.orchestrator import orchestrate
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")

SESSION_HEADER = "X-Session-Id"


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


@router.post("")
def _query(
    request: QueryRequest,
    session_id: Optional[str] = Header(
        default=None,
        alias=SESSION_HEADER,
        description="Session ID. Optional. Forwarded to agents for conversation memory.",
    ),
) -> JSONResponse:
    session_id = (session_id or "").strip() or None
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

    body = QueryResponse(response=result).model_dump()
    headers = {}
    sid = effective_session_id or session_id
    if sid:
        headers[SESSION_HEADER] = sid
    return JSONResponse(content=body, headers=headers)
