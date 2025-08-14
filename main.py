from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import os
import shutil
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from murf import Murf
from murf.core.api_error import ApiError
import assemblyai as aai
import google.generativeai as genai
from typing import Dict, List

import time

load_dotenv()

# Configure APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# In-memory datastore for chat history
chat_sessions: Dict[str, List[Dict[str, str]]] = {}


app = FastAPI(title="30 Days Voice Agents - Day 10", version="1.0.0")

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")
# Initialize Murf client
murf_client = Murf(api_key=os.getenv("MURF_API_KEY"))

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    format: str = "MP3"
    sample_rate: float = 44100.0

class TTSResponse(BaseModel):
    audio_url: str
    message: str

class TranscriptionResponse(BaseModel):
    transcription: str

@app.post("/agent/chat/{session_id}", response_model=TTSResponse)
async def agent_chat(session_id: str, file: UploadFile = File(...)):
    """
    Manages a conversational chat session with history.
    Audio -> STT -> Add to History -> LLM -> Add to History -> TTS -> Audio
    """
    # 1. Transcribe Audio
    if not aai.settings.api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    try:
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(file.file)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        user_query = transcript.text
        if not user_query:
            raise HTTPException(status_code=400, detail="No speech detected in audio.")

    except Exception as e:
        print(f"--- ERROR DURING TRANSCRIPTION: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not transcribe file: {e}")

    # 2. Manage Chat History & Query LLM
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    try:
        # Get or create chat session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])
        
        chat = chat_sessions[session_id]
        response = chat.send_message(user_query)
        llm_response_text = response.text
    except Exception as e:
        print(f"--- ERROR DURING LLM QUERY: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not get LLM response: {e}")

    # 3. Generate Murf TTS from LLM response
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        # Ensure response is not too long for Murf
        if len(llm_response_text) > 2900:
             llm_response_text = llm_response_text[:2900]

        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=llm_response_text,
            voice_id="en-US-natalie"
        )
        return TTSResponse(audio_url=tts_resp.audio_file, message="LLM response audio generated successfully")
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        print(f"--- ERROR DURING MURF TTS GENERATE: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not generate TTS audio: {e}")

@app.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate TTS audio using Murf SDK
    """
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        response = murf_client.text_to_speech.generate(
            format=request.format,
            sample_rate=request.sample_rate,
            text=request.text,
            voice_id=request.voice_id,
        )
        audio_url = response.audio_file
        return TTSResponse(
            audio_url=audio_url,
            message="TTS audio generated successfully"
        )
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Murf API error: {e.body}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts/echo", response_model=TTSResponse)
async def echo_tts(file: UploadFile = File(...)):
    """
    Echo Bot v2: Transcribe uploaded audio, generate new audio via Murf, and return its URL.
    """
    # Transcribe the audio
    if not aai.settings.api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    try:
        cfg = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=cfg)
        transcript = transcriber.transcribe(file.file)
        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        text = transcript.text
    except Exception as e:
        print(f"--- ERROR DURING TRANSCIBE FOR ECHO: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not transcribe for echo: {e}")
    # Generate Murf TTS from transcribed text
    try:
        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=text,
            voice_id="en-US-natalie"
        )
        return TTSResponse(audio_url=tts_resp.audio_file, message="Echo audio generated successfully")
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        print(f"--- ERROR DURING MURF ECHO GENERATE: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not generate echo audio: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "FastAPI server running", "day": 10, "features": ["TTS", "Conversational Agent"]}

@app.get("/", response_class=HTMLResponse)
async def root():
    timestamp = int(time.time())
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day 12 - Voice Agents UI Revamp</title>
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
            <p>Day 12: UI Revamp</p>
        </div>
    </div>
    <script src="/static/script.js?v={timestamp}"></script>
</body>
</html>
'''

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    format: str = "MP3"
    sample_rate: float = 44100.0

class TTSResponse(BaseModel):
    audio_url: str
    message: str

class TranscriptionResponse(BaseModel):
    transcription: str

class LLMQueryRequest(BaseModel):
    query: str

class LLMQueryResponse(BaseModel):
    response: str

@app.post("/llm/query", response_model=TTSResponse)
async def llm_query(file: UploadFile = File(...)):
    """
    Accepts audio, transcribes it, sends to LLM, then to Murf TTS, and returns audio.
    """
    # 1. Transcribe Audio
    if not aai.settings.api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    try:
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(file.file)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        user_query = transcript.text
        if not user_query:
            raise HTTPException(status_code=400, detail="No speech detected in audio.")

    except Exception as e:
        print(f"--- ERROR DURING TRANSCRIPTION: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not transcribe file: {e}")

    # 2. Query LLM
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Simple prompt tweak to keep responses shorter for Murf
        prompt = f"Please answer the following question concisely: {user_query}"
        response = model.generate_content(prompt)
        llm_response_text = response.text
    except Exception as e:
        print(f"--- ERROR DURING LLM QUERY: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not get LLM response: {e}")

    # 3. Generate Murf TTS from LLM response
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        # Ensure response is not too long for Murf
        if len(llm_response_text) > 2900:
             llm_response_text = llm_response_text[:2900]

        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=llm_response_text,
            voice_id="en-US-natalie"
        )
        return TTSResponse(audio_url=tts_resp.audio_file, message="LLM response audio generated successfully")
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        print(f"--- ERROR DURING MURF TTS GENERATE: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not generate TTS audio: {e}")


@app.post("/transcribe/file", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Receives an audio file and returns the transcription with error handling.
    """
    if not aai.settings.api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    try:
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=config)
        
        transcript = transcriber.transcribe(file.file)

        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")

        return TranscriptionResponse(transcription=transcript.text)
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- ERROR DURING AUDIO TRANSCRIPTION: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not transcribe file: {e}")

@app.post("/tts/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate TTS audio using Murf SDK
    """
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        response = murf_client.text_to_speech.generate(
            format=request.format,
            sample_rate=request.sample_rate,
            text=request.text,
            voice_id=request.voice_id,
        )
        audio_url = response.audio_file
        return TTSResponse(
            audio_url=audio_url,
            message="TTS audio generated successfully"
        )
    except ApiError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Murf API error: {e.body}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts/echo", response_model=TTSResponse)
async def echo_tts(file: UploadFile = File(...)):
    """
    Echo Bot v2: Transcribe uploaded audio, generate new audio via Murf, and return its URL.
    """
    # Transcribe the audio
    if not aai.settings.api_key:
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    try:
        cfg = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcriber = aai.Transcriber(config=cfg)
        transcript = transcriber.transcribe(file.file)
        if transcript.status == aai.TranscriptStatus.error:
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        text = transcript.text
    except Exception as e:
        print(f"--- ERROR DURING TRANSCIBE FOR ECHO: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not transcribe for echo: {e}")
    # Generate Murf TTS from transcribed text
    try:
        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=text,
            voice_id="en-US-natalie"
        )
        return TTSResponse(audio_url=tts_resp.audio_file, message="Echo audio generated successfully")
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        print(f"--- ERROR DURING MURF ECHO GENERATE: {e} ---")
        raise HTTPException(status_code=500, detail=f"Could not generate echo audio: {e}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "FastAPI server running", "day": 9, "features": ["TTS", "Echo TTS", "LLM Query"]}

@app.get("/", response_class=HTMLResponse)
async def root():
    timestamp = int(time.time())
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day 9 - Voice Agents Challenge</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body class="matrix-bg">
    <div class="matrix-container">
        <h1 class="matrix-text" data-text="DAY 9 - Voice Query">DAY 9 - Voice Query</h1>
        <div class="rain"></div>
        <form id="tts-form" style="margin-bottom: 30px; z-index:2;">
            <input type="text" id="tts-input" placeholder="Enter text to synthesize..." style="padding:10px; font-size:18px; width:300px; border-radius:5px; border:1px solid #0f0; background:#000; color:#0f0;" required />
            <button type="submit" style="padding:10px 20px; font-size:18px; border-radius:5px; border:none; background:#0f0; color:#000; margin-left:10px; cursor:pointer;">Generate</button>
        </form>
        <audio id="tts-audio" controls style="display:none; margin-bottom:20px; z-index:2;"></audio>
        <div id="tts-message" style="color:#0f0; margin-bottom:10px; z-index:2;"></div>

        <!-- Echo Bot Section -->
        <div id="echo-bot-section" style="margin-top:40px; z-index:2; width:100%; max-width:400px;">
            <h1 style="color:#0f0; font-size:2em; text-align:center; margin-bottom:20px;">Echo Bot</h1>
            <div style="display:flex; justify-content:center; gap:10px; margin-bottom:20px;">
                <button id="start-record" style="padding:10px 20px; font-size:18px; border-radius:5px; border:none; background:#0f0; color:#000; cursor:pointer;">Start Recording</button>
                <button id="stop-record" style="padding:10px 20px; font-size:18px; border-radius:5px; border:none; background:#f00; color:#fff; cursor:pointer;" disabled>Stop Recording</button>
            </div>
            <audio id="echo-audio" controls style="display:none; width:100%;"></audio>
            <div id="echo-message" style="color:#0f0; text-align:center; margin-top:10px;"></div>
        </div>

        <div class="server-info">
            <p>🚀 Powered by FastAPI</p>
            <p>30 Days of Voice Agents Challenge</p>
            <p>🎵 TTS API Ready</p>
        </div>
    </div>
    <script src="/static/script.js?v={timestamp}"></script>
</body>
</html>
'''





