"""
Test script for image generation functionality - Day 26
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_image_generation():
    """Test the FREE image generation service"""
    print("🎨 Testing FREE Image Generation Service...")
    
    # Import after loading environment
    from services.image_generation_service import generate_and_format_for_comedy
    
    # Test queries for Ganesh Chaturthi and general image generation
    test_queries = [
        "create an image of Lord Ganesha for Ganesh Chaturthi",
        "draw a beautiful sunset over mountains",
        "generate a funny cartoon cat",
        "paint a traditional Indian festival scene"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing FREE image query: '{query}'")
        try:
            comedy_response, image_path = await generate_and_format_for_comedy(query)
            print(f"✅ RAVI says: {comedy_response}")
            if image_path:
                print(f"🖼️ FREE Image saved at: {image_path}")
            else:
                print("⏳ Image might be loading - try again in 20 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_llm_with_image_generation():
    """Test LLM service with image generation integration"""
    print("\n🤖 Testing LLM with Image Generation...")
    
    from services.llm_service import query_llm
    
    # Test queries that should trigger image generation
    test_queries = [
        "create an image of Ganesha",
        "draw me a beautiful landscape",
        "show me what a robot looks like",
        "generate art of a peaceful garden"
    ]
    
    session_id = "test_image_session"
    
    for query in test_queries:
        print(f"\n📝 Testing LLM image query: '{query}'")
        try:
            result = await query_llm(session_id, query)
            print(f"✅ RAVI says: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_dual_skills():
    """Test both web search and image generation together"""
    print("\n🚀 Testing Dual Skills (Search + Image)...")
    
    from services.llm_service import query_llm
    
    session_id = "test_dual_skills"
    
    # Test web search
    print("\n1️⃣ Testing Web Search:")
    search_result = await query_llm(session_id, "What's the latest news about Ganesh Chaturthi?")
    print(f"🔍 Search Result: {search_result}")
    
    # Test image generation  
    print("\n2️⃣ Testing Image Generation:")
    image_result = await query_llm(session_id, "Create an image celebrating Ganesh Chaturthi")
    print(f"🎨 Image Result: {image_result}")

if __name__ == "__main__":
    print("🚀 Starting Day 26 - Dual Skills Tests...")
    print("🎨 Using FREE Hugging Face Stable Diffusion!")
    print("💰 Cost: ₹0 - Completely FREE image generation!")
    
    # Check if Tavily API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not found in environment variables!")
        print("Web search will not work")
    else:
        print("✅ Tavily API key found!")
        
    # Hugging Face is optional - works without API key
    if os.getenv("HUGGINGFACE_API_KEY"):
        print("✅ Hugging Face API key found - faster generation!")
    else:
        print("ℹ️ No Hugging Face API key - using FREE public models (slower but works!)")
        
    # Run tests - image generation is always available (FREE!)
    asyncio.run(test_image_generation())
    asyncio.run(test_llm_with_image_generation())
    
    if os.getenv("TAVILY_API_KEY"):
        asyncio.run(test_dual_skills())
