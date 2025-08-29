import os
import json
import asyncio
import websockets
import logging
from typing import Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MurfWebSocketService:
    def __init__(self, api_key: str = None):
        # Use provided API key or get from runtime storage
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self.get_runtime_api_key()
        
        if not self.api_key:
            raise ValueError("Murf API key not configured. Please set it in the API configuration.")
        
        # Correct WebSocket URL from Murf API documentation
        self.websocket_url = "wss://api.murf.ai/v1/speech/stream-input"
        # Use a unique context per request to avoid active context limit issues
    
    def get_runtime_api_key(self) -> str:
        """Get Murf API key from runtime storage."""
        try:
            # Import here to avoid circular imports
            from main import runtime_api_keys
            return runtime_api_keys.get('murf', '')
        except:
            return ''
        
    async def send_text_to_murf(self, text: str, voice_id: str = "en-IN-rohan") -> Optional[str]:
        """
        Send text to Murf WebSocket API and receive base64 encoded audio.
        
        Args:
            text: The text to convert to speech
            voice_id: The voice ID to use (default: en-IN-rohan - Indian English male)
            
        Returns:
            base64 encoded audio string or None if failed
        """
        try:
            # Build WebSocket URL with query parameters as per documentation
            ws_url = f"{self.websocket_url}?api-key={self.api_key}&sample_rate=44100&channel_type=MONO&format=WAV"
            
            logger.info(f"Connecting to Murf WebSocket: {ws_url[:50]}...")
            
            async with websockets.connect(ws_url) as websocket:
                
                # Generate a unique context_id per request to avoid active context limit
                request_context_id = "murf_ctx_" + str(uuid.uuid4())[:8]

                # First, send voice configuration with request-specific context_id
                voice_config = {
                    "voice_config": {
                        "voiceId": voice_id,
                        "style": "Conversational",
                        "rate": 0,
                        "pitch": 0,
                        "variation": 1
                    },
                    "context_id": request_context_id
                }
                
                logger.info(f"Sending voice config: {voice_config}")
                await websocket.send(json.dumps(voice_config))
                
                # Then send the text with end=True to close the context
                text_message = {
                    "text": text,
                    "context_id": request_context_id,
                    "end": True  # This will close the context for concurrency
                }
                
                logger.info(f"Sending text to Murf: '{text}' (context_id={request_context_id})")
                await websocket.send(json.dumps(text_message))
                
                # Collect all audio chunks as raw bytes
                import base64
                audio_bytes = bytearray()
                
                while True:
                    response_raw = await websocket.recv()
                    response = json.loads(response_raw)
                    
                    logger.info(f"Received response: {response}")
                    
                    if "audio" in response:
                        # Each response["audio"] is a standalone base64 string.
                        # Decode to bytes and append so we don't end up with multiple padded base64 segments concatenated.
                        audio_chunk_b64 = response["audio"]
                        try:
                            chunk_bytes = base64.b64decode(audio_chunk_b64, validate=False)
                            audio_bytes.extend(chunk_bytes)
                            logger.info(f"Received audio chunk (b64 len: {len(audio_chunk_b64)} chars, bytes: {len(chunk_bytes)})")
                        except Exception as e:
                            logger.error(f"Failed to decode base64 audio chunk: {e}")
                    
                    # Check if this is the final response
                    if response.get("final"):
                        logger.info("Received final audio response")
                        break
                
                # Encode the combined bytes as a single base64 string
                if len(audio_bytes) > 0:
                    combined_audio_b64 = base64.b64encode(bytes(audio_bytes)).decode("ascii")
                    logger.info(f"Combined audio bytes: {len(audio_bytes)} → base64 length: {len(combined_audio_b64)}")
                    
                    print(f"\n=== MURF BASE64 AUDIO ===")
                    print(f"Text: '{text}'")
                    print(f"Voice ID: {voice_id}")
                    print(f"Base64 Audio (first 100 chars): {combined_audio_b64[:100]}...")
                    print(f"Base64 Audio (last 100 chars): ...{combined_audio_b64[-100:]}")
                    print(f"Total Base64 Length: {len(combined_audio_b64)} characters")
                    print("=== END MURF AUDIO ===\n")
                    
                    return combined_audio_b64
                else:
                    logger.error("No audio data received from Murf")
                    return None
                    
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"Murf WebSocket connection closed: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Murf response JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Error connecting to Murf WebSocket: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def stream_text_to_murf(self, text_chunks: list, voice_id: str = "en-IN-rohan") -> list:
        """
        Send multiple text chunks to Murf and collect all base64 audio responses.
        
        Args:
            text_chunks: List of text chunks to convert
            voice_id: The voice ID to use
            
        Returns:
            List of base64 encoded audio strings
        """
        audio_responses = []
        
        for i, chunk in enumerate(text_chunks):
            if chunk.strip():  # Only process non-empty chunks
                logger.info(f"Processing chunk {i+1}/{len(text_chunks)}: '{chunk[:30]}...'")
                audio_data = await self.send_text_to_murf(chunk.strip(), voice_id)
                if audio_data:
                    audio_responses.append(audio_data)
                
                # Small delay between requests to avoid rate limiting
                await asyncio.sleep(0.5)
        
        return audio_responses

# Function to create instance with runtime API key
def get_murf_service():
    """Get MurfWebSocketService instance with runtime API key."""
    return MurfWebSocketService()

async def send_to_murf_websocket(text: str, voice_id: str = "en-IN-rohan") -> Optional[str]:
    """
    Convenience function to send text to Murf WebSocket.
    
    Args:
        text: Text to convert to speech
        voice_id: Voice ID to use
        
    Returns:
        Base64 encoded audio or None
    """
    murf_service = get_murf_service()
    return await murf_service.send_text_to_murf(text, voice_id)
