from app.schemas.graph_state import AgentState
from app.tools.search_functions import search_student_records, search_student_personality
from app.llm.provider import llm_agent
from langchain_core.output_parsers import StrOutputParser


def router_node(state: AgentState):
    if state["key_word"] == "record":
        return {"tool_to_call" : "record"}
    elif state["key_word"] == "personality":
        return {"tool_to_call" : "personality"}
    else:
        return {"tool_to_call" : "none"}
    
async def record_node(state: AgentState):

    record_chunks = await search_student_records(state["query"])

    return {"chunks" : record_chunks}

async def personality_node(state: AgentState):

    personality_chunks = await search_student_personality(state["query"])

    return {"chunks" : personality_chunks}

async def llm_node(state: AgentState):

    prompt = f"Based on the following information, answer the query: {state['query']}\n\nInformation:\n{state['chunks']}"

    response_text = await (llm_agent | StrOutputParser()).ainvoke(prompt)

    return {"answer" : response_text}