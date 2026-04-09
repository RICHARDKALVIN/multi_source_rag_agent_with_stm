from app.core.redis import redis_client
import json
from app.llm.provider import llm
import asyncio
from langchain_core.output_parsers import StrOutputParser

class RedisSTM:

    def __init__(self, user_id):
        self.msg_key = f"stm:{user_id}:messages"
        self.summary_key = f"stm:{user_id}:summary"
       

    async def add_message(self, role, content):
        msg = json.dumps({"role": role, "content": content})

    
        await redis_client.rpush(self.msg_key, msg)

    
        await redis_client.ltrim(self.msg_key, -6, -1)




    async def get_messages(self):
        msgs =  await redis_client.lrange(self.msg_key, 0, -1)
        stm_messages_ =  [json.loads(m) for m in msgs] or []
        formatted_stm_messages = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in stm_messages_
        )
        stm_messages_re = [json.loads(m) for m in msgs][-4:] or []
        messages_re = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in stm_messages_re
        )

        return formatted_stm_messages,messages_re
    
    async def get_summary(self):
        return await redis_client.get(self.summary_key) or ""

    async def set_summary(self, summary):
        await redis_client.set(self.summary_key, summary)

    async def get_summary_from_messages(self, messages):
        parsed = [json.loads(m) for m in messages]

        formatted = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in parsed
        )

        prompt = f"""Summarize the conversation preserving:
                    - user preferences
                    - goals
                    - important facts
                    - constraints
                    Avoid generic text.
                    Conversation:
                    {formatted}
                    """
        
        chain = llm | StrOutputParser()
        response_text = await chain.ainvoke(prompt)
        
        return  response_text
    
    
    async def summarize_conversation(self):

        messages = await redis_client.lrange(self.msg_key, 0, -1)
         
        summary = await self.get_summary_from_messages(messages)

        await self.set_summary(summary)
    

