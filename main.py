import time
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE other imports
load_dotenv()

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Import services and schemas
from services.stt_service import transcribe_audio_data
from services.llm_service import query_llm
from services.tts_service import generate_tts_audio, generate_comedian_tts_audio
from services.chat_persistence import chat_db
from schemas.tts import TTSResponse, TTSRequest
from schemas.stt import TranscriptionResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI(
    title="30 Days of AI Voice Agents - Complete Voice Agent",
    version="2.0.0",
    description="A complete conversational voice agent with chat persistence, real-time streaming, and enhanced UI."
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
    
    # 3. Generate TTS from LLM response with comedian voice
    logging.info("Generating comedian TTS audio...")
    audio_url = generate_comedian_tts_audio(llm_response_text)
    logging.info(f"Comedian TTS audio generated successfully: {audio_url}")
    
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
        "day": 25,
        "features": ["Complete Voice Agent", "Chat Persistence", "Streaming Audio", "Real-time Transcription", "LLM Integration", "Retry Handling", "Web Search"]
    }

@app.post("/search/web")
async def web_search_endpoint(query: str):
    """
    Day 25: Web search endpoint using Tavily API
    Allows RAVI to search the web for current information
    """
    logging.info(f"Web search requested for: '{query}'")
    try:
        from services.web_search_service import search_and_format_for_comedy
        result = await search_and_format_for_comedy(query)
        return JSONResponse(content={
            "query": query,
            "result": result,
            "success": True
        })
    except Exception as e:
        logging.error(f"Web search failed: {e}")
        return JSONResponse(content={
            "query": query,
            "result": f"Arre yaar! My internet is acting up today. Error: {str(e)} 😅",
            "success": False
        }, status_code=500)

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 10):
    """
    Get chat history for a specific session.
    """
    logging.info(f"Getting chat history for session: {session_id}")
    history = chat_db.get_chat_history(session_id, limit)
    return JSONResponse(content={"session_id": session_id, "history": history})

@app.get("/api/chat/sessions")
async def get_chat_sessions(limit: int = 20):
    """
    Get list of recent chat sessions.
    """
    logging.info("Getting list of chat sessions")
    sessions = chat_db.get_session_list(limit)
    return JSONResponse(content={"sessions": sessions})

@app.delete("/api/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear chat history for a specific session.
    """
    logging.info(f"Clearing chat history for session: {session_id}")
    success = chat_db.clear_session_history(session_id)
    if success:
        return JSONResponse(content={"message": "Chat history cleared successfully"})
    else:
        return JSONResponse(content={"error": "Failed to clear chat history"}, status_code=500)

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
        <title>Day 24 - RAVI Comedy Voice Agent</title>
    <link rel="stylesheet" href="/static/style.css?v={timestamp}">
    <link href="https://fonts.googleapis.com/css2?family=Material+Icons" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <!-- Sidebar like ChatGPT -->
    <div class="sidebar">
        <div class="sidebar-header">
            <div class="sidebar-title">
                <span class="material-icons">🎭</span>
                Comedy Sessions
            </div>
            <button id="new-session-btn" class="new-session-btn">
                <span class="material-icons">add</span>
                New Comedy Chat
            </button>
        </div>
        
        <div class="sidebar-content">
            <div id="sessions-list" class="sessions-list">
                <!-- Sessions will be loaded here -->
            </div>
        </div>
        
        <div class="sidebar-footer">
            <div class="current-session">
                <span class="material-icons">account_circle</span>
                <div class="session-info">
                    <div class="session-name">Current Session</div>
                    <div class="session-id" id="current-session-id"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content Area -->
    <div class="main-content">
        <!-- Header -->
        <div class="main-header">
            <h1 class="app-title">
                <span class="material-icons">🎭</span>
                RAVI - Your Comedy AI Assistant
            </h1>
            <div class="app-subtitle">Day 24 - Standup Comedian Voice Agent</div>
        </div>

        <!-- Voice Agent Section -->
        <div class="voice-agent-container">
            <div class="voice-agent-card">
                <div class="agent-status">
                    <div id="agent-status-indicator" class="status-indicator idle"></div>
                    <span id="agent-status-text">Ready to listen</span>
                </div>
                
                <div class="voice-controls">
                    <button id="record-btn" class="voice-btn">
                        <span class="material-icons icon">mic</span>
                    </button>
                </div>
                
                <div id="echo-message" class="agent-message">Arre yaar! Click the mic and let's have some fun! 😄</div>
                
                <!-- Audio Element (Hidden) -->
                <audio id="echo-audio" autoplay style="display: none;"></audio>
                
                <!-- Audio Indicator -->
                <div id="audio-indicator" class="audio-indicator" style="display: none;">
                    <span class="material-icons">volume_up</span>
                    Playing response...
                </div>
            </div>
        </div>

        <!-- Conversation Area -->
        <div class="conversation-container">
            <!-- Live Transcript -->
            <div class="transcript-section">
                <div class="section-header">
                    <span class="material-icons">transcribe</span>
                    Live Transcript
                </div>
                <div id="current-transcript" class="live-transcript"></div>
            </div>

            <!-- Conversation History -->
            <div class="conversation-section">
                <div class="section-header">
                    <span class="material-icons">chat</span>
                    Conversation
                </div>
                <div id="conversation-history" class="conversation-history">
                    <div class="welcome-message">
                        <span class="material-icons">🎭</span>
                        <h3>Namaste! I'm RAVI, your Comedy AI Assistant!</h3>
                        <p>Ready for some laughs? Just click the mic and let's chat, yaar! I'll crack jokes while solving your problems. Guaranteed entertainment with every response! 😄</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Toast Container -->
    <div id="toast-container" class="toast-container"></div>

    <script src="/static/script.js?v={timestamp}"></script>
</body>
</html>
'''

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass


# --- Day 17: Streaming Audio with AssemblyAI (v3 SDK) ---
import os
import queue
import threading
from assemblyai.streaming.v3 import (
    BeginEvent,
    StreamingClient,
    StreamingClientOptions,
    StreamingError,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
)

# IMPORTANT: Set your AssemblyAI API key in your .env file
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if not ASSEMBLYAI_API_KEY:
    raise ValueError("ASSEMBLYAI_API_KEY environment variable not set.")

# Define event handlers
def on_begin(self, event: BeginEvent):
    logging.info(f"Session started: {event.id}")

def on_turn(self, event: TurnEvent):
    logging.info(f"Turn: {event.transcript} (end_of_turn: {event.end_of_turn})")

def on_terminated(self, event: TerminationEvent):
    logging.info(f"Session terminated: {event.audio_duration_seconds}s of audio processed")

def on_error(self, error: StreamingError):
    logging.error(f"Error occurred: {error}")

from assemblyai import extras

# ... existing code ...

import assemblyai as aai

# ... existing code ...

import assemblyai as aai
from assemblyai.streaming.v3 import (
    StreamingClient,
    StreamingClientOptions,
    StreamingEvents,
    StreamingParameters,
    TerminationEvent,
    TurnEvent,
    StreamingError,
    BeginEvent,
)

# ... existing code ...

def run_transcription(audio_queue: queue.Queue, message_queue: queue.Queue, websocket_conn=None, session_id: str | None = None):
    """Runs the transcription in a separate thread."""
    logging.info("Transcription thread started.")
    
    # Store the full transcript for the current turn
    current_transcript = ""

    def on_begin(client, event: BeginEvent):
        logging.info(f"Session started: {event.id}")

    def on_turn(client, event: TurnEvent):
        nonlocal current_transcript
        if event.transcript:
            current_transcript = event.transcript
            logging.info(f"Turn: {event.transcript} (end_of_turn: {event.end_of_turn})")
            
            if event.end_of_turn:
                try:
                    import json
                    message = {
                        "type": "turn_end",
                        "transcript": current_transcript,
                        "timestamp": time.time()
                    }
                    
                    message_queue.put(json.dumps(message))
                    
                    logging.info(f"Turn ended - queued transcript for client: '{current_transcript}'")
                    # --- Day 21: Stream LLM response to Murf WebSocket and send audio to client ---
                    from services.llm_service import stream_llm_to_murf_and_client
                    print(f"\n[Day 21] Sending transcript to LLM and Murf, then streaming audio to client: '{current_transcript}'")
                    
                    # Capture the transcript value to avoid closure issues
                    transcript_to_process = current_transcript
                    
                    # Create a task to run the async function
                    import threading
                    def run_async_task(transcript, ws_connection, sess_id):
                        print(f"🔍 Inside run_async_task, transcript: '{transcript}'")
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(stream_llm_to_murf_and_client(transcript, ws_connection, session_id=sess_id))
                        finally:
                            loop.close()
                    
                    # Run in a separate thread to avoid blocking
                    task_thread = threading.Thread(target=run_async_task, args=(transcript_to_process, websocket_conn, session_id))
                    task_thread.daemon = True
                    task_thread.start()
                    
                    current_transcript = ""  # Reset for next turn
                except Exception as e:
                    logging.error(f"Error processing turn end: {e}")

    def on_error(client, error: StreamingError):
        logging.error(f"An error occurred: {error}")

    def on_terminated(client, event: TerminationEvent):
        logging.info(f"Session terminated: {event.audio_duration_seconds}s of audio processed")

    try:
        if not aai.settings.api_key:
            raise ValueError("AssemblyAI API key is not set.")

        client = StreamingClient(
            StreamingClientOptions(
                api_key=aai.settings.api_key,
            )
        )

        client.on(StreamingEvents.Begin, on_begin)
        client.on(StreamingEvents.Turn, on_turn)
        client.on(StreamingEvents.Error, on_error)
        client.on(StreamingEvents.Termination, on_terminated)

        client.connect(
            StreamingParameters(
                sample_rate=16_000,
                enable_turn_detection=True,  # Enable turn detection
            )
        )

        # Buffer audio chunks to meet AssemblyAI's duration requirements (50-1000ms)
        buffer = bytearray()
        target_chunk_size = 1600  # 50ms at 16kHz 16-bit mono (16000 * 0.05 * 2 bytes)

        def audio_generator(q: queue.Queue):
            nonlocal buffer
            while True:
                chunk = q.get()
                if chunk is None:
                    # Send any remaining buffered audio before stopping
                    if buffer:
                        yield bytes(buffer)
                    break
                
                buffer.extend(chunk)
                
                # Send chunks when we have enough audio (50ms worth)
                while len(buffer) >= target_chunk_size:
                    yield bytes(buffer[:target_chunk_size])
                    buffer = buffer[target_chunk_size:]
                
                q.task_done()

        client.stream(audio_generator(audio_queue))

    except Exception as e:
        logging.error(f"Error during transcription: {e}", exc_info=True)
    finally:
        logging.info("Transcription thread finished.")




@app.websocket("/ws/stream-audio")
async def stream_audio_websocket(websocket: WebSocket):
    # Extract session_id from query params
    session_id = websocket.query_params.get("session_id")

    await websocket.accept()
    logging.info(f"WebSocket connection established. session_id={session_id}")

    audio_queue = queue.Queue()
    message_queue = queue.Queue()  # Queue for messages from transcription thread
    
    transcription_thread = threading.Thread(
        target=run_transcription, args=(audio_queue, message_queue, websocket, session_id)
    )
    transcription_thread.start()

    async def send_queued_messages():
        """Send any queued messages to the client."""
        try:
            while True:
                message = message_queue.get_nowait()
                await websocket.send_text(message)
                logging.info(f"Sent message to client: {message}")
                message_queue.task_done()
        except queue.Empty:
            pass

    try:
        while True:
            # Always check for messages first
            await send_queued_messages()
            
            # Handle incoming audio data with a timeout
            try:
                data = await asyncio.wait_for(websocket.receive_bytes(), timeout=0.1)
                audio_queue.put(data)
            except asyncio.TimeoutError:
                continue  # Continue checking for messages
                
    except WebSocketDisconnect:
        logging.info("WebSocket disconnected by client.")
        # Signal the transcription thread to stop
        audio_queue.put(None)
    except Exception as e:
        logging.error(f"An error occurred in the websocket: {e}", exc_info=True)
        # Signal the transcription thread to stop
        audio_queue.put(None)
    finally:
        # Wait for the transcription thread to finish
        if transcription_thread.is_alive():
            transcription_thread.join()
        logging.info("WebSocket connection closed.")






