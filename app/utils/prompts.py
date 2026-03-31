
def build_prompt(summary, stm_messages, ltm_memories, user_query):

    formatted_stm_messages = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in stm_messages
        )
    
    prompt = f"""
    You are a helpful assistant.
    Use the provided context to answer the user's question.

    IMPORTANT:
    - Do NOT repeat the summary
    - Do NOT restate the conversation
    - Do NOT output sections like "Summary", "Memory", etc.
    - ONLY answer the user's question directly

    Context:

    Previous conversation summary:
    {summary}

    Long-term memory:
    {ltm_memories}

    Recent conversation:
    {formatted_stm_messages}

    User question:
    {user_query}

    Answer:
    """

    return prompt