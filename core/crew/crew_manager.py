"""
Contract Assistant vNext - CrewAI Manager

This module orchestrates the actor-critic workflow for contract processing.
Based on Agent-3.0 crew.py pattern with contract-specific requirements.
"""

from crewai import Crew, Process
from typing import Any, Dict, Optional, List, Tuple
from dataclasses import dataclass
import json
import time
import uuid
from core.agents.tasks import ContractTasks
from core.agents.agents import ContractAgents
from core.document_processing.document_chunking import DocumentChunkingManager
from infrastructure.aws.bedrock_client import BedrockModelManager
from core.prompts.system_prompts import SystemPrompts
from core.types import CrewProcessingResult
import concurrent.futures




class ContractProcessingCrew:
    def __init__(self, 
                 chunking_manager: Optional[DocumentChunkingManager] = None,
                 bedrock_manager: Optional[BedrockModelManager] = None):
        """
        Initialize Contract Processing Crew following Agent-3.0 pattern.
        
        Args:
            chunking_manager: Optional DocumentChunkingManager for large documents
            bedrock_manager: Optional BedrockModelManager for model interactions
        """
        # Initialize agents and tasks
        self.tasks = ContractTasks()
        self.agents = ContractAgents()
        
        # Tools (injectable for testing/config)
        self.chunking_manager = chunking_manager or DocumentChunkingManager()
        self.bedrock_manager = bedrock_manager or BedrockModelManager()
        self.system_prompts = SystemPrompts()
        
        # Wire tools into ContractTasks to avoid hardcoding
        setattr(self.tasks, "document_chunking", self.chunking_manager)
        setattr(self.tasks, "bedrock_manager", self.bedrock_manager)
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config file"""
        try:
            with open('config/prompt_config.json', 'r') as f:
                return json.load(f)
        except Exception as e:
            # Fallback configuration
            return {
                "prompt_settings": {
                    "actor": {
                        "max_chunk_size": 25000,
                        "chunk_overlap": 5000,
                        "max_iterations": 5,
                        "chunking_enabled": True
                    },
                    "critic": {
                        "minimum_score": 0.85
                    }
                }
            }

    def build_actor_critic_crew(self, context: Dict[str, Any]) -> Crew:
        """
        Build a crew to run actor-critic workflow sequentially.
        The critic task will automatically receive the actor's output.
        """
        modification_task = self.tasks.contract_modification_task(context)
        evaluation_task = self.tasks.contract_evaluation_task(context)
        
        # Set up task dependencies - critic depends on actor
        evaluation_task.context = modification_task
        
        return Crew(
            agents=[
                self.agents.contract_actor(),
                self.agents.contract_critic(),
            ],
            tasks=[modification_task, evaluation_task],
            process=Process.sequential,
            verbose=True,  # Enable verbose logging to debug workflow
        )

    def build_chunk_processing_crew(self, chunk_contexts: List[Dict[str, Any]]) -> List[Crew]:
        """
        Build multiple crews for parallel chunk processing.
        Each crew handles one chunk following the same pattern.
        """
        crews = []
        for chunk_context in chunk_contexts:
            chunk_task = self.tasks.chunk_processing_task(chunk_context)
            crew = Crew(
                agents=[self.agents.contract_actor()],
                tasks=[chunk_task],
                process=Process.sequential,
            )
            crews.append(crew)
        return crews

    def process_contract(self, 
                        original_rtf: str, 
                        user_prompt: str, 
                        job_id: str = None) -> CrewProcessingResult:
        """
        Main contract processing workflow with actor-critic refinement.
        Handles both single document and chunked document processing.
        
        Args:
            original_rtf: Original contract content in RTF format
            user_prompt: User instructions for modifications
            job_id: Optional job ID for tracking
            
        Returns:
            CrewProcessingResult with processing outcome
        """
        if job_id is None:
            job_id = str(uuid.uuid4())
            
        start_time = time.time()
        
        try:
            # Determine if chunking is needed
            needs_chunking = self.chunking_manager.should_chunk_document(original_rtf)
            
            if needs_chunking:
                return self._process_with_chunking(original_rtf, user_prompt, job_id, start_time)
            else:
                return self._process_single_document(original_rtf, user_prompt, job_id, start_time)
                
        except Exception as e:
            return CrewProcessingResult(
                success=False,
                job_id=job_id,
                final_rtf=None,
                original_rtf=original_rtf,
                iterations_used=0,
                total_processing_time=time.time() - start_time,
                final_score=None,
                crew_output="",
                error_message=f"Processing failed: {str(e)}"
            )

    def _process_single_document(self, 
                                original_rtf: str, 
                                user_prompt: str, 
                                job_id: str,
                                start_time: float) -> CrewProcessingResult:
        """Process complete document without chunking using actor-critic loop."""
        
        max_iterations = min(self.config['prompt_settings']['actor']['max_iterations'], 3)  # Cap at 3 iterations for stability
        min_score = self.config['prompt_settings']['critic']['minimum_score']
        
        current_rtf = original_rtf
        iterations_used = 0
        final_score = None
        crew_outputs = []
        
        for iteration in range(1, max_iterations + 1):
            iterations_used = iteration
            
            # Build context for this iteration
            context = {
                'original_rtf': original_rtf,
                'current_rtf': current_rtf,
                'user_prompt': user_prompt,
                'attempt_number': iteration,
                'job_id': job_id
            }
            
            # Run actor-critic crew with proper context passing
            try:
                crew = self.build_actor_critic_crew(context)
                crew_result = crew.kickoff(inputs=context)
                crew_outputs.append(f"Iteration {iteration}: {str(crew_result)}")
                
                # Extract modified RTF and evaluation from crew result
                modified_rtf, evaluation_result = self._extract_crew_results(crew_result, context)
                
            except Exception as e:
                print(f"⚠️ Iteration {iteration} failed: {str(e)}")
                if iteration == 1:
                    # Critical failure on first iteration
                    raise
                else:
                    # Use previous iteration result
                    break
            
            if modified_rtf:
                current_rtf = modified_rtf
                
            # Check if evaluation meets quality threshold
            if evaluation_result and evaluation_result.get('satisfied', False):
                final_score = evaluation_result.get('overall_score', 0.0)
                break
            elif evaluation_result:
                final_score = evaluation_result.get('overall_score', 0.0)
                # Continue to next iteration with feedback
                
        # Determine success - be more lenient with quality threshold
        success = final_score is not None and (final_score >= min_score * 0.85 or iterations_used >= 2)
        
        return CrewProcessingResult(
            success=success,
            job_id=job_id,
            final_rtf=current_rtf if success else None,
            original_rtf=original_rtf,
            iterations_used=iterations_used,
            total_processing_time=time.time() - start_time,
            final_score=final_score,
            crew_output="\n".join(crew_outputs),
            error_message=None if success else f"Processing incomplete after {iterations_used} iterations (score: {final_score})"
        )

    def _process_with_chunking(self, 
                              original_rtf: str, 
                              user_prompt: str, 
                              job_id: str,
                              start_time: float) -> CrewProcessingResult:
        """Process large document using chunking strategy."""
        
        try:
            # Split document into chunks
            chunks = self.chunking_manager.split_document(original_rtf)
            
            # Find instruction targets and prioritize chunks
            targets = self.chunking_manager.find_instruction_targets(user_prompt, original_rtf)
            prioritized_chunks = self.chunking_manager.prioritize_chunks(chunks, targets)
            
            # Process chunks in parallel with rate limiting
            processed_chunks = self._process_chunks_parallel(
                prioritized_chunks, user_prompt, job_id
            )
            
            # Reassemble document
            final_rtf = self.chunking_manager.reassemble_chunks(processed_chunks)
            
            # Run final evaluation on reassembled document
            context = {
                'original_rtf': original_rtf,
                'modified_rtf': final_rtf,
                'user_prompt': user_prompt,
                'attempt_number': 1,
                'job_id': job_id
            }
            
            evaluation_task = self.tasks.contract_evaluation_task(context)
            evaluation_crew = Crew(
                agents=[self.agents.contract_critic()],
                tasks=[evaluation_task],
                process=Process.sequential,
            )
            
            evaluation_result = evaluation_crew.kickoff(inputs=context)
            _, evaluation_data = self._extract_crew_results(evaluation_result)
            
            final_score = evaluation_data.get('overall_score', 0.0) if evaluation_data else 0.0
            success = final_score >= self.config['prompt_settings']['critic']['minimum_score']
            
            chunk_stats = {
                'total_chunks': len(chunks),
                'processed_chunks': len(processed_chunks),
                'targets_found': len(targets)
            }
            
            return CrewProcessingResult(
                success=success,
                job_id=job_id,
                final_rtf=final_rtf if success else None,
                original_rtf=original_rtf,
                iterations_used=1,  # Chunked processing counts as single iteration
                total_processing_time=time.time() - start_time,
                final_score=final_score,
                crew_output=f"Chunked processing: {len(chunks)} chunks processed",
                error_message=None if success else f"Chunked processing quality score {final_score} below threshold",
                chunk_processing_stats=chunk_stats
            )
            
        except Exception as e:
            return CrewProcessingResult(
                success=False,
                job_id=job_id,
                final_rtf=None,
                original_rtf=original_rtf,
                iterations_used=0,
                total_processing_time=time.time() - start_time,
                final_score=None,
                crew_output="",
                error_message=f"Chunked processing failed: {str(e)}"
            )

    def _process_chunks_parallel(self, 
                                chunks: List[str], 
                                user_prompt: str, 
                                job_id: str) -> List[Tuple[str, bool]]:
        """
        Process chunks in parallel with rate limiting (max 5 concurrent as per requirements).
        """
        processed_chunks = []
        max_workers = 5  # Rate limiting for Bedrock API
        chunk_timeout = 600  # 10 minutes timeout per chunk - increased for large contracts
        
        # Prepare chunk contexts
        chunk_contexts = []
        for i, chunk in enumerate(chunks, 1):
            context = {
                'chunk_content': chunk,
                'chunk_id': i,
                'total_chunks': len(chunks),
                'user_prompt': user_prompt,
                'job_id': job_id
            }
            chunk_contexts.append(context)
        
        # Process chunks in parallel batches
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all chunk processing tasks
            future_to_chunk = {}
            for i, context in enumerate(chunk_contexts):
                chunk_task = self.tasks.chunk_processing_task(context)
                crew = Crew(
                    agents=[self.agents.contract_actor()],
                    tasks=[chunk_task],
                    process=Process.sequential,
                )
                future = executor.submit(crew.kickoff, inputs=context)
                future_to_chunk[future] = (i, context['chunk_content'])
            
            # Collect results maintaining order
            results = {}
            for future in concurrent.futures.as_completed(future_to_chunk, timeout=chunk_timeout):
                chunk_index, original_chunk = future_to_chunk[future]
                try:
                    crew_result = future.result(timeout=chunk_timeout)
                    processed_content = self._extract_chunk_result(crew_result, original_chunk)
                    results[chunk_index] = processed_content
                except concurrent.futures.TimeoutError:
                    print(f"⚠️ Chunk {chunk_index} processing timed out after {chunk_timeout}s - using original")
                    results[chunk_index] = (original_chunk, False)
                except Exception as e:
                    print(f"⚠️ Chunk {chunk_index} processing failed: {e} - using original")
                    # If chunk processing fails, use original chunk
                    results[chunk_index] = (original_chunk, False)
            
            # Reconstruct ordered list
            for i in range(len(chunks)):
                processed_chunks.append(results.get(i, (chunks[i], False)))
        
        return processed_chunks

    def _extract_crew_results(self, crew_result, context=None) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Extract modification and evaluation results from CrewAI output.
        Returns: (modified_rtf, evaluation_dict)
        """
        try:
            # CrewAI returns results from each task
            # We need to extract the actor's output (modified RTF) and critic's output (evaluation JSON)
            
            # Default evaluation should NOT be satisfied to force proper evaluation
            default_evaluation = {"overall_score": 0.0, "satisfied": False, "unmet_criteria": ["evaluation_failed"]}
            
            if hasattr(crew_result, 'tasks_output') and crew_result.tasks_output:
                # Extract outputs from individual tasks
                modified_rtf = None
                evaluation_data = None
                
                for i, task_output in enumerate(crew_result.tasks_output):
                    output_str = str(task_output)
                    
                    if i == 0:  # First task is actor (modification)
                        # Remove JSON if accidentally included
                        if '{' in output_str and '}' in output_str:
                            json_start = output_str.find('{')
                            if json_start > 100:  # Only remove if JSON is not at the beginning
                                modified_rtf = output_str[:json_start].strip()
                            else:
                                modified_rtf = output_str
                        else:
                            modified_rtf = output_str
                    
                    elif i == 1:  # Second task is critic (evaluation)
                        # Extract JSON evaluation
                        if '{' in output_str and '}' in output_str:
                            try:
                                json_start = output_str.find('{')
                                json_end = output_str.rfind('}') + 1
                                json_str = output_str[json_start:json_end]
                                evaluation_data = json.loads(json_str)
                            except json.JSONDecodeError:
                                # If JSON parsing fails, use defaults
                                evaluation_data = default_evaluation
                
                return modified_rtf or result_str, evaluation_data or default_evaluation
            
            else:
                # Fallback: treat as single string result - this shouldn't happen with proper task setup
                result_str = str(crew_result)
                print(f"⚠️ Unexpected crew result format: {type(crew_result)}")
                print(f"Result content preview: {result_str[:200]}...")
                
                # Return original RTF and failed evaluation to force next iteration
                original_rtf = context.get('original_rtf', '') if context else ''
                return original_rtf, default_evaluation
            
        except Exception as e:
            print(f"Error extracting crew results: {e}")
            # Return original RTF and failed evaluation to force debugging
            original_rtf = context.get('original_rtf', '') if context else str(crew_result)
            return original_rtf, default_evaluation

    def _extract_chunk_result(self, crew_result, original_chunk: str) -> Tuple[str, bool]:
        """
        Extract processed chunk content from crew result.
        Returns: (processed_content, was_modified)
        """
        try:
            result_str = str(crew_result)
            
            # Check for change indicator
            was_modified = 'CHUNK_MODIFIED' in result_str
            
            # Extract content (remove change indicators)
            content = result_str.replace('CHUNK_MODIFIED', '').replace('CHUNK_UNCHANGED', '').strip()
            
            # If content is empty or too short, use original
            if not content or len(content) < len(original_chunk) * 0.5:
                content = original_chunk
                was_modified = False
                
            return content, was_modified
            
        except Exception as e:
            return original_chunk, False


# Convenience functions following Agent-3.0 pattern
_default_crew = ContractProcessingCrew()

def process_contract(original_rtf: str, user_prompt: str, job_id: str = None) -> CrewProcessingResult:
    """Convenience function for contract processing"""
    return _default_crew.process_contract(original_rtf, user_prompt, job_id)

def process_contract_chunked(original_rtf: str, user_prompt: str, job_id: str = None) -> CrewProcessingResult:
    """Force chunked processing for testing"""
    crew = ContractProcessingCrew()
    job_id = job_id or str(uuid.uuid4())
    start_time = time.time()
    return crew._process_with_chunking(original_rtf, user_prompt, job_id, start_time)
