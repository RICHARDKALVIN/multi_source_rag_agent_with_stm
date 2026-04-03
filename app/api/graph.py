from fastapi import APIRouter
from app.schemas.graph_state import AgentState
from app.services.lang_graph_service import get_weight_or_personality

graph_router = APIRouter(prefix="/graph", tags=["graph"])


@graph_router.post("/get_weight_or_personality")
async def get_weight_or_personality_api(query: str , key_word: str):
    state = AgentState(query=query, key_word=key_word,answer="",tool_to_call="",chunks="")
    return await get_weight_or_personality(state)