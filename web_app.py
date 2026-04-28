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
    url_pattern = re.compile(r'https?://\S+')
    return bool(url_pattern.match(text))

def is_image_generation_request(text):
    keywords = ['generate image', 'create image', 'make image', 'draw', 'picture', 'photo', 'image of', 'picture of', 'logo', 'design', 'icon', 'illustration', 'art', 'visual', 'graphic']
    return any(keyword in text.lower() for keyword in keywords)

def generate_image(prompt):
    import urllib.parse
    import requests
    try:
        # Clean the prompt for URL - better extraction
        clean_prompt = prompt
        # Remove common prefixes
        for prefix in ['generate image of', 'create image of', 'draw a', 'make a', 'make an image of', 'create a', 'generate a']:
            clean_prompt = clean_prompt.replace(prefix, "").strip()
        
        # Add quality keywords for better results
        if 'logo' in clean_prompt.lower():
            clean_prompt += ", professional logo design, vector style, clean"
        elif 'icon' in clean_prompt.lower():
            clean_prompt += ", modern icon design, minimalist"
        else:
            clean_prompt += ", high quality, detailed, professional"
        
        encoded_prompt = urllib.parse.quote(clean_prompt)
        # Use Pollinations.ai with better parameters
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={hash(prompt)}"
        
        # Fetch image data immediately
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            return image_url, response.content
        else:
            return image_url, None
    except Exception as e:
        return None, None

# Page config with custom theme
st.set_page_config(
    page_title="AI Chatbot Pro",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Mode ChatGPT-like UI
st.markdown("""
<style>
    /* Light Mode Colors */
    .stApp {
        background-color: #ffffff !important;
    }
    
    /* Hide default Streamlit elements */
    [data-testid="stHeader"], [data-testid="stSidebarNav"], [data-testid="stSidebarUser"] {
        display: none !important;
    }
    
    /* Padding removal */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 800px !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f9f9f9 !important;
        border-right: 1px solid #e5e5e5;
        width: 260px !important;
    }
    
    /* Main content area */
    .main {
        background-color: #ffffff !important;
    }
    
    /* Chat messages */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        padding: 1.5rem 0 !important;
    }
    
    /* User message - right aligned pill */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarUser"]) {
        background-color: transparent !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarUser"]) [data-testid="stChatMessageContent"] {
        background-color: #f0f0f0 !important;
        border-radius: 1rem !important;
        padding: 1rem 1.5rem !important;
        max-width: 70% !important;
        margin-left: auto !important;
    }
    
    /* AI message - left aligned transparent */
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarAssistant"]) {
        background-color: transparent !important;
    }
    
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarAssistant"]) [data-testid="stChatMessageContent"] {
        background-color: transparent !important;
        padding: 0 !important;
    }
    
    /* Input container */
    [data-testid="stChatInputContainer"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e5e5 !important;
        border-radius: 1rem !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        width: 70% !important;
        max-width: 768px !important;
        margin: 0 auto !important;
    }
    
    /* Input box */
    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #1a1a1a !important;
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
        background-color: #f9f9f9 !important;
    }
    
    [data-testid="stSidebar"] .stSelectbox {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #e5e5e5 !important;
    }
    
    [data-testid="stSidebar"] label {
        color: #1a1a1a !important;
    }
    
    [data-testid="stSidebar"] button {
        background-color: #ffffff !important;
        color: #1a1a1a !important;
        border: 1px solid #e5e5e5 !important;
    }
    
    [data-testid="stSidebar"] button:hover {
        background-color: #f0f0f0 !important;
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6 {
        color: #1a1a1a !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    p, div, span {
        color: #1a1a1a !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
    }
    
    /* Code blocks */
    code {
        background-color: #f0f0f0 !important;
        color: #1a1a1a !important;
        padding: 0.2rem 0.4rem !important;
        border-radius: 0.25rem !important;
        font-family: 'Fira Code', 'Consolas', monospace !important;
    }
    
    pre {
        background-color: #f0f0f0 !important;
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
        color: #1a1a1a !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #666666 !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #ffffff !important;
        border: 1px dashed #e5e5e5 !important;
    }
    
    /* Expander */
    [data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e5e5e5 !important;
    }
    
    /* Error messages */
    .stAlert {
        background-color: #fef2f2 !important;
        border: 1px solid #fecaca !important;
    }
    
    /* Success messages */
    .stSuccess {
        background-color: #f0fdf4 !important;
        border: 1px solid #bbf7d0 !important;
    }
    
    /* Warning messages */
    .stWarning {
        background-color: #fefce8 !important;
        border: 1px solid #fef08a !important;
    }
    
    /* Info messages */
    .stInfo {
        background-color: #f0f9ff !important;
        border: 1px solid #bae6fd !important;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f9f9f9;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #d1d5db;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #9ca3af;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    # New Chat button with pencil icon
    if st.button("📝 New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]
        st.success("New chat started!")
    
    st.markdown("---")
    
    # Search bar
    st.text_input("🔍 Search chats", placeholder="Search...")
    
    st.markdown("---")
    
    # Chat categories
    st.subheader("Projects")
    if st.button("Image Editing"):
        pass
    if st.button("TikTok Prompts"):
        pass
    if st.button("Website Design"):
        pass
    
    st.markdown("---")
    
    st.subheader("Recents")
    # Chat History from database
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''SELECT DISTINCT session_id, MIN(timestamp) as first_msg 
                 FROM chats 
                 GROUP BY session_id 
                 ORDER BY first_msg DESC 
                 LIMIT 5''')
    sessions = c.fetchall()
    conn.close()
    
    if sessions:
        for session_id, timestamp in sessions:
            if st.button(f"Chat {session_id[:8]}...", key=f"chat_{session_id}", use_container_width=True):
                st.session_state.session_id = session_id
                st.session_state.messages = get_chat_history(st.session_state.user_id, session_id)
                st.rerun()
    else:
        st.info("No recent chats")
    
    st.markdown("---")
    
    # User profile at bottom
    st.markdown("### Malik")
    st.markdown("**Free**")
    st.button("Claim offer", use_container_width=True)

# Main chat interface
# Get API key from .env file or environment first
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

# Define model
model = "llama-3.3-70b-versatile"

# Rate limiting
MAX_CHATS_PER_HOUR = 100
if st.session_state.chat_count >= MAX_CHATS_PER_HOUR:
    st.error("Rate limit exceeded! Please wait before sending more messages.")
    st.stop()

# Show centered heading when no messages
if not st.session_state.messages:
    st.markdown('<div style="text-align: center; margin-top: 20vh;"><h1 style="font-size: 2.5rem; color: #1a1a1a;">What\'s on your mind today?</h1></div>', unsafe_allow_html=True)

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
    
    # Check if prompt is an image generation request - handle BEFORE LLM
    if is_image_generation_request(prompt):
        with st.chat_message("assistant"):
            # Show loading spinner while generating
            with st.spinner("Generating image..."):
                # Generate image URL and fetch data immediately
                image_url, image_data = generate_image(prompt)
            
            if image_url and image_data:
                try:
                    # Show success and image together using fetched data
                    st.success("Image generated!")
                    st.image(image_data, caption="Generated Image", use_column_width=True)
                    
                    # Save to database
                    response_text = f"Generated image based on: {prompt}\n\n[Image]({image_url})"
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    save_chat(st.session_state.user_id, st.session_state.session_id, "assistant", response_text)
                    st.session_state.chat_count += 1
                except Exception as e:
                    st.error(f"Error displaying image: {e}")
                    st.markdown(f"Image URL: {image_url}")
            else:
                st.error("Failed to generate image. Please try again.")
        st.stop()  # Stop here, don't continue to LLM
    
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
            
            # Add interactive icons below AI response (no emojis)
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
            with col1:
                st.button("Read", key=f"read_{len(st.session_state.messages)}")
            with col2:
                st.button("Like", key=f"like_{len(st.session_state.messages)}")
            with col3:
                st.button("Dislike", key=f"dislike_{len(st.session_state.messages)}")
            with col4:
                if st.button("Copy", key=f"copy_{len(st.session_state.messages)}"):
                    st.code(full_response)
            with col5:
                st.button("Regenerate", key=f"regen_{len(st.session_state.messages)}")
            
            # Save to database
            save_chat(st.session_state.user_id, st.session_state.session_id, "assistant", full_response)
            st.session_state.chat_count += 1
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Please try again or check your API key.")

# Disclaimer text below input
st.markdown('<div style="text-align: center; color: #666; font-size: 0.75rem; margin-top: 1rem;">ChatGPT can make mistakes. Check important info.</div>', unsafe_allow_html=True)
