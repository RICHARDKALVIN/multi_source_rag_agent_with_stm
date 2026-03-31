from app.schemas.chat_schemas import  ChatRequest, ChatResponse  
from app.llm.provider import llm ,llm_agent
from app.memory.RedisSTM import RedisSTM
from app.utils.prompts import build_prompt
from app.core.redis import redis_client
from langchain_core.output_parsers import StrOutputParser
from app.llm.provider import agent

async def chat(chat_request : ChatRequest):

    redisSTM = RedisSTM(user_id=chat_request.user_id)

    count_key = f"count:messages:{chat_request.user_id}"
    

    stm = await redisSTM.get_messages()

    summary = await redisSTM.get_summary()

    prompt = build_prompt(summary, stm, "none", chat_request.message)

    response_text = await (llm | StrOutputParser()).ainvoke(prompt)
    await redisSTM.add_message("user", chat_request.message)
    await redisSTM.add_message("assistant", response_text)

    new_count = await redis_client.incr(count_key)
    
    if new_count % 3 == 0:
        await redisSTM.summarize_conversation()

    return ChatResponse(response=response_text)



async def chat_with_rag_agent(chat_request : ChatRequest):

    
    input_state = {"messages": [("user", chat_request.message)]}

    result = await agent.ainvoke(input_state)

    final_answer = result["messages"][-1].content

    return final_answer
    


