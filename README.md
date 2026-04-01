
CHAT BOT USING LANGCHAIN — PROJECT DETAILS FOR GITHUB README


--------------------------------------------------------------------------------
1. HIGH-LEVEL SUMMARY
--------------------------------------------------------------------------------
- Purpose: FastAPI backend that exposes chat endpoints powered by Google Gemini
  (LangChain), with optional Redis-backed short-term memory + rolling summaries,
  Chroma vector stores for RAG-style document search, and a LangChain SQL agent
  over a PostgreSQL database.
- Name (folder): Chat_Bot_Using_Langchain
- Entry app: FastAPI in app/main.py, router prefix /chat from app/api/chat.py

--------------------------------------------------------------------------------
2. REPOSITORY LAYOUT (FOLDERS & FILES)
--------------------------------------------------------------------------------
```text
Project root
├── docker-compose.yml          # Redis + ChromaDB server containers (see note)
├── .env                        # Local secrets (untracked in git — do not commit)
├── chroma_db_data/             # Local persisted Chroma data (SQLite + indices)
│                               # Created at runtime by langchain-chroma
└── app/
    ├── main.py                 # FastAPI app, includes chat_router
    ├── api/
    │   └── chat.py             # HTTP routes under /chat
    ├── core/
    │   └── redis.py            # Async Redis client (decode_responses=True)
    ├── memory/
    │   └── RedisSTM.py         # Redis list STM, summary string, summarization
    ├── llm/
    │   └── provider.py         # Gemini LLMs, SQL toolkit, combined agent + tools
    ├── services/
    │   ├── chat_service.py     # chat() and chat_with_rag_agent()
    │   └── data_loading_service.py  # Load CSV + PDF into Chroma
    ├── db/
    │   ├── chroma_db.py        # Chroma collections: csv_data, pdf_documents
    │   └── db_engine.py        # SQLAlchemy engine + LangChain SQLDatabase
    ├── tools/
    │   └── multi_source_tool.py # LangChain @tool wrappers for Chroma search
    ├── utils/
    │   └── prompts.py          # build_prompt() for memory-augmented chat
    ├── schemas/
    │   └── chat_schemas.py     # Pydantic ChatRequest / ChatResponse
    └── data/
        ├── my_file.csv         # Sample student marks (used by data loader)
        └── my_pdf.pdf          # PDF for personality-style RAG (path expected)
```



--------------------------------------------------------------------------------
3. TECHNOLOGY STACK (FROM SOURCE)
--------------------------------------------------------------------------------
- Web: FastAPI, Pydantic
- LLM: LangChain + langchain-google-genai (ChatGoogleGenerativeAI)
- Memory: Redis (async client), JSON messages in Redis lists
- Vector DB: LangChain Chroma + HuggingFace embeddings (all-MiniLM-L6-v2)
- SQL: LangChain SQLDatabase + SQLDatabaseToolkit (PostgreSQL via SQLAlchemy)
- Data loading: CSVLoader, PyPDFLoader, RecursiveCharacterTextSplitter

There is no requirements.txt in the repo root at documentation time; derive a
full list with `pip freeze` from your environment or `pip install` the packages
above when writing README setup steps.

--------------------------------------------------------------------------------
4. ENVIRONMENT VARIABLES
--------------------------------------------------------------------------------
Required / used in code:
- GEMINI_API_KEY       — Google AI API key for Gemini (app/llm/provider.py)
- DATABASE_URL         — PostgreSQL URL; code replaces asyncpg with psycopg2 for
                         SQLAlchemy (app/db/db_engine.py)
- REDIS_HOST           — Redis hostname (app/core/redis.py)
- REDIS_PORT           — Redis port, int (app/core/redis.py)

README should show a .env.example with placeholder values only.

--------------------------------------------------------------------------------
5. DOCKER COMPOSE (docker-compose.yml)
--------------------------------------------------------------------------------
Services:
- redis: image redis:7, port 6379, AOF persistence, volume redis_data
- chromadb: image chromadb/chroma, host port 8001 -> container 8000, persistent
  volume chroma_data

Important implementation note for README:
- app/db/chroma_db.py uses Chroma with persist_directory="./chroma_db_data"
  (embedded/local persistence), not the chromadb Docker service HTTP client.
  The compose chromadb service is optional unless you later wire the app to it.

--------------------------------------------------------------------------------
6. API ENDPOINTS (app/api/chat.py)
--------------------------------------------------------------------------------
Base path: /chat (tag: chat)

POST /chat/
  - Body: ChatRequest { user_id: str, message: str }
  - Response: ChatResponse { response: str }
  - Behavior (app/services/chat_service.py::chat):
    * Loads STM messages + summary from Redis for user_id
    * Builds prompt via app/utils/prompts.build_prompt (LTM slot currently "none")
    * Invokes Gemini via llm | StrOutputParser
    * Appends user + assistant turns to Redis list (trimmed to last 6 items)
    * INCR count:messages:{user_id}; every 3rd increment triggers summarize_conversation()
    * Summary stored at Redis key stm:{user_id}:summary (string SET)

POST /chat/rag
  - Body: ChatRequest
  - Response: plain text string (not wrapped in ChatResponse in code)
  - Behavior: Invokes LangChain agent (app/llm/provider.py) with tools:
    search_student_personality, search_student_records, plus SQL tools from
    SQLDatabaseToolkit. Extracts final assistant text from agent result messages.

POST /chat/load
  - Body: none
  - Response: JSON from data_loading_service.load_data()
  - Behavior: Loads app/data/my_file.csv and app/data/my_pdf.pdf, splits text,
    adds chunks to Chroma collections csv_data and pdf_documents.

--------------------------------------------------------------------------------
7. REDIS DATA MODEL (SHORT-TERM MEMORY)
--------------------------------------------------------------------------------
Per user_id (RedisSTM in app/memory/RedisSTM.py):
- stm:{user_id}:messages  — Redis LIST of JSON strings
  { "role": "user"|"assistant", "content": "..." }
  After each add_message, LTRIM keeps indices -6..-1 (last 6 items).
- stm:{user_id}:summary   — Redis STRING, rolling conversation summary text
- count:messages:{user_id} — Redis STRING counter (INCR per /chat/ request);
  when value % 3 == 0, summarize_conversation() runs

--------------------------------------------------------------------------------
8. CHROMA / RAG TOOLS
--------------------------------------------------------------------------------
- csv_store: collection "csv_data", persist ./chroma_db_data
- pdf_store: collection "pdf_documents", same persist directory
- search_student_records: similarity search on csv_store (k=5)
- search_student_personality: similarity search on pdf_store (k=5)

Sample CSV (app/data/my_file.csv): student-like rows with Gender, DOB, subject
marks (Maths, Physics, etc.). First column appears to be name (header row may
need alignment for CSVLoader — verify if loader warnings occur).

--------------------------------------------------------------------------------
9. LLM CONFIGURATION (app/llm/provider.py)
--------------------------------------------------------------------------------
- llm: gemini-2.5-flash-lite, temperature 0, max_output_tokens 2000
- llm_agent: gemini-flash-latest, temperature 0 (used for agent + SQL toolkit)
- Agent: create_agent with combined_tools = personality + records tools +
  sql_tools; system prompt describes helpful assistant with student DB access

--------------------------------------------------------------------------------
10. HOW TO RUN (SUGGESTED README SECTIONS)
--------------------------------------------------------------------------------
Prerequisites:
- Python 3.x, virtual environment
- Redis running (local or Docker compose redis service)
- PostgreSQL reachable with DATABASE_URL compatible with SQLAlchemy + psycopg2
- GEMINI_API_KEY set

Suggested commands (adapt to your tooling):
  pip install -r requirements.txt   # after you generate requirements.txt
  docker compose up -d redis      # optional chromadb service
  uvicorn app.main:app --reload

Before using /chat/rag, run POST /chat/load once (or whenever data changes) so
Chroma has documents; ensure app/data/my_pdf.pdf exists.

Interactive docs: FastAPI automatic OpenAPI at /docs when server is running.

--------------------------------------------------------------------------------

================================================================================
END OF PROJECT DETAILS
================================================================================
