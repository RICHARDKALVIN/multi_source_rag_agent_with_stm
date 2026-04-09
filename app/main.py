from fastapi import FastAPI
from app.api.chat import chat_router
from app.api.graph import graph_router
from loguru import logger
import sys

app = FastAPI()
logger.remove() 
logger.add("logs/app.log", rotation="500 MB", level="INFO")
logger.add(sys.stderr, level="DEBUG")

app.include_router(chat_router)
app.include_router(graph_router)
    
    