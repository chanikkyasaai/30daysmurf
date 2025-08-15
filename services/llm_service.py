import os
import google.generativeai as genai
from fastapi import HTTPException
from typing import Dict, List

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

def query_llm(session_id: str, query: str) -> str:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    try:
        if session_id not in chat_sessions:
            chat_sessions[session_id] = genai.GenerativeModel('gemini-1.5-flash').start_chat(history=[])
        
        chat = chat_sessions[session_id]
        response = chat.send_message(query)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not get LLM response: {e}")
