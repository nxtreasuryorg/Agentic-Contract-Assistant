#!/usr/bin/env python3
"""
Example usage of BedrockModelManager for Contract Assistant vNext

This script demonstrates how to use the BedrockModelManager for various
contract processing tasks with different complexity levels.
"""

import asyncio
from bedrock_client import BedrockModelManager, TaskComplexity

def main():
    """Demonstrate BedrockModelManager usage"""
    
    # Initialize the manager
    print("Initializing Bedrock Model Manager...")
    manager = BedrockModelManager()
    
    # Display configuration
    print(f"Primary Model: {manager.primary_model}")
    print(f"Fallback Model: {manager.fallback_model}")
    print(f"Region: {manager.region_name}")
    print()
    
    # Example 1: Simple contract question
    print("=" * 60)
    print("Example 1: Simple Contract Question")
    print("=" * 60)
    
    simple_prompt = "What is a force majeure clause in a contract?"
    
    response = manager.invoke_with_fallback(
        prompt=simple_prompt,
        task_complexity=TaskComplexity.SIMPLE
    )
    
    if response.success:
        print(f"✓ Model: {response.model_id}")
        print(f"✓ Latency: {response.latency_ms:.2f}ms")
        print(f"✓ Response: {response.content[:300]}...")
    else:
        print(f"✗ Error: {response.error_message}")
    
    print()
    
    # Example 2: Contract analysis task
    print("=" * 60)
    print("Example 2: Contract Analysis Task")
    print("=" * 60)
    
    contract_clause = """
    "The Contractor shall indemnify and hold harmless the Client from any and all 
    claims, damages, losses, and expenses arising out of the performance of this Agreement."
    """
    
    analysis_prompt = f"""
    Analyze the following contract clause and provide suggestions for improvement:
    
    {contract_clause}
    
    Please consider:
    1. Clarity and specificity
    2. Potential legal risks
    3. Balanced protection for both parties
    4. Industry best practices
    """
    
    response = manager.invoke_with_fallback(
        prompt=analysis_prompt,
        task_complexity=TaskComplexity.COMPLEX,
        document_length=len(analysis_prompt)
    )
    
    if response.success:
        print(f"✓ Model: {response.model_id}")
        print(f"✓ Latency: {response.latency_ms:.2f}ms")
        print(f"✓ Input Tokens: {response.input_tokens}")
        print(f"✓ Output Tokens: {response.output_tokens}")
        print(f"✓ Analysis:\n{response.content}")
    else:
        print(f"✗ Error: {response.error_message}")
    
    print()
    
    # Example 3: Contract modification task
    print("=" * 60)
    print("Example 3: Contract Modification Task")
    print("=" * 60)
    
    modification_prompt = """
    Please modify the following contract clause to be more balanced and specific:
    
    Original: "The Client may terminate this agreement at any time for any reason."
    
    Requirements:
    - Add reasonable notice period
    - Include provisions for work in progress
    - Specify payment terms for completed work
    - Maintain flexibility while protecting both parties
    """
    
    response = manager.invoke_with_fallback(
        prompt=modification_prompt,
        task_complexity=TaskComplexity.MODERATE
    )
    
    if response.success:
        print(f"✓ Model: {response.model_id}")
        print(f"✓ Latency: {response.latency_ms:.2f}ms")
        print(f"✓ Modified Clause:\n{response.content}")
    else:
        print(f"✗ Error: {response.error_message}")
    
    print()
    
    # Example 4: Model information
    print("=" * 60)
    print("Model Configuration Information")
    print("=" * 60)
    
    model_info = manager.get_model_info()
    
    print("Available Models:")
    for name, model_id in model_info["models"].items():
        print(f"  {name}: {model_id}")
    
    print(f"\nConfiguration:")
    print(f"  Max Concurrent Requests: {model_info['max_concurrent_requests']}")
    print(f"  Max Retries: {model_info['max_retries']}")
    print(f"  Base Delay: {model_info['base_delay']}s")
    print(f"  Region: {model_info['region']}")

async def async_example():
    """Demonstrate async usage for concurrent requests"""
    print("\n" + "=" * 60)
    print("Async Example: Concurrent Requests")
    print("=" * 60)
    
    manager = BedrockModelManager()
    
    # Multiple prompts to process concurrently
    prompts = [
        "What is a non-disclosure agreement?",
        "Explain the concept of consideration in contracts.",
        "What are the key elements of a valid contract?",
        "Define breach of contract and its remedies."
    ]
    
    # Process all prompts concurrently
    tasks = [
        manager.invoke_model_async(
            model_id=manager.fallback_model,  # Use faster model for simple questions
            prompt=prompt
        )
        for prompt in prompts
    ]
    
    print(f"Processing {len(prompts)} requests concurrently...")
    start_time = asyncio.get_event_loop().time()
    
    responses = await asyncio.gather(*tasks)
    
    end_time = asyncio.get_event_loop().time()
    total_time = (end_time - start_time) * 1000
    
    print(f"✓ Completed in {total_time:.2f}ms total")
    
    for i, (prompt, response) in enumerate(zip(prompts, responses), 1):
        if response.success:
            print(f"\nQ{i}: {prompt}")
            print(f"A{i}: {response.content[:150]}...")
            print(f"    Latency: {response.latency_ms:.2f}ms")
        else:
            print(f"\nQ{i}: {prompt}")
            print(f"    Error: {response.error_message}")

if __name__ == "__main__":
    # Run synchronous examples
    main()
    
    # Run async example
    asyncio.run(async_example())