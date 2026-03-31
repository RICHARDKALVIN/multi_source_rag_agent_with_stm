from langchain.tools import tool
from app.db.chroma_db import csv_store, pdf_store

@tool
async def search_student_records(query : str) :
    """
    Search the student database for records related to the query.
    Use this to find specific students or marks mentioned in the data.
    """
    docs = await csv_store.asimilarity_search(query, k=5)

    results = "\n\n".join([doc.page_content for doc in docs])

    return results if results else "No matching student records found."

@tool
async def search_student_personality(query : str) :
    """
    Look up this tool for information about a student's personality traits, preferences, or goals.
    """
    docs = await pdf_store.asimilarity_search(query, k=5)

    results = "\n\n".join([doc.page_content for doc in docs])

    return results if results else "No matching student records found."

