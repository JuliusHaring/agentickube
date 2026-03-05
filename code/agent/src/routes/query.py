from fastapi import APIRouter, Body
from logic.agent import agent_loop
from shared.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/query")


@router.post("")
def _query(query: str = Body()):
    logger.info(f"Query received: {query}")
    res = agent_loop(query=query)
    logger.info(f"Query response: {res}")
    return res
