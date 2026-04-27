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
import requests
from bs4 import BeautifulSoup
import re

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

# Web browsing functions
def fetch_url(url):
    """Fetch content from a URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching URL: {str(e)}"

def extract_text_from_html(html):
    """Extract text from HTML"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:2000]  # Limit to 2000 characters
    except Exception as e:
        return f"Error extracting text: {str(e)}"

def is_url(text):
    """Check if text is a URL"""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return bool(url_pattern.match(text))

# Page config with custom theme
st.set_page_config(
    page_title="AI Chatbot Pro",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ChatGPT-like UI
st.markdown("""
<style>
    /* ChatGPT Dark Mode Colors */
    .stApp {
        background-color: #343541 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #202123 !important;
        border-right: 1px solid #4d4d4f;
    }
    
    /* Main content area */
    .main {
        background-color: #343541 !important;
    }
    
    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
    }
    
    /* User message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarUser"]) {
        background-color: transparent !important;
    }
    
    /* AI message */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarAssistant"]) {
        background-color: #444654 !important;
    }
    
    /* Input container */
    [data-testid="stChatInputContainer"] {
        background-color: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1rem !important;
    }
    
    /* Input box */
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #ececf1 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Send button */
    [data-testid="stChatInput"] button {
        background-color: #10a37f !important;
        color: white !important;
        border-radius: 0.5rem !important;
    }
    
    /* Sidebar elements */
    [data-testid="stSidebar"] > div:first-child {
        background-color: #202123 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox {
        background-color: #2a2b32 !important;
        color: #ececf1 !important;
        border: 1px solid #4d4d4f !important;
    }
    
    [data-testid="stSidebar"] label {
        color: #ececf1 !important;
    }
    
    [data-testid="stSidebar"] .stSlider {
        color: #10a37f !important;
    }
    
    [data-testid="stSidebar"] button {
        background-color: #2a2b32 !important;
        color: #ececf1 !important;
        border: 1px solid #4d4d4f !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #3a3b42 !important;
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6 {
        color: #ececf1 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    p, div, span {
        color: #ececf1 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Code blocks */
    code {
        background-color: #2d2d3a !important;
        color: #e0e0e0 !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 0.25rem !important;
        font-family: 'Fira Code', 'Consolas', monospace !important;
    }
    
    pre {
        background-color: #2d2d3a !important;
        padding: 1rem !important;
        border-radius: 0.5rem !important;
        overflow-x: auto !important;
    }
    
    pre code {
        background-color: transparent !important;
        padding: 0 !important;
    }
    
    /* Metrics and stats */
    [data-testid="stMetricValue"] {
        color: #ececf1 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #8e8ea0 !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #2a2b32 !important;
        border: 1px dashed #565869 !important;
    }
    
    /* Expander */
    [data-testid="stExpander"] {
        background-color: #2a2b32 !important;
        border: 1px solid #4d4d4f !important;
    }
    
    /* Error messages */
    .stAlert {
        background-color: #5a1a1a !important;
        border: 1px solid #8b2a2a !important;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #1a5a3a !important;
        border: 1px solid #2a8b5a !important;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #5a4a1a !important;
        border: 1px solid #8b7a2a !important;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #1a3a5a !important;
        border: 1px solid #2a5a8b !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #202123;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4d4d4f;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #565869;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # New Chat button at top
    if st.button("New Chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]
        st.success("New chat started!")
    
    st.markdown("---")
    
    # Chat History from database
    st.subheader("Recent Chats")
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''SELECT DISTINCT session_id, MIN(timestamp) as first_msg 
                 FROM chats 
                 GROUP BY session_id 
                 ORDER BY first_msg DESC 
                 LIMIT 10''')
    sessions = c.fetchall()
    conn.close()
    
    if sessions:
        for session_id, timestamp in sessions:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(f"Chat {session_id[:8]}...", key=f"chat_{session_id}", use_container_width=True):
                        # Load chat history
                        st.session_state.session_id = session_id
                        st.session_state.messages = get_chat_history(st.session_state.user_id, session_id)
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"delete_{session_id}"):
                        # Delete chat
                        conn = sqlite3.connect('chat_history.db')
                        c = conn.cursor()
                        c.execute('''DELETE FROM chats WHERE session_id = ?''', (session_id,))
                        conn.commit()
                        conn.close()
                        st.rerun()
    else:
        st.info("No recent chats")
    
    st.markdown("---")
    
    # Model selection
    model = "llama-3.3-70b-versatile"
    
    st.markdown("---")
    
    # Chat controls
    st.subheader("Chat Controls")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.success("Chat cleared!")
    
    if st.button("Export Chat"):
        if st.session_state.messages:
            chat_data = json.dumps(st.session_state.messages, indent=2)
            b64 = base64.b64encode(chat_data.encode()).decode()
            href = f'<a href="data:file/json;base64,{b64}" download="chat_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Chat</a>'
            st.markdown(href, unsafe_allow_html=True)
        else:
            st.warning("No chat to export!")
    
    st.markdown("---")
    
    # File upload with image preview
    st.subheader("File/Image Upload")
    uploaded_file = st.file_uploader("Upload a file or image", type=['txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif'])
    if uploaded_file:
        st.success(f"File uploaded: {uploaded_file.name}")
        # Image preview
        if uploaded_file.type in ['image/png', 'image/jpeg', 'image/jpg', 'image/gif']:
            st.image(uploaded_file, caption="Preview", use_column_width=True)
        # Process file content
        try:
            content = uploaded_file.read()
            if uploaded_file.type == "text/plain":
                text_content = content.decode("utf-8")
                st.text_area("File Content:", text_content, height=200)
            elif uploaded_file.type.startswith('image/'):
                # Convert to base64 for AI processing
                import base64
                image_base64 = base64.b64encode(content).decode()
                st.session_state.uploaded_image = image_base64
                st.info("Image ready for AI analysis")
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    st.markdown("---")
    
    # Stats
    st.subheader("Statistics")
    st.metric("Messages", len(st.session_state.get("messages", [])))
    
    st.markdown("---")
    st.caption("Powered by Groq + Llama 3")

# Main chat interface
st.markdown("")  # Empty space for better layout

# Get API key from .env file or environment
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("API Key not found in .env file")
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
    
    # Check if prompt contains URL for web browsing
    web_content = ""
    source_url = ""
    if is_url(prompt):
        with st.chat_message("assistant"):
            st.info("Searching the web...")
            html = fetch_url(prompt)
            web_content = extract_text_from_html(html)
            source_url = prompt
            st.success(f"Found content from: {prompt}")
    
    # Add web content to messages if available
    messages_to_send = st.session_state.messages.copy()
    if web_content:
        messages_to_send.append({
            "role": "system",
            "content": f"User provided URL content: {web_content}\n\nPlease analyze this content and provide a helpful response. Cite the source: {source_url}"
        })
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = st.session_state.client.chat.completions.create(
                model=model,
                messages=messages_to_send,
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response)
            
            # Add source citation if web content was used
            if source_url:
                full_response += f"\n\n**Source:** [{source_url}]({source_url})"
                response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Save to database
            save_chat(st.session_state.user_id, st.session_state.session_id, "assistant", full_response)
            st.session_state.chat_count += 1
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Please try again or check your API key.")
