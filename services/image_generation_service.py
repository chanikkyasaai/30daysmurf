import os
import logging
import requests
import base64
from typing import Optional, Dict
from PIL import Image
import io
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageGenerationService:
    def __init__(self):
        # Using FREE Hugging Face Inference API
        self.api_key = os.getenv("HUGGINGFACE_API_KEY")  # Optional - works without it too
        self.base_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
        logger.info("Free Hugging Face Image Generation service initialized")
    
    def is_available(self) -> bool:
        """Check if image generation is available"""
        return True  # Always available - it's FREE!
    
    async def generate_image(self, prompt: str) -> Optional[Dict]:
        """
        Generate image using FREE Hugging Face Stable Diffusion
        
        Args:
            prompt: Text description for image generation
            
        Returns:
            Dictionary with image data and metadata
        """
        try:
            logger.info(f"Generating FREE image for prompt: '{prompt}'")
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "num_inference_steps": 20,
                    "guidance_scale": 7.5,
                    "width": 1024,
                    "height": 1024
                }
            }
            
            # Make request to Hugging Face
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                # Save the image
                image_data = response.content
                filename = f"ravi_free_art_{int(time.time())}.png"
                
                # Create images directory if it doesn't exist
                os.makedirs("static/generated_images", exist_ok=True)
                filepath = f"static/generated_images/{filename}"
                
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"FREE image generated successfully: {filepath}")
                
                return {
                    'success': True,
                    'image_path': filepath,
                    'image_url': f"/static/generated_images/{filename}",
                    'original_prompt': prompt,
                    'model': 'Stable Diffusion XL (FREE)',
                    'cost': '₹0 - Completely FREE! 🎉'
                }
            elif response.status_code == 503:
                # Model is loading, wait and retry
                logger.info("Model is loading, waiting 20 seconds...")
                await self._wait_for_model_load()
                return await self.generate_image(prompt)  # Retry once
            else:
                logger.error(f"Error from Hugging Face API: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'API Error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Error generating FREE image: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _wait_for_model_load(self):
        """Wait for Hugging Face model to load"""
        import asyncio
        await asyncio.sleep(20)  # Wait 20 seconds for model to load
    
    def format_image_response_for_comedy(self, image_data: Dict, local_path: str = None) -> str:
        """
        Format image generation results in a comedic way for RAVI
        """
        if not image_data or not image_data.get('success'):
            error = image_data.get('error', 'Unknown error') if image_data else 'Unknown error'
            if 'loading' in error.lower() or '503' in error:
                return f"Arre yaar! My art studio is warming up... Give me 20 seconds and ask again, na? FREE art takes time! 😅"
            return f"Hawww! My FREE art machine broke down! Error: {error}. But hey, at least it didn't cost you anything! �"
        
        # Add comedy to successful image generation
        comedy_responses = [
            f"Hawww! FREE art by RAVI! Better than those expensive AI tools, I tell you! 🎨💸",
            f"Arre! Made you a masterpiece for ₹0! Even Picasso would be jealous of my FREE skills! 😄",
            f"Boss, FREE image ready! No payment needed - just my comedy guarantee! 🖼️",
            f"Good good! Zero rupees spent, but FULL quality art! I'm like a charitable artist, na? 😂",
            f"Seriously yaar, FREE Stable Diffusion is better than paying lakhs for art college! Check it out! 🎭"
        ]
        
        import random
        response = random.choice(comedy_responses)
        
        if local_path:
            response += f" Cost: ₹0 (FREE!) 🎉"
        
        return response

# Global instance
image_generation_service = ImageGenerationService()

async def generate_and_format_for_comedy(prompt: str) -> tuple[str, str]:
    """
    Convenience function to generate FREE image and format for comedian persona
    
    Returns:
        Tuple of (comedy_response, image_url_or_path)
    """
    # Enhance prompt for better results
    enhanced_prompt = f"{prompt}, high quality, detailed, beautiful, digital art"
    
    # Special enhancement for Ganesh Chaturthi
    if any(word in prompt.lower() for word in ['ganesh', 'ganesha', 'chaturthi', 'elephant', 'hindu']):
        enhanced_prompt = f"{prompt}, traditional Indian art style, colorful, festive, beautiful Lord Ganesha, digital painting"
    
    image_data = await image_generation_service.generate_image(enhanced_prompt)
    
    if image_data and image_data.get('success'):
        comedy_response = image_generation_service.format_image_response_for_comedy(image_data, image_data.get('image_path'))
        return comedy_response, image_data.get('image_url') or image_data.get('image_path')
    else:
        comedy_response = image_generation_service.format_image_response_for_comedy(image_data)
        return comedy_response, None
