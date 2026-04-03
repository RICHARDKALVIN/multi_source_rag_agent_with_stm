from app.schemas.graph_state import AgentState
from langgraph.graph import END

def get_weight_or_personality(state : AgentState):
    if state["key_word"] == "record":
        return "record"
    elif state["key_word"] == "personality":
        return "personality"
    else:
        return  END