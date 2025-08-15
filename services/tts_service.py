import os
from murf import Murf
from murf.core.api_error import ApiError
from fastapi import HTTPException

murf_client = Murf(api_key=os.getenv("MURF_API_KEY"))

def generate_tts_audio(text: str, voice_id: str = "en-US-natalie") -> str:
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        if len(text) > 2900:
            text = text[:2900]
        
        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=text,
            voice_id=voice_id
        )
        return tts_resp.audio_file
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate TTS audio: {e}")
