from fastapi import APIRouter
from pydantic import BaseModel
from logic.agent import agent_loop
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    response: str


@router.post("")
def _query(request: QueryRequest) -> QueryResponse:
    logger.info(f"Query received: {request.query}")
    res = agent_loop(query=request.query)
    logger.info(f"Query response: {res}")
    return QueryResponse(response=res)
