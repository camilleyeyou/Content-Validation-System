"""
OpenAI Client with proper JSON response handling
"""

import asyncio
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import structlog
from ..config.config_manager import AppConfig

logger = structlog.get_logger()

class OpenAIClient:
    """Async OpenAI API client wrapper with JSON support"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai.api_key)
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
            
            response = await self.client.chat.completions.create(**kwargs)
            
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
        await self.client.close()