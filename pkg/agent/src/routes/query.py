from fastapi import APIRouter, Body
from logic.agent import agent_loop

router = APIRouter(prefix="/query")


@router.post("")
def _query(query: str = Body()):
    res = agent_loop(query=query)
    return res
