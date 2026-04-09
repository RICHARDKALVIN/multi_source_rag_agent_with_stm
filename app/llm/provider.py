import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from app.db.db_engine import db
from app.tools.multi_source_tool import search_student_personality, search_student_records

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0,
    api_key= os.getenv("GEMINI_API_KEY"),
    max_output_tokens=2000
)

llm_agent = ChatGoogleGenerativeAI(
    model="gemini-flash-latest",
    temperature=0,
    api_key= os.getenv("GEMINI_API_KEY"),

)
rewiter_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite-preview",
    temperature=0,
    api_key= os.getenv("GEMINI_API_KEY"),
    max_output_tokens=100
)

toolkit = SQLDatabaseToolkit(db=db, llm=llm_agent)
sql_tools = toolkit.get_tools()


combined_tools = [search_student_personality, search_student_records] + sql_tools

system_prompt = (
    "You are a helpful assistant with access to a student database"
    "If a question requires data from the database, use the SQL tools. ")


agent = create_agent(
    model=llm_agent, 
    tools=combined_tools,
    system_prompt=system_prompt
   
)

