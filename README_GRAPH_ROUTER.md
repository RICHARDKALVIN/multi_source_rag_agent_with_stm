# Graph Router README

This document covers only the `graph_router` implementation in this project.

## Router Overview

- File: `app/api/graph.py`
- Prefix: `/graph`
- Tag: `graph`
- Mounted in app: `app/main.py`

`graph_router` exposes one endpoint that builds an `AgentState` and sends it to the LangGraph service.

## Endpoint

### POST `/graph/get_weight_or_personality`

Calls:
- `app.api.graph.get_weight_or_personality_api()`
- which builds `AgentState`
- then calls `app.services.lang_graph_service.get_weight_or_personality(state)`

Request parameters (query params):
- `query` (string): user question
- `key_word` (string): routing selector, expected values:
  - `record`
  - `personality`

Response:
- Returns a plain string answer (`ans["answer"]`) from the LangGraph execution.

## State Shape

`AgentState` is defined in `app/schemas/graph_state.py` as:
- `query: str`
- `key_word: str`
- `tool_to_call: str`
- `chunks: str`
- `answer: str`

The API initializes it as:
- `query=<incoming query>`
- `key_word=<incoming key_word>`
- `answer=""`
- `tool_to_call=""`
- `chunks=""`

## Internal Graph Flow (used by this router)

The router triggers `app.services.lang_graph_service`, which invokes the compiled graph in `app/graph/graph.py`.

Graph nodes:
- `router` -> decides branch from `key_word`
- `record` -> fetches student record chunks
- `personality` -> fetches personality chunks
- `llm` -> creates final answer from chunks

Routing behavior:
- `key_word == "record"` -> `record -> llm`
- `key_word == "personality"` -> `personality -> llm`
- anything else -> `END` (no LLM answer generation path)

## Example Calls

### Record branch

```bash
curl -X POST "http://127.0.0.1:8000/graph/get_weight_or_personality?query=What%20is%20John%27s%20maths%20score%3F&key_word=record"
```

### Personality branch

```bash
curl -X POST "http://127.0.0.1:8000/graph/get_weight_or_personality?query=What%20are%20the%20student%27s%20goals%3F&key_word=personality"
```

## Notes and Constraints

- `query` and `key_word` are query parameters, not JSON body fields.
- `key_word` must be exactly `record` or `personality` to traverse tool + LLM nodes.
- If `key_word` is any other value, the graph ends early and may not return a meaningful answer.
