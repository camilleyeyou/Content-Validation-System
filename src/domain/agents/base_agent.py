# src/domain/agents/base_agent.py
"""
Base Agent with improved JSON response handling and custom prompt support
MODIFY your existing base_agent.py to add the prompt loading functionality
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol
import asyncio
import time
from dataclasses import dataclass
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

class AIClientProtocol(Protocol):
    """Protocol for AI client implementations"""
    async def generate(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      response_format: str = "json",
                      **kwargs) -> Dict[str, Any]:
        ...

@dataclass
class AgentConfig:
    """Configuration for AI agents"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 600
    retry_attempts: int = 3
    timeout: int = 30
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

class BaseAgent(ABC):
    """Abstract base class for all AI agents with improved error handling and custom prompts"""
    
    def __init__(self, 
                 name: str,
                 config: AgentConfig, 
                 ai_client: AIClientProtocol):
        self.name = name
        self.config = config
        self.ai_client = ai_client
        self.logger = logger.bind(agent=name)
        self._call_count = 0
        self._total_tokens = 0
        
        # NEW: Load custom prompts if available
        self._custom_prompts = self._load_custom_prompts()
        
    def _load_custom_prompts(self) -> Dict[str, str]:
        """Load custom prompts for this agent if they exist"""
        try:
            from src.infrastructure.prompts.prompt_manager import get_prompt_manager
            prompt_manager = get_prompt_manager()
            custom = prompt_manager.get_agent_prompts(self.name)
            if custom:
                self.logger.info("Loaded custom prompts", agent=self.name)
            return custom
        except Exception as e:
            self.logger.warning("Could not load custom prompts", error=str(e))
            return {}
    
    def _get_system_prompt(self, default_prompt: str) -> str:
        """Get system prompt - custom if available, otherwise default"""
        if "system_prompt" in self._custom_prompts:
            self.logger.debug("Using custom system prompt")
            return self._custom_prompts["system_prompt"]
        return default_prompt
    
    def _get_user_prompt_template(self, default_template: str) -> str:
        """Get user prompt template - custom if available, otherwise default"""
        if "user_prompt_template" in self._custom_prompts:
            self.logger.debug("Using custom user prompt template")
            return self._custom_prompts["user_prompt_template"]
        return default_template
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input and return result"""
        pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _call_ai(self, 
                       prompt: str, 
                       system_prompt: Optional[str] = None,
                       response_format: str = "json") -> Dict[str, Any]:
        """Make AI call with retry logic, monitoring, and JSON validation"""
        start_time = time.time()
        self._call_count += 1
        
        try:
            self.logger.info("ai_call_started", 
                           call_number=self._call_count,
                           prompt_length=len(prompt),
                           response_format=response_format)
            
            response = await self.ai_client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                response_format=response_format
            )
            
            # Validate response
            if not response:
                raise ValueError("Received null response from AI client")
            
            if not response.get("content"):
                raise ValueError("Response missing content field")
            
            # For JSON responses, ensure we got valid JSON
            if response_format == "json":
                content = response.get("content")
                if isinstance(content, str):
                    self.logger.warning("Received string instead of parsed JSON")
                    import json
                    try:
                        response["content"] = json.loads(content)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse JSON content: {e}")
                        raise ValueError(f"Invalid JSON response: {e}")
                elif not isinstance(content, dict):
                    raise ValueError(f"Expected dict for JSON response, got {type(content)}")
            
            elapsed = time.time() - start_time
            tokens_used = response.get('usage', {}).get('total_tokens', 0)
            self._total_tokens += tokens_used
            
            self.logger.info("ai_call_completed",
                           duration=elapsed,
                           tokens_used=tokens_used,
                           total_tokens=self._total_tokens,
                           response_format=response_format)
            
            return response
            
        except Exception as e:
            self.logger.error("ai_call_failed",
                            error=str(e),
                            call_number=self._call_count,
                            response_format=response_format)
            raise
    
    def _ensure_json_dict(self, content: Any) -> Dict:
        """Ensure content is a dictionary, parsing if necessary"""
        if isinstance(content, dict):
            return content
        elif isinstance(content, str):
            import json
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON string: {e}")
                return {}
        else:
            self.logger.error(f"Unexpected content type: {type(content)}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "call_count": self._call_count,
            "total_tokens": self._total_tokens,
            "estimated_cost": self._estimate_cost(),
            "using_custom_prompts": bool(self._custom_prompts)
        }
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on tokens used"""
        input_price_per_1k = 0.00015
        output_price_per_1k = 0.0006
        
        input_tokens = self._total_tokens * 0.7
        output_tokens = self._total_tokens * 0.3
        
        cost = (input_tokens / 1000 * input_price_per_1k + 
                output_tokens / 1000 * output_price_per_1k)
        
        if self._total_tokens > 0 and cost == 0:
            cost = 0.0001
        
        return round(cost, 6)