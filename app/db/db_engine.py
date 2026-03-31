import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from langchain_community.utilities import SQLDatabase

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DB_URL)

db = SQLDatabase.from_uri(
    DB_URL.replace("asyncpg", "psycopg2"), 
    engine=engine
)