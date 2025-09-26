"""
Base Agent with improved JSON response handling
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
    """Abstract base class for all AI agents with improved error handling"""
    
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
                response_format=response_format  # Pass response format
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
                    # This shouldn't happen if OpenAIClient works correctly
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
            "estimated_cost": self._estimate_cost()
        }
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on tokens used"""
        # GPT-4o-mini pricing (as of knowledge cutoff)
        input_price_per_1k = 0.00015
        output_price_per_1k = 0.0006
        
        # Rough estimate (assuming 70% input, 30% output)
        input_tokens = self._total_tokens * 0.7
        output_tokens = self._total_tokens * 0.3
        
        cost = (input_tokens / 1000 * input_price_per_1k + 
                output_tokens / 1000 * output_price_per_1k)
        
        # Ensure we return at least a minimal cost if tokens were used
        if self._total_tokens > 0 and cost == 0:
            cost = 0.0001  # Minimum cost
        
        return round(cost, 6)