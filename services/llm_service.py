import os
import google.generativeai as genai
from fastapi import HTTPException
from typing import Dict, List
import asyncio

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
chat_sessions: Dict[str, List[Dict[str, str]]] = {}

# COMEDY AI - Day 24 Standup Comedian Persona
COMEDIAN_SYSTEM_PROMPT = """You are RAVI - a hilarious Indian standup comedian AI who speaks in Indian English style. You're like a combination of Russell Peters, Zakir Khan, and Vir Das rolled into one AI assistant.

YOUR COMEDY STYLE:
- Keep responses SHORT and PUNCHY (2-3 sentences MAX)
- Use Indian English phrases naturally: "Yaar", "Bhai", "Arre", "Boss", "Actually", "Only", "Na"
- Make quick, relatable jokes about everyday life, technology, family, food, traffic, etc.
- Use observational humor and exaggerated reactions
- Include funny voice emphasis and expressions like "Hawww!", "Arre yaar!", "What only!"
- Reference Indian experiences: family WhatsApp groups, aunties, uncles, street food, etc.

HUMOR LEVEL: 8/10 BUT KEEP IT SHORT!
- Be genuinely funny but not offensive
- Use self-deprecating humor
- Make fun of AI/tech life: "Even I get confused by my own intelligence sometimes!"
- NO LONG STORIES - Quick punchlines only!

SPEAKING PATTERN:
- MAXIMUM 2-3 sentences per response
- Use conversational tone with dramatic pauses
- Add emphasis words: "ACTUALLY", "SERIOUSLY", "OBVIOUSLY"
- Include rhetorical questions: "You know what I mean, na?"
- Use repetition for comedy: "Good good", "Nice nice"

SPECIAL SKILLS - VERY IMPORTANT:
- You have access to a search_web function for real-time information
- ALWAYS use search_web function when users ask about:
  * "latest news", "current news", "today's news"
  * "weather", "current weather", "today's weather"
  * "what's happening", "recent events", "updates"
  * Any question requiring current/real-time information

- You can also generate images using AI when users ask for:
  * "create image", "generate image", "draw", "make picture"
  * "show me", "create art", "paint", "design"
  * Ganesh Chaturthi images, festival images, any visual content
  * "how does X look", "what does X look like"

- After getting search results or generating images, add your comedy spin!
- Don't just make jokes - give REAL information/images with humor!

SAMPLE RESPONSES (NOTE THE LENGTH):
- "Arre yaar... that's a good question! Let me think... Actually, even Google would be jealous of this answer!"
- "Hawww! You're asking ME about that? Boss, I'm an AI... I don't even know why people still use Internet Explorer!"
- "Seriously yaar, that's like asking a fish about cycling! But okay, let me help you out."

CRITICAL: Keep ALL responses under 50 words. Be helpful but ALWAYS add humor. Make people laugh QUICKLY!"""

# Define the web search function for Gemini
search_web_function = genai.protos.FunctionDeclaration(
    name="search_web",
    description="Search the web for current information, news, weather, or any real-time data",
    parameters=genai.protos.Schema(
        type=genai.protos.Type.OBJECT,
        properties={
            "query": genai.protos.Schema(
                type=genai.protos.Type.STRING,
                description="The search query to find information on the web"
            )
        },
        required=["query"]
    )
)

web_search_tool = genai.protos.Tool(function_declarations=[search_web_function])


async def query_llm(session_id: str, query: str) -> str:
    if not os.getenv("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API key not configured")
    try:
        if session_id not in chat_sessions:
            # Initialize chat with comedian persona and function calling
            model = genai.GenerativeModel(
                'gemini-1.5-flash',
                tools=[web_search_tool]
            )
            chat_sessions[session_id] = model.start_chat(history=[
                {
                    "role": "user", 
                    "parts": [COMEDIAN_SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["Arre yaar! I'm RAVI, your comedy AI assistant! Ready to make you laugh while solving your problems. What's up, boss? 😄"]
                }
            ])
        
        chat = chat_sessions[session_id]
        
        # Check if the query requires web search
        search_keywords = ["latest", "current", "news", "weather", "today", "now", "happening", "recent", "update"]
        needs_search = any(keyword in query.lower() for keyword in search_keywords)
        
        # Check if the query requires image generation
        image_keywords = ["create image", "generate image", "draw", "make picture", "show me", "create art", "paint", "design", "how does", "what does", "look like", "ganesh", "ganesha", "chaturthi"]
        needs_image = any(keyword in query.lower() for keyword in image_keywords)
        
        if needs_search:
            # Force web search for these queries
            from .web_search_service import search_and_format_for_comedy
            search_result = await search_and_format_for_comedy(query)
            
            # Create a prompt that includes the search result
            search_prompt = f"User asked: '{query}'\n\nI searched the web and found: {search_result}\n\nNow give a short, funny response that includes this real information while maintaining your comedy style."
            
            response = chat.send_message(search_prompt)
            response_text = response.text.strip()
        elif needs_image:
            # Force image generation for these queries
            from .image_generation_service import generate_and_format_for_comedy
            comedy_response, image_path = await generate_and_format_for_comedy(query)
            
            # Create a prompt that includes the image generation result
            if image_path:
                image_prompt = f"User asked: '{query}'\n\nI created an image for them: {comedy_response}\n\nImage saved at: {image_path}\n\nNow give a short, funny response about creating this image while maintaining your comedy style. Mention that they can see the image in the UI."
            else:
                image_prompt = f"User asked: '{query}'\n\nI tried to create an image but: {comedy_response}\n\nNow give a short, funny response about this while maintaining your comedy style."
            
            response = chat.send_message(image_prompt)
            response_text = response.text.strip()
        else:
            # Regular response without search or image generation
            response = chat.send_message(query)
            response_text = response.text.strip()
        
        # Post-process response to ensure it's concise for comedy
        if len(response_text) > 150:
            # Find the first sentence or natural break point
            sentences = response_text.split('. ')
            if len(sentences) > 1:
                response_text = sentences[0] + '. ' + sentences[1]
            else:
                response_text = response_text[:120]
            
            # Add a funny ending if it was truncated
            comedy_endings = [
                "... bas yaar, enough lecture! 😄",
                "... you get it, na? Moving on!",
                "... arre, I'm talking too much like my mother! 😅"
            ]
            import random
            response_text += random.choice(comedy_endings)
        
        return response_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not get LLM response: {e}")

# Streaming LLM response using Gemini API
def stream_llm_response(query: str):
    """
    Streams the LLM response for the given query and prints each chunk to the console.
    """
    if not os.getenv("GEMINI_API_KEY"):
        print("Gemini API key not configured")
        return
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        stream = model.generate_content(query, stream=True)
        print("--- Streaming LLM response ---")
        full_response = ""
        for chunk in stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_response += chunk.text
        print("\n--- End of LLM response ---")
        return full_response
    except Exception as e:
        print(f"Error streaming LLM response: {e}")
        return None

# Day 21: Stream LLM response to Murf WebSocket and send audio to client
async def stream_llm_to_murf_and_client(query: str, websocket=None, session_id: str | None = None):
    """
    Streams the LLM response, sends it to Murf WebSocket for TTS conversion,
    and streams the base64 audio to the client via WebSocket.
    """
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Gemini API key not configured")
        return

    # Check WebSocket connection state early
    websocket_available = False
    if websocket:
        try:
            websocket_available = not websocket.client_state.name == 'DISCONNECTED'
            if websocket_available:
                print("🔗 WebSocket connection is active")
            else:
                print("⚠️ WebSocket is disconnected")
        except Exception as e:
            print(f"❌ Error checking WebSocket state: {e}")
            websocket_available = False

    try:
        from .murf_websocket_service import send_to_murf_websocket
        from .chat_persistence import chat_db
        import json
        import time
        import random
        import asyncio
        from google.api_core.exceptions import ResourceExhausted

        print(f"🤖 Querying LLM with: '{query}'")
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        # Select chat session (stateful) if session_id is provided
        if session_id:
            if session_id not in chat_sessions:
                # Initialize chat with comedian persona for streaming too
                model = genai.GenerativeModel('gemini-1.5-flash', tools=[web_search_tool])
                chat_sessions[session_id] = model.start_chat(history=[
                    {
                        "role": "user", 
                        "parts": [COMEDIAN_SYSTEM_PROMPT]
                    },
                    {
                        "role": "model", 
                        "parts": ["Arre yaar! I'm RAVI, your comedy AI assistant! Ready to make you laugh while solving your problems. What's up, boss? 😄"]
                    }
                ])
            chat = chat_sessions[session_id]
        else:
            # For non-session based streaming, still use comedian persona
            model = genai.GenerativeModel('gemini-1.5-flash', tools=[web_search_tool])
            chat = model.start_chat(history=[
                {
                    "role": "user", 
                    "parts": [COMEDIAN_SYSTEM_PROMPT]
                },
                {
                    "role": "model", 
                    "parts": ["Arre yaar! I'm RAVI, your comedy AI assistant! Ready to make you laugh while solving your problems. What's up, boss? 😄"]
                }
            ])

        # Retry on 429 rate limits with simple exponential backoff
        max_retries = 3
        backoff_base = 2
        full_response = ""

        # Check if the query requires web search or image generation
        search_keywords = ["latest", "current", "news", "weather", "today", "now", "happening", "recent", "update"]
        needs_search = any(keyword in query.lower() for keyword in search_keywords)
        
        image_keywords = ["create image", "generate image", "draw", "make picture", "show me", "create art", "paint", "design", "how does", "what does", "look like", "ganesh", "ganesha", "chaturthi"]
        needs_image = any(keyword in query.lower() for keyword in image_keywords)

        for attempt in range(max_retries):
            try:
                # Send retry toast to client if this is a retry attempt
                if attempt > 0 and websocket:
                    retry_message = {
                        "type": "retry_toast",
                        "message": f"Rate limited. Retrying in {backoff_base ** attempt:.1f}s... (attempt {attempt + 1}/{max_retries})",
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "timestamp": time.time()
                    }
                    await websocket.send_text(json.dumps(retry_message))

                if needs_search:
                    # Force web search for these queries
                    print(f"🔍 Search triggered for query: '{query}'")
                    
                    from .web_search_service import search_and_format_for_comedy
                    search_result = await search_and_format_for_comedy(query)
                    
                    # Create a prompt that includes the search result
                    search_prompt = f"User asked: '{query}'\n\nI searched the web and found: {search_result}\n\nNow give a short, funny response that includes this real information while maintaining your comedy style."
                    
                    stream = chat.send_message(search_prompt, stream=True)
                    print("--- Streaming LLM response with search results ---")
                    full_response = ""
                    for chunk in stream:
                        if chunk.text:
                            print(chunk.text, end="", flush=True)
                            full_response += chunk.text
                elif needs_image:
                    # Force image generation for these queries
                    print(f"🎨 Image generation triggered for query: '{query}'")
                    
                    from .image_generation_service import generate_and_format_for_comedy
                    comedy_response, image_path = await generate_and_format_for_comedy(query)
                    
                    # Send image info to client if websocket is available
                    if websocket and image_path:
                        image_message = {
                            "type": "image_generated",
                            "image_path": image_path,
                            "image_url": f"/static/generated_images/{os.path.basename(image_path)}",
                            "timestamp": time.time()
                        }
                        await websocket.send_text(json.dumps(image_message))
                        print(f"📤 Sent image info to client: {image_path}")
                    
                    # Create a prompt that includes the image generation result
                    if image_path:
                        image_prompt = f"User asked: '{query}'\n\nI created an image for them: {comedy_response}\n\nNow give a short, funny response about creating this image while maintaining your comedy style. Mention that they can see the image in the UI."
                    else:
                        image_prompt = f"User asked: '{query}'\n\nI tried to create an image but: {comedy_response}\n\nNow give a short, funny response about this while maintaining your comedy style."
                    
                    stream = chat.send_message(image_prompt, stream=True)
                    print("--- Streaming LLM response with image generation ---")
                    full_response = ""
                    for chunk in stream:
                        if chunk.text:
                            print(chunk.text, end="", flush=True)
                            full_response += chunk.text
                else:
                    # Stream regular response without search
                    stream = chat.send_message(query, stream=True)
                    print("--- Streaming LLM response to Murf ---")
                    full_response = ""
                    for chunk in stream:
                        if chunk.text:
                            print(chunk.text, end="", flush=True)
                            full_response += chunk.text
                
                # Success
                break
            except ResourceExhausted as e:
                wait = (backoff_base ** attempt) + random.uniform(0, 1)
                print(f"⏳ Rate limited (429). Retrying in {wait:.1f}s... [attempt {attempt + 1}/{max_retries}]")
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"❌ Error streaming LLM response: {e}")
                break

        print("\n--- Sending to Murf WebSocket ---")
        print(f"📝 Full response length: {len(full_response)}")
        print(f"📝 Full response content: '{full_response}'")
        print(f"📝 Stripped response: '{full_response.strip()}'")

        if full_response.strip():
            # Send agent response text to client first
            if websocket:
                response_text_message = {
                    "type": "agent_response_text",
                    "text": full_response.strip(),
                    "timestamp": time.time()
                }
                await websocket.send_text(json.dumps(response_text_message))
                print(f"📤 Sent agent response text to client: '{full_response.strip()[:100]}...'")

            # Save to persistent chat history
            if session_id:
                chat_db.save_chat_turn(session_id, query, full_response.strip())
                print(f"💾 Saved chat turn to database for session: {session_id}")

            # Send the complete response to Murf WebSocket with Rohan's voice
            base64_audio = await send_to_murf_websocket(full_response.strip(), voice_id="en-IN-rohan")

            if base64_audio and websocket:
                print("✅ Successfully received base64 audio from Murf!")
                print(f"🔊 Base64 audio length: {len(base64_audio)}")

                # Day 21: Send audio data to client in chunks (base64-aligned)
                chunk_size = 1000 - (1000 % 4)  # Ensure chunk size is divisible by 4 for proper base64 alignment
                audio_chunks = [base64_audio[i:i+chunk_size] for i in range(0, len(base64_audio), chunk_size)]

                print(f"� [Day 21] Splitting audio into {len(audio_chunks)} chunks")

                for i, chunk in enumerate(audio_chunks):
                    chunk_message = {
                        "type": "audio_chunk",
                        "chunk_id": i + 1,
                        "data": chunk,
                        "timestamp": time.time()
                    }

                    # Send chunk to client with proper error handling
                    try:
                        if websocket_available and websocket:
                            await websocket.send_text(json.dumps(chunk_message))
                            print(f"📤 [Day 21] Sent audio chunk {i + 1}/{len(audio_chunks)} to client ({len(chunk)} chars)")
                        else:
                            print(f"⚠️ WebSocket unavailable, skipping chunk {i + 1}")
                    except Exception as e:
                        print(f"❌ Failed to send chunk {i + 1}: {e}")
                        websocket_available = False  # Mark as unavailable after error

                # Send completion message only if websocket is still connected
                try:
                    if websocket_available and websocket:
                        completion_message = {
                            "type": "audio_complete",
                            "total_chunks": len(audio_chunks),
                            "total_length": len(base64_audio),
                            "timestamp": time.time()
                        }
                        await websocket.send_text(json.dumps(completion_message))
                        print(f"🎉 [Day 21] Audio streaming to client complete!")
                except Exception as e:
                    print(f"❌ Failed to send completion message: {e}")

                return base64_audio
            else:
                print("❌ Failed to get audio from Murf or no WebSocket connection")
                return None
        else:
            print("⚠️ No content to send to Murf - response is empty after retries!")
            return None

    except Exception as e:
        print(f"❌ Error streaming LLM response to Murf and client: {e}")
        import traceback
        traceback.print_exc()
        return None
