import time
import logging
import asyncio
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE other imports
load_dotenv()

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
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

# Global variable to store runtime API keys
runtime_api_keys = {}

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

@app.post("/api/test-keys")
async def test_api_keys(request: dict):
    """
    Test the provided API keys to verify they are valid.
    """
    logging.info("Testing API keys")
    results = {}
    
    # Test AssemblyAI key
    if request.get('assemblyai'):
        try:
            import assemblyai as aai
            aai.settings.api_key = request['assemblyai']
            # Simple test - create a client (this validates the key format)
            client = aai.TranscriptionConfig()
            results['assemblyai'] = '✅ Valid'
        except Exception as e:
            results['assemblyai'] = f'❌ Invalid: {str(e)[:50]}...'
    else:
        results['assemblyai'] = '⚠️ Not provided'
    
    # Test OpenAI key
    if request.get('openai'):
        try:
            import openai
            client = openai.OpenAI(api_key=request['openai'])
            # Test with a simple completion
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            results['openai'] = '✅ Valid'
        except Exception as e:
            results['openai'] = f'❌ Invalid: {str(e)[:50]}...'
    else:
        results['openai'] = '⚠️ Not provided'
    
    # Test Murf key (basic format check since we can't easily test without making a request)
    if request.get('murf'):
        murf_key = request['murf']
        if len(murf_key) > 10:  # Basic length check
            results['murf'] = '✅ Format looks valid'
        else:
            results['murf'] = '❌ Key too short'
    else:
        results['murf'] = '⚠️ Not provided'
    
    # Test Tavily key
    if request.get('tavily'):
        try:
            import requests
            headers = {'Authorization': f'Bearer {request["tavily"]}'}
            # Simple API call to test key
            response = requests.get('https://api.tavily.com/health', headers=headers, timeout=5)
            if response.status_code in [200, 401]:  # 401 might indicate key format is recognized
                results['tavily'] = '✅ Valid'
            else:
                results['tavily'] = f'❌ HTTP {response.status_code}'
        except Exception as e:
            results['tavily'] = f'❌ Invalid: {str(e)[:50]}...'
    else:
        results['tavily'] = '⚠️ Not provided'
    
    # Check if all keys are valid
    valid_count = sum(1 for result in results.values() if result.startswith('✅'))
    total_count = len(results)
    
    return JSONResponse(content={
        "success": True,
        "message": f"API Key Test Results: {valid_count}/{total_count} valid",
        "results": results
    })

@app.post("/api/set-runtime-keys")
async def set_runtime_keys(request: dict):
    """
    Set API keys for runtime use (stored in memory for the session).
    """
    logging.info("Setting runtime API keys")
    
    # Store keys in a global variable for runtime use
    global runtime_api_keys
    runtime_api_keys = {
        'assemblyai': request.get('assemblyai', ''),
        'openai': request.get('openai', ''),
        'murf': request.get('murf', ''),
        'tavily': request.get('tavily', '')
    }
    
    return JSONResponse(content={
        "success": True,
        "message": "API keys set for runtime use"
    })

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serves the main HTML page for the voice agent UI.
    """
    timestamp = int(time.time())
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAVI - Your Comedy AI Assistant</title>
    <link rel="stylesheet" href="/static/style.css">
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
</head>
<body>
    <div class="main-container">
        <!-- Left Panel: Sessions -->
        <div class="sessions-panel">
            <div class="sessions-header">
                <h2>Comedy Sessions</h2>
                <div class="header-buttons">
                    <button id="config-btn" title="API Configuration" class="config-btn">
                        <span class="material-icons">settings</span>
                    </button>
                    <button id="new-session-btn" title="New Comedy Chat">+</button>
                </div>
            </div>
            
            <!-- Configuration Section (Initially Hidden) -->
            <div id="config-section" class="config-section" style="display: none;">
                <div class="config-header">
                    <h3><span class="material-icons">key</span> API Configuration</h3>
                    <button id="close-config-btn" class="close-btn">
                        <span class="material-icons">close</span>
                    </button>
                </div>
                
                <div class="config-form">
                    <div class="config-group">
                        <label for="assemblyai-key">AssemblyAI API Key</label>
                        <div class="input-group">
                            <input type="password" id="assemblyai-key" placeholder="Enter AssemblyAI API key" />
                            <button type="button" class="toggle-visibility" data-target="assemblyai-key">
                                <span class="material-icons">visibility</span>
                            </button>
                        </div>
                        <small>Used for speech-to-text transcription</small>
                    </div>
                    
                    <div class="config-group">
                        <label for="openai-key">OpenAI API Key</label>
                        <div class="input-group">
                            <input type="password" id="openai-key" placeholder="Enter OpenAI API key" />
                            <button type="button" class="toggle-visibility" data-target="openai-key">
                                <span class="material-icons">visibility</span>
                            </button>
                        </div>
                        <small>Used for LLM responses and conversations</small>
                    </div>
                    
                    <div class="config-group">
                        <label for="murf-key">Murf API Key</label>
                        <div class="input-group">
                            <input type="password" id="murf-key" placeholder="Enter Murf API key" />
                            <button type="button" class="toggle-visibility" data-target="murf-key">
                                <span class="material-icons">visibility</span>
                            </button>
                        </div>
                        <small>Used for text-to-speech generation</small>
                    </div>
                    
                    <div class="config-group">
                        <label for="tavily-key">Tavily API Key</label>
                        <div class="input-group">
                            <input type="password" id="tavily-key" placeholder="Enter Tavily API key" />
                            <button type="button" class="toggle-visibility" data-target="tavily-key">
                                <span class="material-icons">visibility</span>
                            </button>
                        </div>
                        <small>Used for web search functionality</small>
                    </div>
                    
                    <div class="config-actions">
                        <button id="save-config-btn" class="save-btn">
                            <span class="material-icons">save</span>
                            Save Configuration
                        </button>
                        <button id="test-config-btn" class="test-btn">
                            <span class="material-icons">check_circle</span>
                            Test Keys
                        </button>
                    </div>
                    
                    <div id="config-status" class="config-status"></div>
                </div>
            </div>
            
            <div id="sessions-list">
                <!-- Session items will be loaded here by script.js -->
            </div>
            <div class="session-info">
                <p>Current Session: <span id="current-session-id"></span></p>
            </div>
        </div>

        <!-- Center Panel: Agent Interaction -->
        <div class="main-panel">
            <header class="main-header">
                <h1>RAVI - Your Comedy AI Assistant</h1>
                <p>Day 24 - Standup Comedian Voice Agent</p>
            </header>

            <div id="agent-section">
                <div id="agent-status">
                    <span id="agent-status-indicator" class="status-indicator idle"></span>
                    <span id="agent-status-text">Ready to listen</span>
                </div>
                <button id="record-btn">
                    <span class="icon material-icons">mic</span>
                </button>
                <p id="echo-message">Click the microphone to start</p>
                <div id="audio-indicator" style="display: none;">
                    <div class="dot"></div>
                    <div class="dot"></div>
                    <div class="dot"></div>
                </div>
            </div>

            <div class="transcript-section">
                <h3><span class="material-icons">mic</span> Live Transcript</h3>
                <p id="current-transcript"></p>
            </div>
            
            <audio id="echo-audio" style="display: none;"></audio>
        </div>

        <!-- Right Panel: Chat History -->
        <div class="chat-panel">
            <div class="chat-header">
                <h2><span class="material-icons">forum</span> Conversation</h2>
            </div>
            <div id="conversation-history">
                <!-- Chat messages will be loaded here -->
            </div>
        </div>
    </div>

    <div id="toast-container"></div>

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

# API keys will be provided by users via the frontend

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
        # Use runtime API key if available
        global runtime_api_keys
        assemblyai_key = runtime_api_keys.get('assemblyai') if runtime_api_keys else None
        
        if not assemblyai_key:
            logging.warning("AssemblyAI API key not available in runtime. Streaming transcription may not work.")
            return
        
        # Set the API key for this session
        aai.settings.api_key = assemblyai_key

        client = StreamingClient(
            StreamingClientOptions(
                api_key=assemblyai_key,
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

# For local development
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get port from environment variable (for Render deployment) or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True if os.getenv("ENVIRONMENT") != "production" else False
    )