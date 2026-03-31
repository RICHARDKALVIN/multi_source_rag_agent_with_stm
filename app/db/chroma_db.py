from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

csv_store = Chroma(
    collection_name="csv_data", 
    embedding_function=embeddings,
    persist_directory="./chroma_db_data"
)


pdf_store = Chroma(
    collection_name="pdf_documents", 
    embedding_function=embeddings,
    persist_directory="./chroma_db_data" 
)

