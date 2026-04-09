from app_pro.models.agent_state import state, SyncResult
import hashlib
import asyncio
import aiomysql
from typing import Any
from app_pro.logger.logger import log

async def _fetch_tables(db_name: str) -> list[str]:
    """Return all table names in the database."""
    async with state.pools[db_name].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SHOW TABLES")
            rows = await cur.fetchall()
    return [row[0] for row in rows]
 
 
async def _fetch_columns(db_name: str, table_name: str) -> list[str]:
    """Return column descriptors like 'col_name (TYPE)'."""
    async with state.pools[db_name].acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(f"DESCRIBE `{table_name}`")
            rows = await cur.fetchall()
    return [f"{r['Field']} ({r['Type']})" for r in rows]
 
 
async def _fetch_comment(db_name: str, table_name: str) -> str:
    """Fetch the table comment from information_schema (empty string if none)."""
    sql = (
        "SELECT TABLE_COMMENT FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s"
    )
    async with state.pools[db_name].acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(sql, (db_name, table_name))
            row = await cur.fetchone()
    return (row[0] or "") if row else ""
 
 
async def _get_schema(db_name: str) -> list[dict[str, Any]]:
    """
    Introspect one database fully concurrently:
      1. Fetch all table names.
      2. For each table, fetch columns + comment in parallel.
    """
    table_names = await _fetch_tables(db_name)
 
    async def _describe_table(table_name: str) -> dict:
        columns, comment = await asyncio.gather(
            _fetch_columns(db_name, table_name),
            _fetch_comment(db_name, table_name),
        )
        return {
            "db":      db_name,
            "table":   table_name,
            "columns": columns,
            "comment": comment,
        }
 
    return list(await asyncio.gather(*[_describe_table(t) for t in table_names]))
 
 
# ---------------------------------------------------------------------------
# Pure helpers (sync — no I/O)
# ---------------------------------------------------------------------------
 
def _build_document(t: dict) -> str:
    """
    Rich text fed to the embedding model.
    More context = better semantic retrieval accuracy.
    """
    col_str = ", ".join(t["columns"])
    comment = f" — {t['comment']}" if t["comment"] else ""
    return (
        f"Database: {t['db']}. "
        f"Table: {t['table']}{comment}. "
        f"Columns: {col_str}."
    )
 
def _doc_id(db: str, table: str) -> str:
    return f"{db}::{table}"
 
def _content_hash(doc_text: str) -> str:
    """MD5 fingerprint — skip re-embedding if schema hasn't changed."""
    return hashlib.md5(doc_text.encode()).hexdigest()
 
 
# ---------------------------------------------------------------------------
# Core upsert logic — one table, blocking calls offloaded to thread pool
# ---------------------------------------------------------------------------
 
async def _upsert_table(t: dict) -> str | None:
    """
    Returns the doc_id if upserted, None if skipped (schema unchanged).
 
    HuggingFace embed_query() and Chroma upsert/get are synchronous/blocking.
    asyncio.to_thread() runs them in a thread pool without stalling the event loop.
    """
    doc_id   = _doc_id(t["db"], t["table"])
    doc_text = _build_document(t)
    new_hash = _content_hash(doc_text)
 
    # Hash check — skip if nothing changed
    existing = await asyncio.to_thread(
        state.collection.get, ids=[doc_id], include=["metadatas"]
    )
    if existing["ids"] and existing["metadatas"][0].get("hash") == new_hash:
        log.debug("Skipped (unchanged): %s", doc_id)
        return None
 
    # Embed — blocking HuggingFace inference → thread pool
    vector = await asyncio.to_thread(state.embeddings.embed_query, doc_text)
 
    # Upsert into Chroma — blocking → thread pool
    await asyncio.to_thread(
        state.collection.upsert,
        ids        = [doc_id],
        embeddings = [vector],
        documents  = [doc_text],
        metadatas  = [{
            "db":      t["db"],
            "table":   t["table"],
            "columns": ", ".join(t["columns"]),
            "hash":    new_hash,
        }],
    )
    log.info("Upserted: %s", doc_id)
    return doc_id