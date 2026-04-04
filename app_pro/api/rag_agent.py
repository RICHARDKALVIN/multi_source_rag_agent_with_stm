from fastapi import APIRouter

from app_pro.models.agent_state import state
from database_config.data_base_config import DB_CONFIGS
from app_pro.models.agent_state import SyncResult
from app_pro.helpers.helpers import _doc_id, _get_schema, _upsert_table
from app_pro.logger.logger import log
from fastapi import HTTPException
from pydantic import BaseModel
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

TOP_K_TABLES = int(os.getenv("TOP_K_TABLES", 5))


app = APIRouter(prefix="/rag", tags=["rag_agent"])


@app.post("/sync", response_model=SyncResult, summary="Embed / refresh schema metadata")
async def sync_schemas(databases: list[str] | None = None) -> SyncResult:
    """
    Syncs all (or selected) databases concurrently.
 
    Concurrency model:
      - All target DBs are introspected in parallel (asyncio.gather).
      - Within each DB, columns + comments for all tables are fetched in parallel.
      - Embedding + Chroma upsert per table run in the thread pool (asyncio.to_thread).
      - Tables with unchanged schema are skipped via MD5 hash check.
 
    Query params:
        ?databases=studentdb&databases=coursedb  → sync only those two
        (omit)                                   → sync all configured DBs
    """
    targets = databases if databases else list(DB_CONFIGS.keys())
    unknown = [d for d in targets if d not in DB_CONFIGS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown databases: {unknown}")
 
    upserted, skipped, errors = [], [], []
 
    async def _sync_one_db(db_name: str) -> None:
        log.info("Introspecting %s …", db_name)
        try:
            tables = await _get_schema(db_name)
        except Exception as exc:
            log.error("Failed to introspect %s: %s", db_name, exc)
            errors.append(f"{db_name}: {exc}")
            return
 
        # Upsert all tables in this DB concurrently
        results = await asyncio.gather(
            *[_upsert_table(t) for t in tables],
            return_exceptions=True,
        )
        for t, result in zip(tables, results):
            doc_id = _doc_id(db_name, t["table"])
            if isinstance(result, Exception):
                log.error("Error upserting %s: %s", doc_id, result)
                errors.append(f"{doc_id}: {result}")
            elif result is None:
                skipped.append(doc_id)
            else:
                upserted.append(result)
 
    # All DBs in parallel
    await asyncio.gather(*[_sync_one_db(db) for db in targets])
 
    return SyncResult(upserted=upserted, skipped=skipped, errors=errors)
 
 
# ---------------------------------------------------------------------------
# /retrieve
# ---------------------------------------------------------------------------
 
class RetrieveRequest(BaseModel):
    query:     str
    top_k:     int = TOP_K_TABLES
    db_filter: str | None = None   # e.g. "studentdb" to restrict search scope
 
 
class TableMatch(BaseModel):
    id:       str
    db:       str
    table:    str
    columns:  str
    distance: float
    document: str
 
 
class RetrieveResult(BaseModel):
    matches: list[TableMatch]
 
 
@app.post("/retrieve", response_model=RetrieveResult, summary="Find relevant tables for a query")
async def retrieve_tables(req: RetrieveRequest) -> RetrieveResult:
    """
    Embeds the user query and returns top-k matching tables from ChromaDB.
    Both the embed call and the Chroma query are offloaded to the thread pool.
    """
    # Embed query — blocking → thread pool
    vector = await asyncio.to_thread(state.embeddings.embed_query, req.query)
 
    where = {"db": req.db_filter} if req.db_filter else None
 
    # Chroma query — blocking → thread pool
    results = await asyncio.to_thread(
        state.collection.query,
        query_embeddings = [vector],
        n_results        = req.top_k,
        where            = where,
        include          = ["documents", "metadatas", "distances"],
    )
 
    matches = [
        TableMatch(
            id       = doc_id,
            db       = results["metadatas"][0][i]["db"],
            table    = results["metadatas"][0][i]["table"],
            columns  = results["metadatas"][0][i]["columns"],
            distance = round(results["distances"][0][i], 4),
            document = results["documents"][0][i],
        )
        for i, doc_id in enumerate(results["ids"][0])
    ]
 
    return RetrieveResult(matches=matches)
 
 
# ---------------------------------------------------------------------------
# /sync/status
# ---------------------------------------------------------------------------
 
@app.get("/sync/status", summary="Indexed table counts per database")
async def sync_status() -> dict:
    """Returns how many tables are indexed per database."""
 
    async def _count(db_name: str) -> tuple[str, int]:
        res = await asyncio.to_thread(
            state.collection.get, where={"db": db_name}, include=[]
        )
        return db_name, len(res["ids"])
 
    pairs = await asyncio.gather(*[_count(db) for db in DB_CONFIGS])
    counts = dict(pairs)
    counts["total"] = sum(counts.values())
    return counts
 