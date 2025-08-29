# 🚀 RAVI Comedy AI Assistant - Deployment Guide

## Day 28: Deploying to Render.com

### Prerequisites
- GitHub account
- Render.com account (free)
- Your API keys ready

### Step-by-Step Deployment

#### 1. Push to GitHub
```bash
git add .
git commit -m "Day 28: Prepare for deployment"
git push origin main
```

#### 2. Deploy on Render.com
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `ravi-comedy-ai-assistant`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: `Free`

#### 3. Set Environment Variables in Render
Add these environment variables in Render dashboard:
- `ASSEMBLYAI_API_KEY`: Your AssemblyAI key
- `GEMINI_API_KEY`: Your Google Gemini key  
- `MURF_API_KEY`: Your Murf API key
- `TAVILY_API_KEY`: Your Tavily search key
- `ENVIRONMENT`: `production`

#### 4. Deploy
- Click "Create Web Service"
- Wait for deployment (5-10 minutes)
- Your app will be live at: `https://your-app-name.onrender.com`

### Features Deployed
✅ Voice-to-Voice Conversation
✅ Real-time Speech Recognition  
✅ Comedy AI Assistant (RAVI)
✅ Text-to-Speech with Indian Voice
✅ Web Search Integration
✅ Image Generation (Free Stable Diffusion)
✅ Client-side Chat History (Privacy-focused)
✅ Multi-session Support
✅ API Key Configuration UI

### Cost Optimization
- Using FREE tiers:
  - Render.com: Free web service
  - Hugging Face: Free image generation
  - Client-side storage: No database costs
  
### Performance Features
- Optimized for free hosting
- Minimal server resources
- Client-side data storage
- No database required

### Security & Privacy
- API keys stored securely on Render
- Chat history stays on user's device
- No user data stored on server
- HTTPS enabled by default

## 🎉 Your Voice Agent is Live!

Share your deployed link on LinkedIn with:
#BuildwithMurf #30DaysofVoiceAgents
