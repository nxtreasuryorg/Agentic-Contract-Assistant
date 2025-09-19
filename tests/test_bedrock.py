#!/usr/bin/env python3
"""
Test script for AWS Bedrock integration

This script tests the BedrockModelManager functionality including:
- Connectivity and authentication
- Model selection logic
- Retry mechanisms
- Error handling
"""

import sys
import os
import logging
from dotenv import load_dotenv
from bedrock_client import BedrockModelManager, TaskComplexity

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_bedrock_connectivity():
    """Test basic Bedrock connectivity and authentication"""
    print("=" * 60)
    print("Testing AWS Bedrock Connectivity")
    print("=" * 60)
    
    try:
        # Initialize Bedrock manager
        manager = BedrockModelManager()
        
        # Display configuration
        print(f"Region: {manager.region_name}")
        print(f"Primary Model: {manager.primary_model}")
        print(f"Fallback Model: {manager.fallback_model}")
        print(f"Max Retries: {manager.max_retries}")
        print()
        
        # Test connectivity
        print("Testing model connectivity...")
        test_results = manager.test_connectivity()
        
        # Display results
        for model_name, result in test_results.items():
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"{model_name}: {status}")
            print(f"  Model ID: {result['model_id']}")
            print(f"  Latency: {result['latency_ms']:.2f}ms")
            
            if result["success"]:
                print(f"  Response: {result['response_preview']}")
            else:
                print(f"  Error: {result['error']}")
            print()
        
        return all(result["success"] for result in test_results.values())
        
    except Exception as e:
        print(f"Failed to initialize Bedrock manager: {e}")
        return False

def test_model_selection():
    """Test model selection logic based on task complexity"""
    print("=" * 60)
    print("Testing Model Selection Logic")
    print("=" * 60)
    
    try:
        manager = BedrockModelManager()
        
        test_cases = [
            (TaskComplexity.SIMPLE, 1000, "Simple task, short document"),
            (TaskComplexity.MODERATE, 5000, "Moderate task, medium document"),
            (TaskComplexity.COMPLEX, 20000, "Complex task, large document"),
            (TaskComplexity.SIMPLE, 20000, "Simple task, large document"),
        ]
        
        for complexity, doc_length, description in test_cases:
            selected_model = manager.get_model_for_task(complexity, doc_length)
            print(f"{description}:")
            print(f"  Complexity: {complexity.value}")
            print(f"  Document Length: {doc_length} chars")
            print(f"  Selected Model: {selected_model}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Model selection test failed: {e}")
        return False

def test_sample_invocations():
    """Test sample model invocations with different prompts"""
    print("=" * 60)
    print("Testing Sample Model Invocations")
    print("=" * 60)
    
    try:
        manager = BedrockModelManager()
        
        test_prompts = [
            {
                "prompt": "What is the capital of France?",
                "complexity": TaskComplexity.SIMPLE,
                "description": "Simple factual question"
            },
            {
                "prompt": "Explain the key differences between contract law and tort law in 2-3 sentences.",
                "complexity": TaskComplexity.MODERATE,
                "description": "Legal knowledge question"
            },
            {
                "prompt": "Analyze this contract clause and suggest improvements: 'The party agrees to perform all obligations.'",
                "complexity": TaskComplexity.COMPLEX,
                "description": "Contract analysis task"
            }
        ]
        
        for i, test_case in enumerate(test_prompts, 1):
            print(f"Test {i}: {test_case['description']}")
            print(f"Prompt: {test_case['prompt']}")
            print(f"Complexity: {test_case['complexity'].value}")
            
            # Test with fallback
            response = manager.invoke_with_fallback(
                prompt=test_case['prompt'],
                task_complexity=test_case['complexity']
            )
            
            if response.success:
                print(f"✓ SUCCESS")
                print(f"Model Used: {response.model_id}")
                print(f"Latency: {response.latency_ms:.2f}ms")
                print(f"Input Tokens: {response.input_tokens}")
                print(f"Output Tokens: {response.output_tokens}")
                print(f"Response: {response.content[:200]}...")
            else:
                print(f"✗ FAILED: {response.error_message}")
            
            print("-" * 40)
        
        return True
        
    except Exception as e:
        print(f"Sample invocation test failed: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid inputs"""
    print("=" * 60)
    print("Testing Error Handling")
    print("=" * 60)
    
    try:
        manager = BedrockModelManager()
        
        # Test with invalid model
        print("Testing invalid model ID...")
        response = manager.invoke_model(
            model_id="invalid-model-id",
            prompt="Test prompt"
        )
        
        if not response.success:
            print("✓ Invalid model correctly handled")
            print(f"Error: {response.error_message}")
        else:
            print("✗ Invalid model should have failed")
        
        print()
        
        # Test with empty prompt
        print("Testing empty prompt...")
        response = manager.invoke_with_fallback(
            prompt="",
            task_complexity=TaskComplexity.SIMPLE
        )
        
        print(f"Empty prompt result: {'SUCCESS' if response.success else 'FAILED'}")
        if not response.success:
            print(f"Error: {response.error_message}")
        
        return True
        
    except Exception as e:
        print(f"Error handling test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("AWS Bedrock Integration Test Suite")
    print("=" * 60)
    
    # Check environment variables
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_REGION_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file configuration.")
        return False
    
    print("✅ Environment variables loaded successfully")
    print()
    
    # Run tests
    tests = [
        ("Connectivity Test", test_bedrock_connectivity),
        ("Model Selection Test", test_model_selection),
        ("Sample Invocations Test", test_sample_invocations),
        ("Error Handling Test", test_error_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅' if result else '❌'} {test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            results.append((test_name, False))
            print(f"❌ {test_name}: FAILED with exception: {e}")
        print()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bedrock integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)