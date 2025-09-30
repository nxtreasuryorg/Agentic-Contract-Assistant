"""
AWS Bedrock Model Manager for Contract Assistant vNext

This module provides the foundation for AWS Bedrock integration with support for:
- Nova Premier v1:0 (1000k) and Mistral Large 2402 v1:0 models
- Retry logic and error handling
- Model selection based on task complexity
- Rate limiting and concurrent request management
"""

import boto3
import json
import time
import logging
import os
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import concurrent.futures
from botocore.exceptions import ClientError, BotoCoreError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TaskComplexity(Enum):
    """Task complexity levels for model selection"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class BedrockResponse:
    """Response from Bedrock model invocation"""
    content: str
    model_id: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    success: bool
    error_message: Optional[str] = None


class BedrockModelManager:
    """
    Manages AWS Bedrock model interactions with retry logic and error handling.
    
    Supports:
    - Primary model: amazon.nova-premier-v1:0:1000k
    - Fallback model: mistral.mistral-large-2402-v1:0
    - Intelligent model selection based on task complexity
    - Retry logic with exponential backoff
    - Rate limiting for concurrent requests
    """
    
    # Model configurations
    MODELS = {
        "nova_pro": "us.amazon.nova-pro-v1:0",
        "mistral_large": "mistral.mistral-large-2402-v1:0"
    }
    
    # Model parameters
    MODEL_PARAMS = {
        "us.amazon.nova-pro-v1:0": {
            "maxTokens": 8000,  # Nova Pro max output tokens
            "temperature": 0.1,
            "topP": 0.9
        },
        "mistral.mistral-large-2402-v1:0": {
            "max_tokens": 4000,
            "temperature": 0.1,
            "top_p": 0.9
        }
    }
    
    # Request timeout configurations for large contracts
    REQUEST_TIMEOUT_SECONDS = 600  # 10 minutes for large document processing
    
    def __init__(self, 
                 region_name: Optional[str] = None,
                 max_concurrent_requests: Optional[int] = None,
                 max_retries: Optional[int] = None,
                 base_delay: Optional[float] = None):
        """
        Initialize Bedrock Model Manager
        
        Args:
            region_name: AWS region for Bedrock service (defaults to env var)
            max_concurrent_requests: Maximum concurrent API calls (defaults to env var)
            max_retries: Maximum retry attempts for failed requests (defaults to env var)
            base_delay: Base delay for exponential backoff (defaults to env var)
        """
        # Load configuration from environment variables with defaults
        self.region_name = region_name or os.getenv('AWS_REGION_NAME', 'us-east-1')
        self.max_concurrent_requests = max_concurrent_requests or int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        self.max_retries = max_retries or int(os.getenv('MAX_RETRIES', '5'))  # Increased for large contracts
        self.base_delay = base_delay or float(os.getenv('BASE_DELAY', '2.0'))  # Increased base delay
        
        # Initialize Bedrock client with credentials from environment
        try:
            # AWS credentials will be loaded from environment variables
            # Configure with increased timeout for large contracts
            import botocore.config
            config = botocore.config.Config(
                read_timeout=self.REQUEST_TIMEOUT_SECONDS,
                connect_timeout=30,
                retries={'max_attempts': self.max_retries}
            )
            
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.region_name,
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                config=config
            )
        except Exception as e:
            logging.error(f"Failed to initialize Bedrock client: {e}")
            raise
        
        # Rate limiting semaphore
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Model selection preferences from environment variables
        self.primary_model = os.getenv('CONTRACT_PRIMARY_MODEL', self.MODELS["nova_pro"])
        self.fallback_model = os.getenv('CONTRACT_FALLBACK_MODEL', self.MODELS["mistral_large"])
    
    def get_model_for_task(self, task_complexity: TaskComplexity, 
                          document_length: int = 0) -> str:
        """
        Select optimal model based on task complexity and document characteristics
        
        Args:
            task_complexity: Complexity level of the task
            document_length: Length of document in characters
            
        Returns:
            Model ID string for the selected model
        """
        # Complex tasks or large documents use Nova Pro
        if (task_complexity == TaskComplexity.COMPLEX or 
            document_length > 15000):
            return self.primary_model
        
        # Moderate complexity tasks use Nova Pro for better accuracy
        elif task_complexity == TaskComplexity.MODERATE:
            return self.primary_model
        
        # Simple tasks can use Mistral Large for faster processing
        else:
            return self.fallback_model
    
    def _prepare_request_body(self, model_id: str, prompt: str, 
                             system_prompt: Optional[str] = None) -> str:
        """
        Prepare request body based on model type
        
        Args:
            model_id: Bedrock model identifier
            prompt: User prompt text
            system_prompt: Optional system prompt
            
        Returns:
            JSON string for request body
        """
        if "nova" in model_id:
            # Nova model format with schemaVersion
            messages = [{"role": "user", "content": [{"text": prompt}]}]
            system_list = []
            if system_prompt:
                system_list.append({"text": system_prompt})
            
            body = {
                "schemaVersion": "messages-v1",
                "messages": messages,
                "inferenceConfig": self.MODEL_PARAMS[model_id]
            }
            if system_list:
                body["system"] = system_list
        elif "mistral" in model_id:
            # Mistral model format
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            body = {
                "messages": messages,
                **self.MODEL_PARAMS[model_id]
            }
        else:
            raise ValueError(f"Unsupported model: {model_id}")
        
        return json.dumps(body)
    
    def _parse_response(self, model_id: str, response_body: str) -> Tuple[str, Dict[str, int]]:
        """
        Parse model response based on model type
        
        Args:
            model_id: Bedrock model identifier
            response_body: Raw response from Bedrock
            
        Returns:
            Tuple of (content, token_usage)
        """
        response_data = json.loads(response_body)
        
        if "nova" in model_id:
            content = response_data["output"]["message"]["content"][0]["text"]
            token_usage = {
                "input_tokens": response_data.get("usage", {}).get("inputTokens", 0),
                "output_tokens": response_data.get("usage", {}).get("outputTokens", 0)
            }
        elif "mistral" in model_id:
            content = response_data["choices"][0]["message"]["content"]
            token_usage = {
                "input_tokens": response_data.get("usage", {}).get("prompt_tokens", 0),
                "output_tokens": response_data.get("usage", {}).get("completion_tokens", 0)
            }
        else:
            raise ValueError(f"Unsupported model: {model_id}")
        
        return content, token_usage
    
    def invoke_model(self, 
                    model_id: str, 
                    prompt: str,
                    system_prompt: Optional[str] = None,
                    max_tokens: int = 4000) -> BedrockResponse:
        """
        Invoke Bedrock model with retry logic and error handling
        
        Args:
            model_id: Bedrock model identifier
            prompt: User prompt text
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            BedrockResponse with model output and metadata
        """
        start_time = time.time()
        
        for attempt in range(self.max_retries + 1):
            try:
                # Prepare request
                request_body = self._prepare_request_body(model_id, prompt, system_prompt)
                
                # Make API call
                response = self.bedrock_client.invoke_model(
                    modelId=model_id,
                    body=request_body,
                    contentType="application/json",
                    accept="application/json"
                )
                
                # Parse response
                response_body = response['body'].read().decode('utf-8')
                content, token_usage = self._parse_response(model_id, response_body)
                
                # Calculate latency
                latency_ms = (time.time() - start_time) * 1000
                
                self.logger.info(f"Successfully invoked {model_id} in {latency_ms:.2f}ms")
                
                return BedrockResponse(
                    content=content,
                    model_id=model_id,
                    input_tokens=token_usage["input_tokens"],
                    output_tokens=token_usage["output_tokens"],
                    latency_ms=latency_ms,
                    success=True
                )
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                
                self.logger.warning(f"Bedrock API error (attempt {attempt + 1}): {error_code} - {error_message}")
                
                # Handle specific error types
                if error_code in ['ThrottlingException', 'ServiceQuotaExceededException']:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        self.logger.info(f"Rate limited, retrying in {delay}s...")
                        time.sleep(delay)
                        continue
                elif error_code in ['ValidationException', 'AccessDeniedException']:
                    # Don't retry for validation or access errors
                    break
                else:
                    # Retry for other errors
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                
            except BotoCoreError as e:
                self.logger.warning(f"Boto3 error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
                    
            except Exception as e:
                self.logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    time.sleep(delay)
                    continue
        
        # All retries failed
        latency_ms = (time.time() - start_time) * 1000
        error_msg = f"Failed to invoke {model_id} after {self.max_retries + 1} attempts"
        self.logger.error(error_msg)
        
        return BedrockResponse(
            content="",
            model_id=model_id,
            input_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error_message=error_msg
        )
    
    def invoke_with_fallback(self, 
                           prompt: str,
                           task_complexity: TaskComplexity = TaskComplexity.MODERATE,
                           document_length: int = 0,
                           system_prompt: Optional[str] = None) -> BedrockResponse:
        """
        Invoke model with automatic fallback to secondary model on failure
        
        Args:
            prompt: User prompt text
            task_complexity: Complexity level for model selection
            document_length: Document length for model selection
            system_prompt: Optional system prompt
            
        Returns:
            BedrockResponse from primary or fallback model
        """
        # Select primary model
        primary_model = self.get_model_for_task(task_complexity, document_length)
        
        # Try primary model
        response = self.invoke_model(primary_model, prompt, system_prompt)
        
        if response.success:
            return response
        
        # Fallback to secondary model
        fallback_model = self.fallback_model if primary_model == self.primary_model else self.primary_model
        
        self.logger.info(f"Primary model {primary_model} failed, trying fallback {fallback_model}")
        
        return self.invoke_model(fallback_model, prompt, system_prompt)
    
    async def invoke_model_async(self, 
                               model_id: str, 
                               prompt: str,
                               system_prompt: Optional[str] = None) -> BedrockResponse:
        """
        Async version of invoke_model with rate limiting
        
        Args:
            model_id: Bedrock model identifier
            prompt: User prompt text
            system_prompt: Optional system prompt
            
        Returns:
            BedrockResponse with model output and metadata
        """
        async with self.semaphore:
            # Run synchronous invoke_model in thread pool
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                response = await loop.run_in_executor(
                    executor, 
                    self.invoke_model, 
                    model_id, 
                    prompt, 
                    system_prompt
                )
            return response
    
    def test_connectivity(self) -> Dict[str, Any]:
        """
        Test Bedrock connectivity and authentication with sample prompts
        
        Returns:
            Dictionary with test results for each model
        """
        test_prompt = "Hello, please respond with 'Connection successful' to confirm you are working."
        test_results = {}
        
        for model_name, model_id in self.MODELS.items():
            self.logger.info(f"Testing connectivity for {model_name} ({model_id})")
            
            try:
                response = self.invoke_model(model_id, test_prompt)
                
                test_results[model_name] = {
                    "model_id": model_id,
                    "success": response.success,
                    "latency_ms": response.latency_ms,
                    "response_preview": response.content[:100] if response.content else "",
                    "error": response.error_message
                }
                
                if response.success:
                    self.logger.info(f"✓ {model_name} connectivity test passed")
                else:
                    self.logger.error(f"✗ {model_name} connectivity test failed: {response.error_message}")
                    
            except Exception as e:
                test_results[model_name] = {
                    "model_id": model_id,
                    "success": False,
                    "latency_ms": 0,
                    "response_preview": "",
                    "error": str(e)
                }
                self.logger.error(f"✗ {model_name} connectivity test failed with exception: {e}")
        
        return test_results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about configured models and settings
        
        Returns:
            Dictionary with model configuration details
        """
        return {
            "models": self.MODELS,
            "model_params": self.MODEL_PARAMS,
            "primary_model": self.primary_model,
            "fallback_model": self.fallback_model,
            "max_concurrent_requests": self.max_concurrent_requests,
            "max_retries": self.max_retries,
            "base_delay": self.base_delay,
            "region": self.region_name
        }