from typing import TypedDict
from pydantic import BaseModel
from langchain_community.embeddings import HuggingFaceEmbeddings
import chromadb
import aiomysql

class SyncResult(BaseModel):
    upserted: list[str]
    skipped:  list[str]
    errors:   list[str]
 
class AppState:
    embeddings: HuggingFaceEmbeddings
    collection: chromadb.Collection
    pools: dict[str, aiomysql.Pool]   # one connection pool per database
 
state = AppState()