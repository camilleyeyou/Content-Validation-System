import asyncio
import json
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import structlog
from ..config.config_manager import AppConfig

logger = structlog.get_logger()

class OpenAIClient:
    """Async OpenAI API client wrapper"""
    
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
        """Generate completion from OpenAI API"""
        
        model = model or self.config.openai.model
        temperature = temperature or self.config.openai.temperature
        max_tokens = max_tokens or self.config.openai.max_tokens
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            if response_format == "json":
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"}
                )
            else:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            content = response.choices[0].message.content
            
            # Parse JSON if expected
            if response_format == "json":
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse JSON response", 
                                      content=content[:200])
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
            
        except Exception as e:
            self.logger.error("OpenAI API error", error=str(e))
            raise

    async def close(self):
        """Close the client"""
        await self.client.close()
