# Graph Router README

This document explains only the `graph_router` implementation and the LangGraph flow behind it.

## Router Overview

- API file: `app/api/graph.py`
- Router object: `graph_router = APIRouter(prefix="/graph", tags=["graph"])`
- Mounted in: `app/main.py`
- Service entrypoint: `app/services/lang_graph_service.py`
- Graph definition: `app/graph/graph.py`

The router exposes one endpoint that converts incoming query params to `AgentState`, then executes a compiled LangGraph and returns the final `answer`.

## Endpoint

### POST `/graph/get_weight_or_personality`

Handler:
- `get_weight_or_personality_api(query: str, key_word: str)`

Request format:
- Query params (not JSON body):
  - `query`: user question
  - `key_word`: route selector (`record` or `personality`)

Runtime chain:
1. Build `AgentState` in API layer.
2. Call `get_weight_or_personality(state)` service.
3. Service runs `await app.ainvoke(state)` on compiled graph.
4. Return `ans["answer"]` to client.

Response:
- Plain text string (final answer from graph state).

## AgentState Contract

Defined in `app/schemas/graph_state.py`:
- `query: str`
- `key_word: str`
- `tool_to_call: str`
- `chunks: str`
- `answer: str`

Initial state created by API:
- `query=<request query>`
- `key_word=<request key_word>`
- `tool_to_call=""`
- `chunks=""`
- `answer=""`

## LangGraph Nodes (What Each Node Does)

All nodes are implemented in `app/graph/nodes/graph_nodes.py`.

### 1) `router_node(state)`
- Purpose: lightweight intent router based on `state["key_word"]`.
- Logic:
  - `record` -> sets `tool_to_call="record"`
  - `personality` -> sets `tool_to_call="personality"`
  - otherwise -> sets `tool_to_call="none"`
- Output state update: `{"tool_to_call": ...}`

### 2) `record_node(state)`
- Purpose: retrieve record-related chunks from vector store.
- Calls: `search_student_records(state["query"])` from `app/tools/search_functions.py`
- Retrieval source: `csv_store` (Chroma collection for CSV data).
- Output state update: `{"chunks": "<retrieved text>"}`.

### 3) `personality_node(state)`
- Purpose: retrieve personality-related chunks from vector store.
- Calls: `search_student_personality(state["query"])` from `app/tools/search_functions.py`
- Retrieval source: `pdf_store` (Chroma collection for PDF data).
- Output state update: `{"chunks": "<retrieved text>"}`.

### 4) `llm_node(state)`
- Purpose: generate final answer using retrieved context.
- Prompt pattern:
  - query + `state["chunks"]` in a simple instruction template.
- Model path:
  - `llm_agent` from `app/llm/provider.py`
  - output parsed using `StrOutputParser()`
- Output state update: `{"answer": "<final model answer>"}`.

## Graph Wiring and Flow

Graph is assembled in `app/graph/graph.py` using `StateGraph(AgentState)` with:
- Nodes: `router`, `record`, `personality`, `llm`
- Entry point: `router`
- Conditional edge from `router` decided by `get_weight_or_personality(...)` in `app/graph/nodes/graph_helper_functions.py`
- Static edges:
  - `record -> llm`
  - `personality -> llm`

### Decision Function

`get_weight_or_personality(state)` returns:
- `"record"` when `key_word == "record"`
- `"personality"` when `key_word == "personality"`
- `END` otherwise

### End-to-End Flow Diagram

```text
POST /graph/get_weight_or_personality
        |
        v
build AgentState in API
        |
        v
service -> graph app.ainvoke(state)
        |
        v
      router
   /     |      \
record personality END
  |         |
  v         v
  llm <-----+
   |
   v
return state["answer"]
```

## Data and Tool Dependencies Used by Nodes

- `record_node` and `personality_node` use `app/tools/search_functions.py`.
- Search functions query Chroma stores from `app/db/chroma_db.py`:
  - `csv_store` (`collection_name="csv_data"`)
  - `pdf_store` (`collection_name="pdf_documents"`)
- Both return a joined text block; fallback: `"No matching student records found."`

## Example Calls

### Record path

```bash
curl -X POST "http://127.0.0.1:8000/graph/get_weight_or_personality?query=What%20is%20John%27s%20maths%20score%3F&key_word=record"
```

### Personality path

```bash
curl -X POST "http://127.0.0.1:8000/graph/get_weight_or_personality?query=What%20are%20the%20student%27s%20goals%3F&key_word=personality"
```

## Important Notes

- This endpoint currently accepts only query parameters.
- Only `record` and `personality` trigger retrieval + LLM execution.
- Any other `key_word` routes to `END`; in that case, `answer` may be empty and the API can return a blank result.
