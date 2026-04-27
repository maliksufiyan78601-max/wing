# AI Chatbot Pro - Advanced AI Assistant

A powerful, feature-rich AI chatbot powered by Groq API and multiple LLM models. Deploy to the web and use it from anywhere!

## Features

### Enhanced UI
- Beautiful gradient background
- Custom chat message styling
- Professional design with responsive layout
- Code highlighting for technical responses

### Multiple AI Models
- **Llama 3.3 70B** - Best quality, most intelligent
- **Llama 3.1 70B** - Fast and high quality
- **Mixtral 8x7B** - Balanced performance
- **Gemma 2 9B** - Fastest response time

### Advanced Chat Features
- **Chat History Persistence** - All conversations saved to SQLite database
- **Export Chat** - Download your conversations as JSON
- **Clear Chat** - Start fresh with one click
- **Temperature Control** - Adjust AI creativity level (0.0-1.0)

### File Upload
- Upload text files (TXT, PDF, DOC, DOCX)
- Read and analyze file content
- Context-aware responses based on uploaded files

### Analytics Dashboard
- Real-time message statistics
- Session tracking
- Rate limit monitoring
- Recent activity log

### Security & Performance
- **Rate Limiting** - 100 messages/hour to prevent abuse
- **Session Management** - Unique session IDs for tracking
- **Error Handling** - Graceful error messages
- **Database Backup** - Automatic chat history saving

### Deployment Options
- **Streamlit Cloud** - Free hosting with subdomain
- **Render** - Free with custom domain support
- **Vercel** - Free with custom domain support
- **Self-hosted** - Run on your own server

## Installation

### 1. Get Free Groq API Key
1. Go to https://console.groq.com
2. Sign up (free, no credit card required)
3. Go to API Keys section
4. Create a new API key
5. Copy the key

### 2. Configure Environment
1. Open `.env` file
2. Add your API key:
   ```
   GROQ_API_KEY=gsk_your_actual_key_here
   ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Locally
```bash
streamlit run web_app.py
```
Then open http://localhost:8501

## Deploy to Web

### Option 1: Streamlit Cloud (Recommended - Free)

1. **Create GitHub Repository**
   - Upload all files to GitHub
   - Files needed: `web_app.py`, `requirements.txt`, `.env`, `README.md`

2. **Deploy to Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Sign up (free, use GitHub)
   - Click "New app"
   - Connect your GitHub repository
   - Main file: `web_app.py`
   - Deploy

3. **Add API Key in Secrets**
   - Go to Settings → Secrets
   - Add: `GROQ_API_KEY = "gsk_your_key_here"` (TOML format with quotes)
   - Save and Rerun

4. **Your App is Live!**
   - Free URL: `https://your-app.streamlit.app`

### Option 2: Render (Free - Custom Domain)
1. Go to https://render.com
2. Connect GitHub repo
3. Add `GROQ_API_KEY` as environment variable
4. Deploy
5. Add custom domain in Settings (free!)

### Option 3: Vercel (Free - Custom Domain)
1. Go to https://vercel.com
2. Import GitHub repo
3. Add `GROQ_API_KEY` as environment variable
4. Deploy
5. Add custom domain in Settings (free!)

## Usage

### Basic Chat
- Type your message in the chat input
- AI responds intelligently
- Chat history is maintained during session
- All messages saved to database automatically

### Model Selection
- Use sidebar to select AI model
- Different models for different needs:
  - Use **Llama 3.3 70B** for complex tasks
  - Use **Gemma 2 9B** for fast responses
  - Use **Mixtral 8x7B** for balanced performance

### Temperature Control
- Adjust creativity level (0.0 - 1.0)
- 0.0 = More focused, deterministic
- 1.0 = More creative, random
- Default: 0.7 (balanced)

### File Upload
- Upload text files in sidebar
- AI can read and analyze content
- Useful for document analysis

### Export Chat
- Click "Export Chat" in sidebar
- Downloads as JSON file
- Includes full conversation history

### Clear Chat
- Click "Clear Chat" to reset
- Starts fresh conversation
- Database keeps old history

## Database

The bot uses SQLite for chat history persistence:
- Automatic initialization on first run
- Stores: user_id, session_id, role, content, timestamp
- View analytics in dashboard
- All conversations backed up locally

## Configuration

### Environment Variables
```
GROQ_API_KEY=gsk_your_key_here
