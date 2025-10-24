# chatbot_api.py ----------------------------------------------------------------
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from Chatbot_backend import chatbot, retrieve_all_threads
import uuid

app = FastAPI(title="LangGraph Chatbot API")

# ---------- Utility ---------- #
def generate_thread_id():
    return str(uuid.uuid4())

def load_conversation(thread_id: str):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])

# ---------- Request Models ---------- #
class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    thread_id: str
    response: str

class ThreadListResponse(BaseModel):
    threads: List[str]

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatHistoryResponse(BaseModel):
    thread_id: str
    history: List[HistoryMessage]

# ---------- Endpoints ---------- #

@app.get("/")
def read_root():    
    return {"message": "Welcome to the LangGraph Chatbot API"}  

@app.get("/threads", response_model=ThreadListResponse)
def get_all_threads():
    return {"threads": retrieve_all_threads()}

@app.post("/new_thread", response_model=ChatResponse)
def create_thread():
    thread_id = generate_thread_id()
    return {"thread_id": thread_id, "response": "New thread created"}

@app.post("/chat", response_model=ChatResponse)
async def chat(chat: ChatRequest):
    CONFIG = {
        "configurable": {"thread_id": chat.thread_id},
        "metadata": {"thread_id": chat.thread_id},
        "run_name": "chat_turn",
    }
    try:
        final_response = ""
        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=chat.message)]},
            config=CONFIG,
            stream_mode="messages"
        ):
            if isinstance(message_chunk, AIMessage):
                final_response += message_chunk.content

        return {"thread_id": chat.thread_id, "response": final_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{thread_id}", response_model=ChatHistoryResponse)
def history(thread_id: str):
    messages = load_conversation(thread_id)
    formatted = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted.append({"role": role, "content": msg.content})
    return {"thread_id": thread_id, "history": formatted}
