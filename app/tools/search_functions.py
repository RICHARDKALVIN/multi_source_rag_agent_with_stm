
from app.db.chroma_db import csv_store, pdf_store


async def search_student_records(query : str) :
   
    docs = await csv_store.asimilarity_search(query, k=5)

    results = "\n\n".join([doc.page_content for doc in docs])

    return results if results else "No matching student records found."


async def search_student_personality(query : str) :
   
    docs = await pdf_store.asimilarity_search(query, k=5)

    results = "\n\n".join([doc.page_content for doc in docs])

    return results if results else "No matching student records found."

