
from langchain_core.output_parsers import StrOutputParser
from app.llm.provider import rewiter_llm
from loguru import logger

async def get_re_written_query(query : str, history : str):

   
    prompt = f"""
    Rewrite the user query into a standalone query.

    Chat History:
    {history}

    User Query:
    {query}

    Rewritten Query:
    """
    response_text = await (rewiter_llm | StrOutputParser()).ainvoke(prompt)

    logger.info(f"user query: {query} rewritten query: {response_text}")

    return response_text


