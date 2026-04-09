from app.graph.graph import app

async def get_weight_or_personality(state):
    ans = await app.ainvoke(state)
    return ans["answer"]