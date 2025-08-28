import os
from murf import Murf
from murf.core.api_error import ApiError
from fastapi import HTTPException

murf_client = Murf(api_key=os.getenv("MURF_API_KEY"))

def generate_tts_audio(text: str, voice_id: str = "en-IN-rohan") -> str:
    """
    Generate TTS audio with comedian persona voice settings.
    Using Indian English male voice with customized parameters for standup comedy feel.
    """
    if not os.getenv("MURF_API_KEY"):
        raise HTTPException(status_code=500, detail="Murf API key not configured")
    try:
        if len(text) > 2900:
            text = text[:2900]
        
        # Enhanced TTS settings for comedian persona
        tts_resp = murf_client.text_to_speech.generate(
            format="MP3",
            sample_rate=44100.0,
            text=text,
            voice_id=voice_id  # Indian English male voice optimized for comedy
        )
        return tts_resp.audio_file
    except ApiError as e:
        raise HTTPException(status_code=e.status_code, detail=f"Murf API error: {e.body}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate TTS audio: {e}")

def generate_comedian_tts_audio(text: str) -> str:
    """
    Specialized TTS function for comedian persona with optimal Indian English male voices.
    """
    # Best Indian English male voices for comedy (in order of preference)
    indian_male_voices = [
        "en-IN-rohan",      # Best choice: Conversational, Promo, Narration - perfect for comedy
        "en-IN-aarav",      # Good alternative: Conversational style
        "en-IN-eashwar",    # Another option: Narration, Conversational
        "en-US-ronnie",     # Supports Indian English + multiple emotions (Angry, Sad, etc.)
    ]
    
    for voice in indian_male_voices:
        try:
            print(f"🎭 Trying comedian voice: {voice}")
            return generate_tts_audio(text, voice_id=voice)
        except Exception as e:
            print(f"❌ Voice {voice} failed: {e}")
            continue
    
    # Fallback to default
    print("⚠️ All preferred voices failed, using default")
    return generate_tts_audio(text)
