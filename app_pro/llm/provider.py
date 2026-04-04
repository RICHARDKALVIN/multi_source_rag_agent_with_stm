import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit



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

