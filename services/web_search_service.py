import os
import logging
from typing import Dict, List, Optional
from tavily import TavilyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_runtime_api_key() -> str:
    """Get Tavily API key from runtime storage only, NO fallback to environment."""
    try:
        # Import here to avoid circular imports
        from main import runtime_api_keys
        return runtime_api_keys.get('tavily', '')
    except:
        return ''

class WebSearchService:
    def __init__(self):
        # Don't initialize with env variable anymore
        self.client = None
        logger.info("WebSearch service initialized (client will be created per request)")
    
    def is_available(self) -> bool:
        """Check if web search is available"""
        api_key = get_runtime_api_key()
        return bool(api_key)
    
    async def search_web(self, query: str, max_results: int = 3) -> Optional[Dict]:
        """
        Search the web using Tavily API
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Search results with title, content, and URL
        """
        # Get API key from runtime storage only
        api_key = get_runtime_api_key()
        if not api_key:
            logger.error("Web search is not available - Tavily API key not configured in user settings")
            return None
        
        # Create client with runtime API key
        client = TavilyClient(api_key=api_key)
            
        try:
            logger.info(f"Searching web for: '{query}'")
            
            # Use Tavily's search method
            response = client.search(
                query=query,
                search_depth="basic",  # Can be "basic" or "advanced"
                max_results=max_results,
                include_answer=True,  # Get a direct answer if possible
                include_images=False,  # We don't need images for voice
                include_raw_content=False  # Keep it concise
            )
            
            if response and 'results' in response:
                logger.info(f"Found {len(response['results'])} search results")
                return {
                    'success': True,
                    'query': query,
                    'answer': response.get('answer', ''),  # Direct answer from Tavily
                    'results': response['results'][:max_results],
                    'total_results': len(response['results'])
                }
            else:
                logger.warning("No results found")
                return {
                    'success': False,
                    'query': query,
                    'error': 'No results found'
                }
                
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return {
                'success': False,
                'query': query,
                'error': str(e)
            }
    
    def format_search_results_for_comedy(self, search_data: Dict) -> str:
        """
        Format search results in a comedic way for RAVI the comedian
        """
        if not search_data or not search_data.get('success'):
            return "Arre yaar! Google se bhi puch kar aata hun... but kuch nahi mila! Maybe try asking your neighbor uncle? 😅"
        
        # Use the direct answer if available
        if search_data.get('answer'):
            answer = search_data['answer']
            # Keep it short and add comedy
            if len(answer) > 100:
                answer = answer[:100] + "..."
            return f"Bosss! Here's what I found: {answer} ...bas yaar, enough Google gyan! 😄"
        
        # Format results
        results = search_data.get('results', [])
        if not results:
            return "Hawww! Even Google is confused today. Try again later, na? 🤔"
        
        # Take first result and make it funny
        first_result = results[0]
        content = first_result.get('content', '')[:80] + "..." if len(first_result.get('content', '')) > 80 else first_result.get('content', '')
        
        return f"Arre! Found something: {content} Source: {first_result.get('url', 'Internet ki dukaan')} 😂"

# Global instance
web_search_service = WebSearchService()

async def search_and_format_for_comedy(query: str) -> str:
    """
    Convenience function to search web and format for comedian persona
    """
    if not web_search_service.is_available():
        return "Arre yaar! My internet search is broken today. Ask me something else, na? 🤷‍♂️"
    
    search_results = await web_search_service.search_web(query)
    return web_search_service.format_search_results_for_comedy(search_results)
