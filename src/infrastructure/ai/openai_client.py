"""
AI Client with OpenAI for text generation and Google Gemini for image generation
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from google import genai
from PIL import Image
from io import BytesIO
import structlog
from ..config.config_manager import AppConfig

logger = structlog.get_logger()

class OpenAIClient:
    """Async AI client wrapper with OpenAI (text) and Google Gemini (images)"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        
        # OpenAI client (for text generation)
        self.openai_client = AsyncOpenAI(api_key=config.openai.api_key)
        
        # Google Gemini client (for image generation)
        try:
            google_api_key = config.google.api_key
            self.gemini_client = genai.Client(api_key=google_api_key)
            self.gemini_image_model = config.google.image_model
            self.use_images = config.google.use_images
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini client: {e}")
            self.gemini_client = None
            self.use_images = False
        
        # Setup image output directory
        self.image_output_dir = Path("data/images")
        self.image_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger.bind(component="openai_client")
        
    async def generate(self, 
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      model: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: str = "json") -> Dict[str, Any]:
        """Generate completion from OpenAI API with JSON support"""
        
        model = model or self.config.openai.model
        temperature = temperature or self.config.openai.temperature
        max_tokens = max_tokens or self.config.openai.max_tokens
        
        messages = []
        
        # Add JSON instruction to system prompt
        if system_prompt:
            if response_format == "json":
                system_prompt += "\n\nIMPORTANT: You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."
            messages.append({"role": "system", "content": system_prompt})
        elif response_format == "json":
            # If no system prompt but JSON expected, add instruction
            messages.append({"role": "system", "content": "You MUST respond with valid JSON only. No additional text, no markdown formatting, no explanations - just pure, valid JSON."})
        
        # Add JSON reminder to user prompt
        if response_format == "json":
            prompt += "\n\nRemember: Respond ONLY with valid JSON. No other text."
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            # Build request kwargs
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            # Add response_format for compatible models
            if response_format == "json" and ("gpt-4" in model or "gpt-3.5-turbo" in model):
                kwargs["response_format"] = {"type": "json_object"}
            
            response = await self.openai_client.chat.completions.create(**kwargs)
            
            content = response.choices[0].message.content
            
            # Handle empty content
            if not content:
                self.logger.error("Received empty content from OpenAI")
                content = "{}" if response_format == "json" else ""
            
            # Try to parse JSON if expected
            if response_format == "json":
                try:
                    # Clean the content first
                    content = content.strip()
                    
                    # Remove markdown code blocks if present
                    if content.startswith("```json"):
                        content = content[7:]
                    elif content.startswith("```"):
                        content = content[3:]
                    
                    if content.endswith("```"):
                        content = content[:-3]
                    
                    content = content.strip()
                    
                    # Parse JSON
                    if content:
                        parsed_content = json.loads(content)
                    else:
                        self.logger.warning("Empty JSON content, returning empty dict")
                        parsed_content = {}
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse JSON response: {e}")
                    self.logger.debug(f"Raw content: {content[:500]}")
                    # Try to extract JSON from the content
                    parsed_content = self._extract_json_from_text(content)
                    if parsed_content is None:
                        parsed_content = {"error": "Failed to parse response", "raw_content": content}
            else:
                parsed_content = content
            
            return {
                "content": parsed_content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason if response.choices else "unknown"
            }
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    async def generate_image(self,
                           prompt: str,
                           base_image_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate image using Google Gemini 2.5 Flash Image
        
        Args:
            prompt: Detailed image description
            base_image_path: Optional path to base image for editing/remixing
            
        Returns:
            Dict with:
                - image_data: Raw image bytes
                - generation_time_seconds: Time taken to generate
                - size_mb: File size in megabytes
                
        Cost:
            - Gemini 2.5 Flash Image: $0.039 per image
        """
        
        if not self.use_images:
            self.logger.warning("Image generation disabled in config")
            return {"error": "Image generation disabled", "image_data": None}
        
        if not self.gemini_client:
            self.logger.error("Gemini client not initialized")
            return {"error": "Gemini client not available", "image_data": None}
        
        try:
            import time
            start_time = time.time()
            
            self.logger.info("Generating image with Gemini 2.5 Flash Image",
                           prompt_length=len(prompt),
                           has_base_image=base_image_path is not None)
            
            # Prepare contents for Gemini
            contents = [prompt]
            
            # Add base image if provided (for editing/remixing)
            if base_image_path and os.path.exists(base_image_path):
                try:
                    base_image = Image.open(base_image_path)
                    contents.append(base_image)
                    self.logger.info(f"Added base image: {base_image_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to load base image: {e}")
            
            # Generate image using Gemini
            response = self.gemini_client.models.generate_content(
                model=self.gemini_image_model,
                contents=contents,
            )
            
            # Extract image data from response
            image_data = None
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    break
            
            if not image_data:
                self.logger.error("No image data in Gemini response")
                return {"error": "No image generated", "image_data": None}
            
            # Calculate metrics
            generation_time = time.time() - start_time
            size_mb = len(image_data) / (1024 * 1024)
            
            result = {
                "image_data": image_data,
                "generation_time_seconds": round(generation_time, 2),
                "size_mb": round(size_mb, 3),
                "provider": "google_gemini",
                "model": self.gemini_image_model,
                "cost": 0.039
            }
            
            self.logger.info("Image generated successfully",
                           generation_time=result["generation_time_seconds"],
                           size_mb=result["size_mb"])
            
            return result
            
        except Exception as e:
            self.logger.error(f"Gemini image generation failed: {str(e)}", exc_info=True)
            return {
                "error": str(e),
                "image_data": None,
                "provider": "google_gemini",
                "model": self.gemini_image_model
            }
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict]:
        """Try to extract JSON from text that may contain other content"""
        # Look for JSON-like structures
        import re
        
        # Try to find JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    async def close(self):
        """Close the client"""
        await self.openai_client.close()