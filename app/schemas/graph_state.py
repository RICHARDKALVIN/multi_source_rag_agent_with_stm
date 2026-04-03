from typing import TypedDict


class AgentState(TypedDict):
    query : str
    key_word : str
    tool_to_call : str
    chunks : str
    answer : str
