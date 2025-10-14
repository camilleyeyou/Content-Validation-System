# src/infrastructure/ai/gemini_client.py

import os
import logging
from typing import Optional
from google import genai
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class GeminiImageClient:
    """Client for Google Gemini 2.5 Flash Image generation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini client"""
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        
        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.5-flash-image"
        
        logger.info("GeminiImageClient initialized")
    
    def generate_image(
        self,
        prompt: str,
        base_image_path: Optional[str] = None
    ) -> bytes:
        """
        Generate image using Gemini 2.5 Flash Image
        
        Args:
            prompt: Text description of image to generate
            base_image_path: Optional path to base image for editing
            
        Returns:
            Image data as bytes
        """
        
        logger.info(f"Generating image with prompt length: {len(prompt)}")
        
        try:
            contents = [prompt]
            
            # Optional: Include base image for editing/remixing
            if base_image_path:
                logger.info(f"Using base image: {base_image_path}")
                base_image = Image.open(base_image_path)
                contents.append(base_image)
            
            # Generate image
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
            )
            
            # Extract image bytes from response
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    logger.info("Image generated successfully")
                    return part.inline_data.data
            
            logger.error("No image data in response")
            return None
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    def save_image(self, image_data: bytes, output_path: str) -> str:
        """Save image bytes to file"""
        
        try:
            image = Image.open(BytesIO(image_data))
            image.save(output_path)
            logger.info(f"Image saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise