#!/usr/bin/env python3
"""
Quick test script for RAVI the comedian persona
"""

import asyncio
import requests
import json

def test_comedian_llm():
    """Test the comedian LLM response"""
    print("🎭 Testing RAVI the Comedian LLM...")
    
    try:
        from services.llm_service import query_llm
        
        # Test queries
        test_queries = [
            "Hello, who are you?",
            "Tell me a joke about programming",
            "What's the weather like?",
            "Can you help me with my work?"
        ]
        
        session_id = "test_comedian_session"
        
        for query in test_queries:
            print(f"\n👤 User: {query}")
            response = query_llm(session_id, query)
            print(f"🎭 RAVI: {response}")
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Error testing comedian LLM: {e}")

def test_comedian_voice():
    """Test the comedian voice synthesis"""
    print("\n🎙️ Testing RAVI's Voice...")
    
    try:
        from services.tts_service import generate_comedian_tts_audio
        
        test_text = "Arre yaar! I'm RAVI, your comedy AI assistant! Ready to make you laugh while solving your problems. What's up, boss?"
        
        print(f"🔊 Generating audio for: {test_text[:50]}...")
        audio_url = generate_comedian_tts_audio(test_text)
        print(f"✅ Audio generated successfully: {audio_url}")
        
    except Exception as e:
        print(f"❌ Error testing comedian voice: {e}")

def test_api_endpoint():
    """Test the API endpoint"""
    print("\n🌐 Testing API endpoint...")
    
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Server is running and responding")
            if "RAVI" in response.text:
                print("✅ RAVI persona is loaded in UI")
            else:
                print("⚠️ RAVI persona not found in UI")
        else:
            print(f"❌ Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    print("🎭 Welcome to RAVI Comedian Voice Agent Test!")
    print("=" * 60)
    
    # Test LLM
    test_comedian_llm()
    
    # Test Voice
    test_comedian_voice()
    
    # Test API
    test_api_endpoint()
    
    print("\n🎉 Testing complete!")
