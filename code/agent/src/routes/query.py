from typing import Optional
import uuid
from fastapi import APIRouter
from fastapi.params import Header
from pydantic import BaseModel

from config import agent_config
from logic.agent import agent_loop
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


@router.post("")
def _query(
    request: QueryRequest,
    session_id: Optional[str] = Header(
        default_factory=lambda: (
            uuid.uuid4().hex if agent_config.conversation_memory_enabled else None
        ),
        alias="X-Session-Id",
        description="Session ID. Optional. Only used when conversation_memory is enabled.",
    ),
) -> QueryResponse:
    logger.info(
        "Query received: query=%s and session_id=%s", request.query[:80], session_id
    )
    result = agent_loop(query=request.query, session_id=session_id)
    return QueryResponse(response=result)
