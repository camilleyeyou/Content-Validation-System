"""
Modified OpenAI Client with Automatic Cost Tracking
Wraps the original client to track all API calls and costs
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import sys

# Add project root to path
CURRENT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = CURRENT_DIR.parent.parent if "portal" in str(CURRENT_DIR) else CURRENT_DIR.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cost_tracker import get_cost_tracker
import structlog

logger = structlog.get_logger(__name__)


class CostTrackedOpenAIClient:
    """
    Wrapper around OpenAI client that automatically tracks costs
    Drop-in replacement for the original client
    """
    
    def __init__(self, original_client, agent_name: str = "Unknown"):
        """
        Initialize with original client
        
        Args:
            original_client: The original OpenAIClient instance
            agent_name: Name of the agent using this client
        """
        self.client = original_client
        self.agent_name = agent_name
        self.cost_tracker = get_cost_tracker()
        self.logger = logger.bind(component="cost_tracked_client", agent=agent_name)
    
    async def generate(self,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      model: Optional[str] = None,
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      response_format: str = "json",
                      batch_id: Optional[str] = None,
                      post_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate completion with automatic cost tracking
        
        All parameters same as original, plus:
            batch_id: Optional batch ID for grouping
            post_number: Optional post number for grouping
        """
        
        # Call original method
        try:
            result = await self.client.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            
            # Extract usage data
            usage = result.get("usage", {})
            model_used = result.get("model", model or "gpt-4o-mini")
            
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)
            
            # Track the cost
            self.cost_tracker.track_api_call(
                agent_name=self.agent_name,
                model=model_used,
                provider="openai",
                call_type="text_generation",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                batch_id=batch_id,
                post_number=post_number,
                success=True
            )
            
            return result
            
        except Exception as e:
            # Track failed call
            self.cost_tracker.track_api_call(
                agent_name=self.agent_name,
                model=model or "gpt-4o-mini",
                provider="openai",
                call_type="text_generation",
                success=False,
                error_message=str(e)
            )
            raise
    
    async def generate_image(self,
                           prompt: str,
                           base_image_path: Optional[str] = None,
                           batch_id: Optional[str] = None,
                           post_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate image with automatic cost tracking
        
        All parameters same as original, plus:
            batch_id: Optional batch ID for grouping
            post_number: Optional post number for grouping
        """
        
        import time
        start_time = time.time()
        
        try:
            result = await self.client.generate_image(
                prompt=prompt,
                base_image_path=base_image_path
            )
            
            generation_time = time.time() - start_time
            
            # Check if generation succeeded
            if result.get("image_data"):
                # Track successful image generation
                model = result.get("model", "gemini-2.5-flash-image")
                
                self.cost_tracker.track_api_call(
                    agent_name=self.agent_name,
                    model=model,
                    provider="google",
                    call_type="image_generation",
                    image_count=1,
                    batch_id=batch_id,
                    post_number=post_number,
                    generation_time=generation_time,
                    success=True
                )
            else:
                # Track failed image generation
                self.cost_tracker.track_api_call(
                    agent_name=self.agent_name,
                    model="gemini-2.5-flash-image",
                    provider="google",
                    call_type="image_generation",
                    success=False,
                    error_message=result.get("error", "Unknown error")
                )
            
            return result
            
        except Exception as e:
            # Track exception
            self.cost_tracker.track_api_call(
                agent_name=self.agent_name,
                model="gemini-2.5-flash-image",
                provider="google",
                call_type="image_generation",
                success=False,
                error_message=str(e)
            )
            raise
    
    async def close(self):
        """Close the underlying client"""
        await self.client.close()


def wrap_client_with_cost_tracking(original_client, agent_name: str) -> CostTrackedOpenAIClient:
    """
    Wrap an existing OpenAI client with cost tracking
    
    Usage:
        original_client = OpenAIClient(config)
        tracked_client = wrap_client_with_cost_tracking(original_client, "AdvancedContentGenerator")
        
        # Now use tracked_client exactly like original_client
        result = await tracked_client.generate(prompt="...", batch_id="batch1", post_number=1)
    
    Args:
        original_client: The original OpenAIClient instance
        agent_name: Name of the agent (for tracking purposes)
    
    Returns:
        CostTrackedOpenAIClient that tracks all costs automatically
    """
    return CostTrackedOpenAIClient(original_client, agent_name)