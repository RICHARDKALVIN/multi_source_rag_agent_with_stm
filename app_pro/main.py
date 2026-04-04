from fastapi import FastAPI
import asyncio
from fastapi.concurrency import asynccontextmanager
from langchain_community.embeddings import HuggingFaceEmbeddings
from app_pro.models.agent_state import state
from app_pro.logger.logger import log
import aiomysql
import chromadb
import os
from dotenv import load_dotenv
from chromadb.config import Settings
from database_config.data_base_config import DB_CONFIGS
load_dotenv()




CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
COLLECTION_NAME    = os.getenv("COLLECTION_NAME", "schema_metadata")
TOP_K_TABLES       = int(os.getenv("TOP_K_TABLES", 5))

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Loading embedding model …")
    # HuggingFace model load is blocking — offload to thread pool
    state.embeddings = await asyncio.to_thread(
        HuggingFaceEmbeddings,
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},        # switch to "cuda" if GPU available
        encode_kwargs={"normalize_embeddings": True},
    )
 
    log.info("Initialising ChromaDB …")
    chroma_client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR,
        settings=Settings(anonymized_telemetry=False),
    )
    state.collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
 
    log.info("Creating MySQL connection pools …")
    state.pools = {}
    for db_name, cfg in DB_CONFIGS.items():
        state.pools[db_name] = await aiomysql.create_pool(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            db=cfg["db"],
            minsize=1,
            maxsize=5,       # small pool — introspection only, not query traffic
            autocommit=True,
        )
        log.info("Pool ready: %s", db_name)
 
    yield  # app runs here
 
    # Shutdown — close all pools cleanly
    for db_name, pool in state.pools.items():
        pool.close()
        await pool.wait_closed()
        log.info("Pool closed: %s", db_name)
 
app = FastAPI(title="Schema Sync Service", lifespan=lifespan)

    
    