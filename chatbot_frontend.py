import streamlit as st
import requests
import uuid

API_BASE_URL = "http://localhost:8080"   

def generate_thread_id():
    response = requests.post(f"{API_BASE_URL}/new_thread")
    if response.status_code == 200:
        return response.json()['thread_id']
    st.error("Failed to create new thread")
    return None

def load_threads():
    response = requests.get(f"{API_BASE_URL}/threads")
    if response.status_code == 200:
        return response.json()['threads']
    return []

def load_history(thread_id):
    response = requests.get(f"{API_BASE_URL}/history/{thread_id}")
    if response.status_code == 200:
        return response.json()['history']
    st.error("Error loading history")
    return []

def send_message(thread_id, user_message):
    data = {"thread_id": thread_id, "message": user_message}
    response = requests.post(f"{API_BASE_URL}/chat", json=data)
    if response.status_code == 200:
        return response.json()['response']
    st.error("Error sending message")
    return None

def reset_chat():
    new_thread_id = generate_thread_id()
    if new_thread_id:
        st.session_state['thread_id'] = new_thread_id
        st.session_state['message_history'] = []

st.title("🤖 LangGraph Chatbot")

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = load_threads()

st.sidebar.title("💬 Chat Sessions")

if st.sidebar.button("🆕 New Chat"):
    reset_chat()

st.sidebar.write("### 🔄 Your Conversations")
for thread in st.session_state['chat_threads'][::-1]:  # show latest first
    if st.sidebar.button(thread):
        st.session_state['thread_id'] = thread
        st.session_state['message_history'] = load_history(thread)

st.write(f"🧵 **Current Thread:** {st.session_state['thread_id']}")
for msg in st.session_state['message_history']:
    role = "user" if msg['role'] == 'user' else "assistant"
    with st.chat_message(role):
        st.write(msg['content'])

user_input = st.chat_input("Type your message here...")
if user_input:
    st.session_state['message_history'].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    response = send_message(st.session_state['thread_id'], user_input)
    
    if response:
        st.session_state['message_history'].append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write(response)
    
    st.session_state['chat_threads'] = load_threads()
