from app.db.chroma_db import csv_store, pdf_store
from langchain_community.document_loaders import PyPDFLoader, CSVLoader
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter

async def load_data():

    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    file_path_1 = project_root / "data" / "my_file.csv"
    file_path_2 = project_root / "data" / "my_pdf.pdf"

    csv_loader = CSVLoader(file_path_1)
    pdf_loader = PyPDFLoader(file_path_2)

    csv_docs = csv_loader.load()
    pdf_docs = pdf_loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=10,
        add_start_index=True 
    )

    csv_chunks = text_splitter.split_documents(csv_docs)
    pdf_chunks = text_splitter.split_documents(pdf_docs)

    await csv_store.aadd_documents(csv_chunks)
    await pdf_store.aadd_documents(pdf_chunks)

    return {"message": "Data loaded successfully"}