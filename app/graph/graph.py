from langgraph.graph import END, StateGraph
from app.schemas.graph_state import AgentState
from app.graph.nodes.graph_nodes import router_node, record_node, personality_node, llm_node
from app.graph.nodes.graph_helper_functions import get_weight_or_personality

builder = StateGraph(AgentState)

builder.add_node("router",router_node)
builder.add_node("record",record_node)
builder.add_node("personality",personality_node)
builder.add_node("llm",llm_node)

builder.add_conditional_edges("router", get_weight_or_personality,["record", "personality",END])
builder.add_edge("record","llm")
builder.add_edge("personality","llm")

builder.set_entry_point("router")

app = builder.compile()