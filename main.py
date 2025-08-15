import time
import logging
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE other imports
load_dotenv()

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import services and schemas
from services.stt_service import transcribe_audio_data
from services.llm_service import query_llm
from services.tts_service import generate_tts_audio
from schemas.tts import TTSResponse, TTSRequest
from schemas.stt import TranscriptionResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="30 Days of AI Voice Agents - Day 14 Refactor",
    version="1.1.0",
    description="A refactored, maintainable voice agent using FastAPI and various AI services."
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/agent/chat/{session_id}", response_model=TTSResponse)
async def agent_chat(session_id: str, file: UploadFile = File(...)):
    """
    Main conversational endpoint.
    Handles the full pipeline: Audio -> STT -> LLM -> TTS -> Audio
    """
    logging.info(f"Received chat request for session_id: {session_id}")
    
    # Read audio data into memory
    audio_data = await file.read()
    
    # 1. Transcribe Audio
    logging.info("Transcribing audio...")
    user_query = transcribe_audio_data(audio_data)
    logging.info(f"Transcription successful: '{user_query}'")
    
    # 2. Query LLM with chat history
    logging.info("Querying LLM...")
    llm_response_text = query_llm(session_id, user_query)
    logging.info(f"LLM response received: '{llm_response_text}'")
    
    # 3. Generate TTS from LLM response
    logging.info("Generating TTS audio...")
    audio_url = generate_tts_audio(llm_response_text)
    logging.info(f"TTS audio generated successfully: {audio_url}")
    
    return TTSResponse(audio_url=audio_url, message="LLM response audio generated successfully")

@app.post("/tts/generate", response_model=TTSResponse)
async def generate_tts_endpoint(request: TTSRequest):
    """
    Endpoint for generating TTS audio from text.
    """
    logging.info(f"Received TTS generation request for text: '{request.text[:30]}...'")
    audio_url = generate_tts_audio(request.text, request.voice_id)
    logging.info(f"TTS audio generated: {audio_url}")
    return TTSResponse(audio_url=audio_url, message="TTS audio generated successfully")

@app.post("/transcribe/file", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """
    Endpoint for transcribing an audio file.
    """
    logging.info("Received request to transcribe an audio file.")
    audio_data = await file.read()
    transcription = transcribe_audio_data(audio_data)
    logging.info(f"Transcription successful: '{transcription}'")
    return TranscriptionResponse(transcription=transcription)

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify server status.
    """
    logging.info("Health check requested.")
    return {
        "status": "healthy",
        "message": "FastAPI server running",
        "day": 14,
        "features": ["Refactored Services", "TTS", "STT", "LLM", "Conversational Agent"]
    }

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serves the main HTML page for the voice agent UI.
    """
    timestamp = int(time.time())
    # HTML content remains the same as Day 12
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day 14 - Voice Agent Refactor</title>
    <link rel="stylesheet" href="/static/style.css?v={timestamp}">
    <link href="https://fonts.googleapis.com/css2?family=Material+Icons" rel="stylesheet">
</head>
<body class="matrix-bg">
    <div class="matrix-container">
        <h1 class="matrix-text" data-text="AI Voice Agent">AI Voice Agent</h1>
        
        <!-- Agent Section -->
        <div id="agent-section">
            <button id="record-btn">
                <span class="material-icons icon">mic</span>
            </button>
            <audio id="echo-audio" autoplay></audio>
            <div id="echo-message">Click the mic to start</div>
        </div>

        <div class="server-info">
            <p>🚀 30 Days of Voice Agents Challenge</p>
            <p>Day 14: Code Refactor</p>
        </div>
    </div>
    <script src="/static/script.js?v={timestamp}"></script>
</body>
</html>
'''





