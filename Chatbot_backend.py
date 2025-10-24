# Chatbot_backend.py -----------------------------------------------------------
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
import sqlite3
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import os

load_dotenv()

google_api_key = os.getenv("GOOGLE_API_KEY")
llm = init_chat_model("google_genai:gemini-2.0-flash")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Tools
search_tool = DuckDuckGoSearchRun()
wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

@tool
def calculate(first_n: float, second_n: float, opertn: str) -> dict:
    """Perform basic arithmetic operations."""
    try:
        if opertn == 'add':
            result = first_n + second_n
        elif opertn == 'subtract':
            result = first_n - second_n
        elif opertn == 'multiply':
            result = first_n * second_n
        elif opertn == 'divide':
            result = first_n / second_n if second_n != 0 else "Cannot divide by zero"
        else:
            result = "Invalid operation"

        return {"first_number": first_n, "second_number": second_n, "operation": opertn, "result": result}
    except Exception as e:
        return {"error": str(e)}

tools = [search_tool, calculate, wikipedia_tool]

llm_with_tools = llm.bind_tools(tools)
tool_node = ToolNode(tools=tools)

def chat_node(state: ChatState):
    messages = state['messages']
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph = StateGraph(ChatState)
graph.add_node('chat_node', chat_node)
graph.add_node('tools', tool_node)

graph.add_edge(START, 'chat_node')
graph.add_conditional_edges('chat_node', tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    unique_threads = set()
    for checkpoint in checkpointer.list(None):
        unique_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(unique_threads)
