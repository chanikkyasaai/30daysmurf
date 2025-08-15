from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "en-US-natalie"
    format: str = "MP3"
    sample_rate: float = 44100.0

class TTSResponse(BaseModel):
    audio_url: str
    message: str
