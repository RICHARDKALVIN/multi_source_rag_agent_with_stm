from fastapi import APIRouter
from app.schemas.chat_schemas import ChatRequest, ChatResponse
from app.services import chat_service, data_loading_service

chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.post("/",response_model=ChatResponse)
async def chat(chat_request: ChatRequest):
    return await chat_service.chat(chat_request)


@chat_router.post("/rag")
async def chat_with_rag_agent(chat_request: ChatRequest):
    return await chat_service.chat_with_rag_agent(chat_request)

@chat_router.post("/load")
async def load_data():
    return await data_loading_service.load_data()