"""
Contract Assistant vNext - CrewAI Agents

This module contains the Actor and Critic agents for contract processing using CrewAI framework.
Based on Agent-3.0 code style with legacy-derived system prompts.
"""

from crewai import Agent, LLM
import os
from dotenv import load_dotenv, find_dotenv
from bedrock_client import BedrockModelManager


class ContractAgents:
    def __init__(self):
        # Load environment variables from .env if present
        env_path = find_dotenv()
        if env_path:
            load_dotenv(env_path, override=True)

        # Get Bedrock model configuration
        self._actor_model = os.getenv("ACTOR_MODEL", "amazon.titan-text-premier-v1:0")
        self._critic_model = os.getenv("CRITIC_MODEL", "amazon.titan-text-premier-v1:0")
        
        # Initialize Bedrock manager for custom LLM integration
        self.bedrock_manager = BedrockModelManager()
        
        # Per-agent LLM runtime configuration following Agent-3.0 pattern
        # Using Bedrock models through CrewAI LLM interface
        self._actor_llm = LLM(
            model=self._actor_model,
            temperature=0.1,  # Low temperature for precise contract editing
            max_tokens=3000,  # Titan Premier max is 3072
        )
        self._critic_llm = LLM(
            model=self._critic_model,
            temperature=0.2,  # Slightly higher for evaluation flexibility
            max_tokens=2500,  # Conservative limit for Titan
        )

    def contract_actor(self):
        """
        Creates the Contract Actor Agent based on legacy system prompts.
        Handles semantic contract manipulations with chunking support.
        """
        return Agent(
            role="Contract Modification Specialist",
            goal="Apply semantic manipulations to legal contracts with precision, handling large documents through intelligent chunking",
            backstory=(
                "You are a precise contract editor with deep expertise in legal document modification. "
                "You specialize in semantic manipulations including counterparty changes, domicile shifts, "
                "liability reallocations, and clause operations while maintaining RTF formatting integrity. "
                "You have mastered the art of processing large contracts through intelligent chunking, "
                "ensuring context preservation across document boundaries."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self._actor_llm,
        )

    def contract_critic(self):
        """
        Creates the Contract Critic Agent based on experiment framework evaluation logic.
        Evaluates modification quality and provides structured feedback.
        """
        return Agent(
            role="Contract Quality Evaluator",
            goal="Evaluate contract modifications for accuracy and legal compliance with detailed scoring against acceptance criteria",
            backstory=(
                "You are a senior legal contract evaluator with expertise in quality assurance and "
                "semantic manipulation validation. Your mission is to ensure that all contract modifications "
                "meet stringent quality standards through systematic evaluation against five key criteria: "
                "entity substitution completeness, jurisdiction transformation accuracy, liability reallocation "
                "correctness, clause operations success, and legal coherence maintenance. You provide "
                "detailed feedback to guide refinement iterations toward the 0.85 quality threshold."
            ),
            verbose=True,
            allow_delegation=False,
            llm=self._critic_llm,
        )
