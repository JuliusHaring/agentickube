from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from logic.agent import agent_loop
from logic.sessions import get_session_id
from shared.logging import get_logger
from config import agent_config

logger = get_logger(__name__)

router = APIRouter(prefix="/query")


class BaseQueryRequest(BaseModel):
    query: str


class QueryRequestWithSessionId(BaseQueryRequest):
    session_id: Optional[str] = None
    """Only allowed when spec.conversation.enabled is true. Must be a valid UUID."""


class BaseQueryResponse(BaseModel):
    response: str


class QueryResponseWithSessionId(BaseQueryResponse):
    session_id: str


@router.post("")
def _query(
    request: QueryRequestWithSessionId
    if agent_config.conversation_memory_enabled
    else BaseQueryRequest,
) -> (
    QueryResponseWithSessionId
    if agent_config.conversation_memory_enabled
    else BaseQueryResponse
):
    if not agent_config.conversation_memory_enabled:
        logger.info("Query received: use_memory=False query=%s", request.query[:80])
        session_id = None
    else:
        session_id = get_session_id(request.session_id)
        logger.info(
            "Query received: use_memory=True session_id=%s query=%s",
            session_id,
            request.query[:80],
        )

    res = agent_loop(
        query=request.query,
        use_memory=agent_config.conversation_memory_enabled,
        session_id=session_id,
    )
    logger.info("Query response: %s", res[:80] if len(res) > 80 else res)
    return (
        QueryResponseWithSessionId(response=res, session_id=session_id)
        if agent_config.conversation_memory_enabled
        else BaseQueryResponse(response=res)
    )
