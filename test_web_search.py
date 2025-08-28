"""
Test script for web search functionality
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_web_search():
    """Test the web search service"""
    print("🧪 Testing Web Search Service...")
    
    # Import after loading environment
    from services.web_search_service import search_and_format_for_comedy
    
    # Test queries
    test_queries = [
        "latest news today",
        "current weather in Delhi",
        "what's happening in AI industry"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing query: '{query}'")
        try:
            result = await search_and_format_for_comedy(query)
            print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def test_llm_with_search():
    """Test LLM service with web search integration"""
    print("\n🤖 Testing LLM with Web Search...")
    
    from services.llm_service import query_llm
    
    # Test queries that should trigger web search
    test_queries = [
        "What's the latest news today?",
        "What's happening in the world?",
        "Tell me current weather updates"
    ]
    
    session_id = "test_session"
    
    for query in test_queries:
        print(f"\n📝 Testing LLM query: '{query}'")
        try:
            result = await query_llm(session_id, query)
            print(f"✅ RAVI says: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Web Search Tests...")
    
    # Check if Tavily API key is set
    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not found in environment variables!")
        print("Please add your Tavily API key to the .env file")
        print("You can get a free API key from: https://tavily.com/")
    else:
        print("✅ Tavily API key found!")
        asyncio.run(test_web_search())
        asyncio.run(test_llm_with_search())
