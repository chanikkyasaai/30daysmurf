import os
import assemblyai as aai
from fastapi import HTTPException
import logging

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def transcribe_audio_data(audio_data: bytes) -> str:
    logging.info("--- ENTERING STT SERVICE ---")
    if not aai.settings.api_key:
        logging.error("AssemblyAI API key is not configured.")
        raise HTTPException(status_code=500, detail="AssemblyAI API key not configured")
    
    try:
        logging.info("Step 1: Creating TranscriptionConfig")
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        
        logging.info("Step 2: Creating Transcriber")
        transcriber = aai.Transcriber(config=config)
        
        logging.info("Step 3: Calling transcriber.transcribe()")
        transcript = transcriber.transcribe(audio_data)
        logging.info(f"Step 4: Transcription complete. Status: {transcript.status}")

        if transcript.status == aai.TranscriptStatus.error:
            logging.error(f"Transcription failed with error: {transcript.error}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {transcript.error}")
        
        if not transcript.text:
            logging.warning("No speech was detected in the audio.")
            raise HTTPException(status_code=400, detail="No speech detected in audio.")
            
        logging.info(f"Step 5: Transcription successful. Text: '{transcript.text[:50]}...'")
        return transcript.text
        
    except Exception as e:
        logging.error(f"An unexpected exception occurred in STT service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Could not transcribe audio data: {e}")
