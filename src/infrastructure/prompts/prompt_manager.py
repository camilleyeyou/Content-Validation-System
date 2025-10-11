# src/infrastructure/prompts/prompt_manager.py
"""
Prompt Management System - Allows runtime prompt customization without code changes
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()

class PromptManager:
    """Manages custom prompt overrides for agents"""
    
    def __init__(self, prompts_file: str = "config/prompts.json"):
        self.prompts_file = Path(prompts_file)
        self._ensure_prompts_file()
        self._prompts: Dict[str, Dict[str, str]] = self._load_prompts()
    
    def _ensure_prompts_file(self):
        """Create prompts file if it doesn't exist"""
        if not self.prompts_file.exists():
            self.prompts_file.parent.mkdir(parents=True, exist_ok=True)
            self.prompts_file.write_text("{}")
            logger.info("Created prompts file", path=str(self.prompts_file))
    
    def _load_prompts(self) -> Dict[str, Dict[str, str]]:
        """Load prompts from JSON file"""
        try:
            with open(self.prompts_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load prompts", error=str(e))
            return {}
    
    def _save_prompts(self):
        """Save prompts to JSON file"""
        try:
            with open(self.prompts_file, 'w') as f:
                json.dump(self._prompts, f, indent=2)
            logger.info("Saved prompts", path=str(self.prompts_file))
        except Exception as e:
            logger.error("Failed to save prompts", error=str(e))
            raise
    
    def get_agent_prompts(self, agent_name: str) -> Dict[str, Optional[str]]:
        """Get custom prompts for an agent (returns None if using defaults)"""
        return self._prompts.get(agent_name, {})
    
    def set_agent_prompts(self, agent_name: str, prompts: Dict[str, str]) -> bool:
        """Set custom prompts for an agent"""
        try:
            # Validate prompt keys
            valid_keys = {"system_prompt", "user_prompt_template"}
            if not all(key in valid_keys for key in prompts.keys()):
                raise ValueError(f"Invalid prompt keys. Must be in {valid_keys}")
            
            self._prompts[agent_name] = prompts
            self._save_prompts()
            logger.info("Set custom prompts", agent=agent_name)
            return True
        except Exception as e:
            logger.error("Failed to set prompts", agent=agent_name, error=str(e))
            raise
    
    def reset_agent_prompts(self, agent_name: str) -> bool:
        """Reset agent to use default prompts"""
        if agent_name in self._prompts:
            del self._prompts[agent_name]
            self._save_prompts()
            logger.info("Reset to default prompts", agent=agent_name)
            return True
        return False
    
    def has_custom_prompts(self, agent_name: str) -> bool:
        """Check if agent has custom prompts"""
        return agent_name in self._prompts and bool(self._prompts[agent_name])
    
    def list_agents_with_custom_prompts(self) -> List[str]:
        """List all agents with custom prompts"""
        return list(self._prompts.keys())
    
    def get_all_prompts(self) -> Dict[str, Dict[str, str]]:
        """Get all custom prompts"""
        return self._prompts.copy()


# Singleton instance
_prompt_manager: Optional[PromptManager] = None

def get_prompt_manager() -> PromptManager:
    """Get or create the global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager