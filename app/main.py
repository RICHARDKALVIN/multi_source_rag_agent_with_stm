from fastapi import FastAPI
from app.api.chat import chat_router
from app.api.graph import graph_router



app = FastAPI()

app.include_router(chat_router)
app.include_router(graph_router)
    
    