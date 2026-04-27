import os
from groq import Groq
from dotenv import load_dotenv
import streamlit as st
from streamlit_chat import message
import json
from datetime import datetime
import base64
import sqlite3
import hashlib

load_dotenv()

# Database initialization for chat history
def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id TEXT,
                  session_id TEXT,
                  role TEXT,
                  content TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_chat(user_id, session_id, role, content):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''INSERT INTO chats (user_id, session_id, role, content)
                 VALUES (?, ?, ?, ?)''', (user_id, session_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(user_id, session_id):
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''SELECT role, content FROM chats 
                 WHERE user_id = ? AND session_id = ?
                 ORDER BY timestamp''', (user_id, session_id))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

# Initialize database
init_db()

# Page config with custom theme
st.set_page_config(
    page_title="AI Chatbot Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    .assistant-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4caf50;
    }
    code {
        background-color: #f4f4f4;
        padding: 2px 6px;
        border-radius: 3px;
        font-family: monospace;
    }
    pre {
        background-color: #f4f4f4;
        padding: 1rem;
        border-radius: 0.5rem;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 AI Chatbot Pro")
    st.markdown("---")
    
    # Model selection
    st.subheader("🎯 Model Selection")
    model_options = {
        "Llama 3.3 70B (Best)": "llama-3.3-70b-versatile",
        "Llama 3.1 70B (Fast)": "llama-3.1-70b-versatile",
        "Mixtral 8x7B (Balanced)": "mixtral-8x7b-32768",
        "Gemma 2 9B (Fastest)": "gemma2-9b-it"
    }
    selected_model = st.selectbox("Choose AI Model", list(model_options.keys()))
    model = model_options[selected_model]
    
    st.markdown("---")
    
    # Temperature slider
    st.subheader("🌡️ Temperature")
    temperature = st.slider("Creativity Level", 0.0, 1.0, 0.7, 0.1)
    
    st.markdown("---")
    
    # Chat controls
    st.subheader("💬 Chat Controls")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.success("Chat cleared!")
    
    if st.button("📥 Export Chat"):
        if st.session_state.messages:
            chat_data = json.dumps(st.session_state.messages, indent=2)
            b64 = base64.b64encode(chat_data.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="chat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Chat</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.warning("No chat to export!")
    
    st.markdown("---")
    
    # File upload
    st.subheader("📁 File Upload")
    uploaded_file = st.file_uploader("Upload a file", type=['txt', 'pdf', 'doc', 'docx'])
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        # Process file content
        try:
            content = uploaded_file.read()
            if uploaded_file.type == "text/plain":
                text_content = content.decode("utf-8")
                st.text_area("File Content:", text_content, height=200)
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    st.markdown("---")
    
    # Stats
    st.subheader("📊 Statistics")
    st.metric("Messages", len(st.session_state.get("messages", [])))
    
    st.markdown("---")
    st.caption("Powered by Groq + Llama 3")

# Main chat interface
st.title("🤖 AI Chatbot Pro")
st.markdown("Advanced AI Assistant with Multiple Models")

# Get API key from .env file or environment
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ API Key not found in .env file")
    st.info("Make sure .env file is uploaded with GROQ_API_KEY")
    st.stop()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = Groq(api_key=api_key)

if "user_id" not in st.session_state:
    st.session_state.user_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]

if "session_id" not in st.session_state:
    st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]

if "chat_count" not in st.session_state:
    st.session_state.chat_count = 0

# Rate limiting
MAX_CHATS_PER_HOUR = 100
if st.session_state.chat_count >= MAX_CHATS_PER_HOUR:
    st.error("❌ Rate limit exceeded! Please wait before sending more messages.")
    st.stop()

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Save user message to database
    save_chat(st.session_state.user_id, st.session_state.session_id, "user", prompt)
    st.session_state.chat_count += 1
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = st.session_state.client.chat.completions.create(
                model=model,
                messages=st.session_state.messages,
                temperature=temperature,
                max_tokens=2048,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Save to database
            save_chat(st.session_state.user_id, st.session_state.session_id, "assistant", full_response)
            st.session_state.chat_count += 1
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.info("Please try again or check your API key.")

# Analytics Dashboard (at the bottom)
st.markdown("---")
st.subheader("📊 Analytics Dashboard")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Messages", len(st.session_state.get("messages", [])))
with col2:
    st.metric("Session ID", st.session_state.session_id[:8] + "...")
with col3:
    st.metric("Rate Limit", f"{st.session_state.chat_count}/{MAX_CHATS_PER_HOUR}")

# Recent activity
st.subheader("🕒 Recent Activity")
conn = sqlite3.connect('chat_history.db')
c = conn.cursor()
c.execute('''SELECT role, content, timestamp FROM chats 
             ORDER BY timestamp DESC LIMIT 5''')
recent_chats = c.fetchall()
conn.close()

if recent_chats:
    for role, content, timestamp in recent_chats:
        with st.expander(f"{role.upper()} - {timestamp}"):
            st.text(content[:200] + "..." if len(content) > 200 else content)
else:
    st.info("No recent activity")
