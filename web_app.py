import os
from groq import Groq
import streamlit as st
from streamlit_chat import message

st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

st.title("🤖 AI Chatbot")
st.markdown("Powered by Groq + Llama 3 (Free)")

# Get API key from environment or secrets
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("Please set GROQ_API_KEY in Streamlit secrets")
    st.info("Go to Settings → Secrets and add GROQ_API_KEY")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "client" not in st.session_state:
    st.session_state.client = Groq(api_key=api_key)

for msg in st.session_state.messages:
    message(msg["content"], is_user=msg["role"] == "user")

if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True)
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            stream = st.session_state.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Error: {e}")
