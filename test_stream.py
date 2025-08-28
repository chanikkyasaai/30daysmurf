import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai

async def test_stream_llm():
    """Test the streaming LLM function"""
    if not os.getenv("GEMINI_API_KEY"):
        print("Gemini API key not configured")
        return
    
    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        query = "Hello, how are you?"
        
        print(f"Testing streaming with query: '{query}'")
        print("--- Streaming LLM response ---")
        
        stream = model.generate_content(query, stream=True)
        
        full_response = ""
        for chunk in stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text
        
        print("\n--- End of LLM response ---")
        print(f"Full response length: {len(full_response)}")
        print(f"Full response: '{full_response.strip()}'")
        
        if full_response.strip():
            print("✅ Response has content")
        else:
            print("❌ Response is empty")
            
    except Exception as e:
        print(f"Error in streaming: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_stream_llm())
