"""
Base Agent - Foundation for all validation agents
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import structlog

logger = structlog.get_logger()


@dataclass
class AgentConfig:
    """Configuration for agents"""
    max_retries: int = 3
    timeout_seconds: int = 30
    log_level: str = "INFO"


class BaseAgent(ABC):
    """Base class for all agents in the system"""
    
    def __init__(self, name: str, config: AgentConfig, ai_client):
        self.name = name
        self.config = config
        self.ai_client = ai_client
        self.logger = logger.bind(agent=name)
        self._calls_made = 0
        self._total_tokens = 0
        
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input and return output - must be implemented by subclasses"""
        pass
    
    async def _call_ai(self, prompt: str, system_prompt: str = None, 
                      response_format: str = "json", **kwargs) -> Dict[str, Any]:
        """Call the AI client with retry logic"""
        self._calls_made += 1
        
        try:
            response = await self.ai_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                response_format=response_format,
                **kwargs
            )
            
            # Track token usage
            if "usage" in response:
                self._total_tokens += response["usage"].get("total_tokens", 0)
            
            return response
            
        except Exception as e:
            self.logger.error(f"AI call failed: {str(e)}")
            raise
    
    async def _generate_image(self, prompt: str, base_image_path: str = None) -> Dict[str, Any]:
        """Generate an image using the AI client"""
        try:
            return await self.ai_client.generate_image(
                prompt=prompt,
                base_image_path=base_image_path
            )
        except Exception as e:
            self.logger.error(f"Image generation failed: {str(e)}")
            raise
    
    def _ensure_json_dict(self, content: Any) -> Dict[str, Any]:
        """Ensure content is a dictionary, handling various formats"""
        if isinstance(content, dict):
            return content
        elif isinstance(content, str):
            try:
                import json
                return json.loads(content)
            except:
                return {"raw_content": content}
        elif content is None:
            return {}
        else:
            return {"content": str(content)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "agent_name": self.name,
            "calls_made": self._calls_made,
            "total_tokens": self._total_tokens
        }