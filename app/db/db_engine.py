import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DB_URL.replace("asyncpg", "psycopg2")
)

db = SQLDatabase(engine)