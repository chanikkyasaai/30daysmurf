# 🎭 RAVI - Your Comedy AI Voice Assistant

Welcome to the complete **30 Days of AI Voice Agents Challenge** project! Meet **RAVI**, a sophisticated conversational AI voice agent that combines speech recognition, natural language processing, text-to-speech, and even image generation into one seamless experience.

🌐 **Live Demo**: [https://ravi-murf.onrender.com](https://ravi-murf.onrender.com)

![UI Screenshot](static/ui-screenshot.png)

## 🚀 Project Overview

RAVI is a full-featured AI voice assistant that:
- 🎙️ **Listens** to your voice in real-time
- 🧠 **Understands** your requests using Google Gemini
- 🎭 **Responds** with personality as a standup comedian
- 🗣️ **Speaks** back using realistic Indian English voice
- 🖼️ **Generates** images when requested
- 🔍 **Searches** the web for current information
- 💾 **Remembers** conversation history
- 🌐 **Hosted** and ready for public use

## ✨ Key Features

### 🎯 Core Voice Capabilities
- **Real-time Speech-to-Text** using AssemblyAI with streaming
- **Advanced LLM Integration** with Google Gemini Pro
- **High-quality Text-to-Speech** using Murf AI with Indian English voice
- **WebSocket Streaming** for real-time audio processing
- **Session Management** with persistent chat history

### 🎭 Personality & Intelligence
- **Comedian Persona** - RAVI responds with humor and wit
- **Context Awareness** - Remembers previous conversations
- **Web Search Integration** - Access to current information via Tavily API
- **Image Generation** - Creates images using Stable Diffusion XL
- **Smart Responses** - Handles various topics with personality

### 🔧 Technical Excellence
- **Production Ready** - Deployed on Render.com
- **No Environment Variables Required** - User-provided API keys for security
- **Dynamic API Configuration** - Frontend configuration panel
- **Real-time WebSocket Communication** - Seamless voice streaming
- **Error Handling & Fallbacks** - Robust error recovery
- **Mobile Responsive** - Works on all devices

### 🎨 User Experience
- **Modern Animated UI** - Beautiful, intuitive interface
- **One-Click Voice Recording** - Simple microphone button
- **Live Transcription Display** - See speech-to-text in real-time
- **Session Management** - Multiple conversation sessions
- **Audio Indicators** - Visual feedback during processing
- **Toast Notifications** - User-friendly status updates

## 🛠️ Technologies Used

### Backend Stack
- **FastAPI** - High-performance Python web framework
- **WebSockets** - Real-time bidirectional communication
- **AssemblyAI** - Advanced speech recognition with streaming
- **Google Gemini Pro** - State-of-the-art language model
- **Murf AI** - Professional text-to-speech synthesis
- **Tavily API** - Real-time web search capabilities
- **Hugging Face** - Free image generation with Stable Diffusion

### Frontend Stack
- **Vanilla JavaScript** - Modern ES6+ features
- **WebAudio API** - Real-time audio processing
- **WebSockets** - Live audio streaming
- **CSS3 Animations** - Smooth, responsive UI
- **Local Storage** - Secure API key management

### Deployment & Infrastructure
- **Render.com** - Cloud hosting platform
- **GitHub Actions** - Automated deployments
- **Environment Agnostic** - No server-side secrets required

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Voice    │───▶│   Frontend JS    │───▶│  FastAPI Server │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                        ┌─────────────────────────────────┼─────────────────────────────────┐
                        │                                 │                                 │
                        ▼                                 ▼                                 ▼
                ┌───────────────┐                ┌─────────────────┐                ┌─────────────────┐
                │ AssemblyAI    │                │  Google Gemini  │                │    Murf AI      │
                │ (Speech-to-   │                │     (LLM)       │                │ (Text-to-Speech)│
                │    Text)      │                │                 │                │                 │
                └───────────────┘                └─────────────────┘                └─────────────────┘
                        │                                 │                                 │
                        │                                 ▼                                 │
                        │                        ┌─────────────────┐                       │
                        │                        │   Tavily API    │                       │
                        │                        │ (Web Search)    │                       │
                        │                        └─────────────────┘                       │
                        │                                 │                                 │
                        │                                 ▼                                 │
                        │                        ┌─────────────────┐                       │
                        │                        │ Hugging Face    │                       │
                        │                        │(Image Generation)│                       │
                        │                        └─────────────────┘                       │
                        │                                 │                                 │
                        └─────────────────────────────────┼─────────────────────────────────┘
                                                          │
                                                          ▼
                                                ┌─────────────────┐
                                                │   Frontend:     │
                                                │ Audio Playback  │
                                                │ Image Display   │
                                                └─────────────────┘
```

## 🚀 Getting Started

### Live Demo
Visit the hosted version: **[https://ravi-murf.onrender.com](https://ravi-murf.onrender.com)**

1. **Configure API Keys** - Click the settings icon and add your API keys
2. **Start Talking** - Click the microphone and start a conversation
3. **Enjoy** - Experience real-time voice conversation with RAVI!

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chanikkyasaai/30daysmurf.git
   cd 30daysmurf
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the server:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Open your browser:**
   Navigate to [http://localhost:8000](http://localhost:8000)

## 🔑 API Keys Required

The application requires the following API keys (configured via the frontend):

- **AssemblyAI API Key** - For speech-to-text transcription
- **Google Gemini API Key** - For LLM responses and conversations  
- **Murf API Key** - For text-to-speech generation
- **Tavily API Key** - For web search functionality (optional)

**Note**: No server-side environment variables needed! All keys are provided securely via the frontend.

## 📱 Usage Examples

### Basic Conversation
- **You**: "Hello RAVI, how are you?"
- **RAVI**: "Arre yaar! I'm doing fantastic! Thanks for asking. Ready for some comedy gold today?"

### Image Generation
- **You**: "Generate me an image of a sunset over mountains"
- **RAVI**: "Oh wow, getting all artistic now! Let me paint you a digital masterpiece..." *(generates and displays image)*

### Web Search
- **You**: "What's the latest news about AI?"
- **RAVI**: "Let me check the internet for you..." *(searches and provides current information)*

## 📦 API Endpoints

### Core Endpoints
- `POST /agent/chat/{session_id}` - Main conversational endpoint (audio in, audio out)
- `POST /tts/generate` - Direct text-to-speech conversion
- `POST /transcribe/file` - Audio file transcription
- `POST /search/web` - Web search functionality

### Configuration Endpoints
- `POST /api/set-runtime-keys` - Set API keys for session
- `POST /api/test-keys` - Test API key validity
- `GET /api/chat/history/{session_id}` - Get conversation history
- `DELETE /api/chat/history/{session_id}` - Clear conversation history

### WebSocket Endpoints
- `WS /ws/stream-audio` - Real-time audio streaming and processing

## 🌟 Advanced Features

### Real-time Audio Processing
- WebSocket-based audio streaming
- Live transcription display
- Continuous conversation flow
- Audio buffering and optimization

### Session Management
- Multiple conversation sessions
- Persistent chat history in localStorage
- Session switching and management
- Conversation export capabilities

### Error Handling
- Graceful fallback mechanisms
- User-friendly error messages
- Retry logic for failed requests
- Network connectivity handling

### Security & Privacy
- Client-side API key storage
- No server-side secrets
- Secure WebSocket connections
- Privacy-focused design

## 🎯 Day-by-Day Progress

This project was built over 30 days as part of the **#30DaysofVoiceAgents** challenge:

- **Days 1-5**: Basic FastAPI setup and core structure
- **Days 6-10**: Speech-to-text integration with AssemblyAI
- **Days 11-15**: LLM integration with Google Gemini
- **Days 16-20**: Text-to-speech with Murf AI
- **Days 21-25**: Real-time streaming and WebSocket implementation
- **Days 26-30**: Advanced features, hosting, and final polish

## 🚀 Deployment

The application is deployed on **Render.com** with:
- Automatic deployments from GitHub
- Environment-agnostic configuration
- Production-ready performance
- Global CDN distribution

### Deployment Configuration
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- **Python Version**: 3.11+
- **Dependencies**: All listed in `requirements.txt`

## 🤝 Contributing

Contributions are welcome! Please feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## � Acknowledgments

- **Murf AI** for the amazing text-to-speech capabilities
- **AssemblyAI** for robust speech recognition
- **Google** for the powerful Gemini language model
- **Hugging Face** for free image generation
- **30 Days of Voice Agents Challenge** for the inspiration

---

## 🔗 Links

- **Live Demo**: [https://ravi-murf.onrender.com](https://ravi-murf.onrender.com)
- **GitHub Repository**: [https://github.com/chanikkyasaai/30daysmurf](https://github.com/chanikkyasaai/30daysmurf)
- **LinkedIn**: [Post about this project](#)

---

**Built with ❤️ during the #30DaysofVoiceAgents challenge**

#BuildwithMurf #30DaysofVoiceAgents #AI #VoiceAgent #Python #FastAPI
