"""
Contract Assistant vNext - CrewAI Tasks

This module contains the task definitions for contract processing workflow.
Based on Agent-3.0 code style with contract-specific requirements.
"""

from crewai import Task
from .agents import ContractAgents
from core.prompts.system_prompts import SystemPrompts
import json


class ContractTasks:
    def __init__(self):
        self.agents = ContractAgents()
        self.system_prompts = SystemPrompts()
        # Tools will be injected from crew_manager for flexibility
        self.document_chunking = None  # Will be set by crew_manager
        self.bedrock_manager = None   # Will be set by crew_manager

    def contract_modification_task(self, context):
        """
        Task for Actor agent to modify contract according to user instructions.
        Handles both single-chunk and multi-chunk processing.
        """
        original_rtf = context.get('original_rtf', '')
        user_prompt = context.get('user_prompt', '')
        chunk_id = context.get('chunk_id', None)
        total_chunks = context.get('total_chunks', None)
        
        # Generate appropriate system prompt for chunking context
        if chunk_id is not None and total_chunks is not None:
            actor_prompt = self.system_prompts.get_actor_prompt(chunk_id, total_chunks)
            chunk_context = f"Processing chunk {chunk_id} of {total_chunks}."
        else:
            actor_prompt = self.system_prompts.get_actor_prompt()
            chunk_context = "Processing complete document."
        
        task = Task(
            description=f"""
            Apply the following semantic manipulations to the contract document:
            
            USER INSTRUCTIONS: {user_prompt}
            
            {chunk_context}
            
            DOCUMENT TO MODIFY (RTF format):
            {original_rtf}
            
            CRITICAL REQUIREMENTS:
            1. Make ALL changes requested in the user's instructions - this is CRITICAL
            2. Maintain the EXACT RTF structure and formatting of the original document
            3. ONLY modify the text content within RTF elements as specified in instructions
            4. NEVER add, remove, or modify RTF tags, attributes, or structure
            5. Preserve ALL formatting elements: headings, paragraphs, styling, spacing
            6. If processing a chunk, return the FULL modified text for this chunk only
            7. If no changes are needed for this chunk, return it exactly as provided
            
            SEMANTIC MANIPULATION FOCUS:
            - Counterparty name changes (replace all entity references)
            - Legal domicile shifts (governing law, jurisdiction, venue changes)
            - Liability reallocation (shift responsibility between parties)
            - Clause operations (add, delete, modify specific clauses)
            
            System Prompt Context: {actor_prompt[:200]}...
            """,
            expected_output="""
            Complete RTF document (or chunk) with all requested modifications applied.
            Maintain exact RTF formatting and structure while implementing the semantic changes.
            Return only the modified RTF content without additional commentary.
            """,
            agent=self.agents.contract_actor(),
        )
        return task

    def contract_evaluation_task(self, context):
        """
        Task for Critic agent to evaluate contract modifications against quality criteria.
        Provides structured scoring and feedback for refinement.
        """
        original_rtf = context.get('original_rtf', '')
        modified_rtf = context.get('modified_rtf', '')
        user_prompt = context.get('user_prompt', '')
        attempt_number = context.get('attempt_number', 1)
        
        # Load evaluation criteria from config
        config_path = context.get('config_path', 'config/prompt_config.json')
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            criteria = config['prompt_settings']['critic']['evaluation_criteria']
            minimum_score = config['prompt_settings']['critic']['minimum_score']
        except Exception as e:
            # Fallback criteria if config loading fails
            criteria = {
                "entity_substitution": {"weight": 0.25},
                "jurisdiction_transformation": {"weight": 0.20},
                "liability_reallocation": {"weight": 0.20},
                "clause_operations": {"weight": 0.20},
                "legal_coherence": {"weight": 0.15}
            }
            minimum_score = 0.85
        
        critic_prompt = self.system_prompts.get_critic_prompt()
        
        task = Task(
            description=f"""
            Evaluate the quality of contract modifications against acceptance criteria:
            
            ORIGINAL CONTRACT (First 1000 chars): {original_rtf[:1000]}...
            
            MODIFIED CONTRACT (First 1000 chars): {modified_rtf[:1000]}...
            
            USER REQUIREMENTS: {user_prompt}
            
            ATTEMPT NUMBER: {attempt_number}
            
            EVALUATION CRITERIA (with weights):
            {json.dumps(criteria, indent=2)}
            
            MINIMUM ACCEPTABLE SCORE: {minimum_score}
            
            EVALUATION INSTRUCTIONS:
            1. Score each criterion from 0.0 to 1.0 based on how well the modification meets requirements
            2. Calculate overall score using weighted average of criteria scores
            3. Determine if overall score meets minimum threshold ({minimum_score})
            4. Identify specific unmet criteria with clear explanations
            5. Provide actionable feedback for improvement if score is below threshold
            
            System Prompt Context: {critic_prompt[:200]}...
            """,
            expected_output=f"""
            Return a valid JSON object with the following structure:
            {{
                "overall_score": 0.XX,
                "criteria_scores": {{
                    "entity_substitution": 0.XX,
                    "jurisdiction_transformation": 0.XX,
                    "liability_reallocation": 0.XX,
                    "clause_operations": 0.XX,
                    "legal_coherence": 0.XX
                }},
                "satisfied": true/false,
                "unmet_criteria": ["list of failed criteria"],
                "feedback": "Specific improvement suggestions for failed criteria",
                "attempt_number": {attempt_number}
            }}
            
            Minimum score required: {minimum_score}
            """,
            expected_output_type="json",
            agent=self.agents.contract_critic(),
        )
        return task

    def chunk_processing_task(self, context):
        """
        Task for processing individual chunks with parallel support.
        Used when document chunking is required for large contracts.
        """
        chunk_content = context.get('chunk_content', '')
        chunk_id = context.get('chunk_id', 1)
        total_chunks = context.get('total_chunks', 1)
        user_prompt = context.get('user_prompt', '')
        
        actor_prompt = self.system_prompts.get_actor_prompt(chunk_id, total_chunks)
        
        task = Task(
            description=f"""
            Process chunk {chunk_id} of {total_chunks} for contract modification:
            
            USER INSTRUCTIONS: {user_prompt}
            
            CHUNK CONTENT TO MODIFY:
            {chunk_content}
            
            CHUNKING CONTEXT:
            - This is chunk {chunk_id} of {total_chunks} total chunks
            - Some instructions may not apply to this specific chunk
            - Return the FULL modified text for this chunk with applicable changes
            - Maintain context awareness for chunk boundaries
            - If no changes are needed for this chunk, return it exactly as provided
            
            PROCESSING REQUIREMENTS:
            1. Apply only the modifications that are relevant to this chunk's content
            2. Maintain RTF formatting and document structure integrity
            3. Preserve chunk boundaries and overlap regions appropriately
            4. Return complete chunk content with modifications applied
            
            System Prompt: {actor_prompt[:300]}...
            """,
            expected_output="""
            Complete chunk content with relevant modifications applied.
            Maintain RTF formatting and return full chunk text.
            Include change indicator: CHUNK_MODIFIED or CHUNK_UNCHANGED
            """,
            agent=self.agents.contract_actor(),
        )
        return task
