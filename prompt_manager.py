"""
Prompt Manager for Contract Assistant vNext.

This module provides a centralized way to manage system prompts with configuration support,
template loading, and dynamic prompt generation based on legacy patterns.
"""

import json
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from system_prompts import SystemPrompts


@dataclass
class PromptConfig:
    """Configuration for prompt generation."""
    max_chunk_size: int = 25000
    chunk_overlap: int = 5000
    quality_threshold: float = 0.85
    max_iterations: int = 5
    chunking_enabled: bool = True
    minimum_score: float = 0.85
    primary_model: str = "amazon.titan-text-premier-v1:0"
    fallback_model: str = "mistral.mistral-large-2402-v1:0"


class PromptManager:
    """
    Manages system prompts with configuration support and template loading.
    Provides centralized access to Actor and Critic prompts with variable substitution.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the PromptManager with optional configuration file.
        
        Args:
            config_path: Path to JSON configuration file. If None, uses default config.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.prompt_config = self._create_prompt_config()
        
    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, 'config', 'prompt_config.json')
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in config file: {e}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails."""
        return {
            "prompt_settings": {
                "actor": {
                    "max_chunk_size": 25000,
                    "chunk_overlap": 5000,
                    "quality_threshold": 0.85,
                    "max_iterations": 5,
                    "chunking_enabled": True
                },
                "critic": {
                    "minimum_score": 0.85
                }
            },
            "model_settings": {
                "primary_model": "amazon.titan-text-premier-v1:0",
                "fallback_model": "mistral.mistral-large-2402-v1:0"
            }
        }
    
    def _create_prompt_config(self) -> PromptConfig:
        """Create PromptConfig from loaded configuration."""
        actor_settings = self.config.get("prompt_settings", {}).get("actor", {})
        critic_settings = self.config.get("prompt_settings", {}).get("critic", {})
        model_settings = self.config.get("model_settings", {})
        
        return PromptConfig(
            max_chunk_size=actor_settings.get("max_chunk_size", 25000),
            chunk_overlap=actor_settings.get("chunk_overlap", 5000),
            quality_threshold=actor_settings.get("quality_threshold", 0.85),
            max_iterations=actor_settings.get("max_iterations", 5),
            chunking_enabled=actor_settings.get("chunking_enabled", True),
            minimum_score=critic_settings.get("minimum_score", 0.85),
            primary_model=model_settings.get("primary_model", "amazon.titan-text-premier-v1:0"),
            fallback_model=model_settings.get("fallback_model", "mistral.mistral-large-2402-v1:0")
        )
    
    def get_actor_prompt(self, chunk_id: Optional[int] = None, total_chunks: Optional[int] = None) -> str:
        """
        Get Actor system prompt with optional chunking context.
        
        Args:
            chunk_id: Current chunk number for chunked processing
            total_chunks: Total number of chunks for chunked processing
            
        Returns:
            Complete Actor system prompt
        """
        if not self.prompt_config.chunking_enabled:
            chunk_id = None
            total_chunks = None
            
        return SystemPrompts.get_actor_prompt(chunk_id, total_chunks)
    
    def get_critic_prompt(self) -> str:
        """
        Get Critic system prompt.
        
        Returns:
            Complete Critic system prompt
        """
        return SystemPrompts.get_critic_prompt()
    
    def create_actor_task(
        self, 
        original_rtf: str, 
        user_prompt: str, 
        chunk_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create Actor task description with configuration-aware chunking.
        
        Args:
            original_rtf: Original contract content
            user_prompt: User's modification instructions
            chunk_info: Optional chunking information
            
        Returns:
            Complete Actor task description
        """
        # Apply chunking configuration
        if chunk_info and not self.prompt_config.chunking_enabled:
            chunk_info = None
            
        return SystemPrompts.create_actor_task_description(original_rtf, user_prompt, chunk_info)
    
    def create_critic_task(
        self, 
        original_rtf: str, 
        modified_rtf: str, 
        user_prompt: str, 
        attempt_number: int = 1
    ) -> str:
        """
        Create Critic task description.
        
        Args:
            original_rtf: Original contract content
            modified_rtf: Modified contract content to evaluate
            user_prompt: Original user instructions
            attempt_number: Current iteration attempt number
            
        Returns:
            Complete Critic task description
        """
        return SystemPrompts.create_critic_task_description(
            original_rtf, modified_rtf, user_prompt, attempt_number
        )
    
    def should_chunk_document(self, document_content: str) -> bool:
        """
        Determine if document should be chunked based on configuration.
        
        Args:
            document_content: Document content to check
            
        Returns:
            True if document should be chunked
        """
        if not self.prompt_config.chunking_enabled:
            return False
            
        return len(document_content) >= self.prompt_config.max_chunk_size
    
    def get_evaluation_criteria(self) -> Dict[str, Any]:
        """
        Get evaluation criteria configuration for Critic agent.
        
        Returns:
            Dictionary of evaluation criteria with weights
        """
        return self.config.get("prompt_settings", {}).get("critic", {}).get("evaluation_criteria", {})
    
    def get_legacy_patterns(self) -> Dict[str, Any]:
        """
        Get legacy pattern definitions for reference.
        
        Returns:
            Dictionary of legacy patterns with requirements
        """
        return self.config.get("legacy_patterns", {})
    
    def get_test_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get test scenarios for prompt validation.
        
        Returns:
            List of test scenario configurations
        """
        return self.config.get("test_scenarios", [])
    
    def validate_prompt_effectiveness(self, sample_rtf: str) -> Dict[str, bool]:
        """
        Validate prompt effectiveness with sample content.
        
        Args:
            sample_rtf: Sample RTF content for testing
            
        Returns:
            Dictionary of validation results
        """
        results = {}
        
        try:
            # Test Actor prompt generation
            actor_prompt = self.get_actor_prompt()
            results["actor_prompt_generation"] = len(actor_prompt) > 1000
            
            # Test Actor prompt with chunking
            chunked_prompt = self.get_actor_prompt(chunk_id=1, total_chunks=3)
            results["actor_chunking_support"] = "chunk 1 of 3" in chunked_prompt
            
            # Test Critic prompt generation
            critic_prompt = self.get_critic_prompt()
            results["critic_prompt_generation"] = len(critic_prompt) > 1000
            
            # Test task creation
            actor_task = self.create_actor_task(sample_rtf, "Test instruction")
            results["actor_task_creation"] = len(actor_task) > 500
            
            critic_task = self.create_critic_task(sample_rtf, sample_rtf, "Test instruction")
            results["critic_task_creation"] = len(critic_task) > 500
            
            # Test configuration loading
            results["config_loading"] = self.prompt_config.quality_threshold > 0
            
            # Test chunking decision
            results["chunking_logic"] = isinstance(self.should_chunk_document(sample_rtf), bool)
            
        except Exception as e:
            print(f"Validation error: {e}")
            results["validation_error"] = str(e)
        
        return results
    
    def get_model_config(self) -> Dict[str, Any]:
        """
        Get model configuration settings.
        
        Returns:
            Dictionary of model settings
        """
        return self.config.get("model_settings", {})
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration and reload settings.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)
        self.prompt_config = self._create_prompt_config()
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            output_path: Path to save configuration. If None, uses current config path.
        """
        save_path = output_path or self.config_path
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            print(f"Configuration saved to {save_path}")
        except Exception as e:
            print(f"Error saving configuration: {e}")


def test_prompt_manager():
    """Test the PromptManager functionality."""
    print("Testing PromptManager...")
    
    # Initialize manager
    manager = PromptManager()
    
    # Test basic functionality
    actor_prompt = manager.get_actor_prompt()
    assert len(actor_prompt) > 1000, "Actor prompt too short"
    
    critic_prompt = manager.get_critic_prompt()
    assert len(critic_prompt) > 1000, "Critic prompt too short"
    
    # Test chunking
    chunked_prompt = manager.get_actor_prompt(chunk_id=2, total_chunks=5)
    assert "chunk 2 of 5" in chunked_prompt, "Chunking context missing"
    
    # Test task creation
    sample_rtf = "Sample RTF content"
    actor_task = manager.create_actor_task(sample_rtf, "Test instruction")
    assert len(actor_task) > 100, "Actor task too short"
    
    critic_task = manager.create_critic_task(sample_rtf, sample_rtf, "Test instruction")
    assert len(critic_task) > 100, "Critic task too short"
    
    # Test configuration access
    criteria = manager.get_evaluation_criteria()
    patterns = manager.get_legacy_patterns()
    scenarios = manager.get_test_scenarios()
    
    print("✓ PromptManager tests passed!")
    
    # Test validation
    validation_results = manager.validate_prompt_effectiveness(sample_rtf)
    print(f"✓ Validation results: {validation_results}")
    
    return manager


if __name__ == "__main__":
    test_prompt_manager()