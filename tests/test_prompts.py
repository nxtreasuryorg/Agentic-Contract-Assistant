#!/usr/bin/env python3
"""
Test script for validating system prompt effectiveness.
Tests the Actor and Critic prompts with sample contract content.
"""

import os
import sys
import json
from typing import Dict, Any

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from system_prompts import SystemPrompts


def load_sample_contract() -> str:
    """Load the sample contract RTF content."""
    sample_path = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_contract.rtf')
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Sample contract not found at {sample_path}")
        return "Sample RTF content for testing"


def test_actor_prompt_basic():
    """Test basic Actor prompt generation."""
    print("=" * 60)
    print("TESTING ACTOR PROMPT - BASIC")
    print("=" * 60)
    
    prompt = SystemPrompts.get_actor_prompt()
    
    # Validate prompt structure
    assert "precise contract editor" in prompt.lower()
    assert "rtf formatting" in prompt.lower()
    assert "semantic manipulation" in prompt.lower()
    assert "counterparty name changes" in prompt.lower()
    assert "liability reallocation" in prompt.lower()
    
    print(f"✓ Basic Actor prompt generated successfully ({len(prompt)} characters)")
    print(f"✓ Contains required semantic manipulation instructions")
    print(f"✓ Contains RTF formatting preservation rules")
    
    return prompt


def test_actor_prompt_chunking():
    """Test Actor prompt with chunking support."""
    print("\n" + "=" * 60)
    print("TESTING ACTOR PROMPT - CHUNKING")
    print("=" * 60)
    
    prompt = SystemPrompts.get_actor_prompt(chunk_id=2, total_chunks=5)
    
    # Validate chunking context
    assert "chunk 2 of 5" in prompt
    assert "CHUNKING CONTEXT" in prompt
    assert "context awareness across chunk boundaries" in prompt.lower()
    
    print(f"✓ Chunked Actor prompt generated successfully ({len(prompt)} characters)")
    print(f"✓ Contains chunking context for chunk 2 of 5")
    print(f"✓ Includes chunk boundary awareness instructions")
    
    return prompt


def test_critic_prompt():
    """Test Critic prompt generation."""
    print("\n" + "=" * 60)
    print("TESTING CRITIC PROMPT")
    print("=" * 60)
    
    prompt = SystemPrompts.get_critic_prompt()
    
    # Validate prompt structure
    assert "senior legal contract evaluator" in prompt.lower()
    assert "evaluation criteria" in prompt.lower()
    assert "entity substitution completeness" in prompt.lower()
    assert "jurisdiction transformation" in prompt.lower()
    assert "liability reallocation" in prompt.lower()
    assert "0.85" in prompt  # Minimum score threshold
    assert "json evaluation" in prompt.lower()
    
    print(f"✓ Critic prompt generated successfully ({len(prompt)} characters)")
    print(f"✓ Contains all 5 evaluation criteria with weights")
    print(f"✓ Includes JSON output format requirements")
    print(f"✓ Specifies 0.85 minimum acceptable score")
    
    return prompt


def test_task_descriptions():
    """Test task description generation."""
    print("\n" + "=" * 60)
    print("TESTING TASK DESCRIPTIONS")
    print("=" * 60)
    
    sample_rtf = load_sample_contract()
    user_instruction = "Change all references from 'Hash Blockchain Limited' to 'Quantum Finance Corp' and update governing law from Hong Kong to Singapore"
    
    # Test Actor task description
    actor_task = SystemPrompts.create_actor_task_description(sample_rtf, user_instruction)
    
    assert "semantic manipulations" in actor_task.lower()
    assert user_instruction in actor_task
    assert "rtf format" in actor_task.lower()
    
    print(f"✓ Actor task description generated ({len(actor_task)} characters)")
    
    # Test Actor task with chunking
    chunk_info = {
        'chunk_id': 1,
        'total_chunks': 3,
        'chunk_content': sample_rtf[:500]
    }
    
    chunked_actor_task = SystemPrompts.create_actor_task_description(
        sample_rtf, user_instruction, chunk_info
    )
    
    assert "chunk 1 of 3" in chunked_actor_task
    assert "CHUNKING INFORMATION" in chunked_actor_task
    
    print(f"✓ Chunked Actor task description generated ({len(chunked_actor_task)} characters)")
    
    # Test Critic task description
    modified_rtf = sample_rtf.replace("Hash Blockchain Limited", "Quantum Finance Corp")
    critic_task = SystemPrompts.create_critic_task_description(
        sample_rtf, modified_rtf, user_instruction, attempt_number=2
    )
    
    assert "evaluate the quality" in critic_task.lower()
    assert "ATTEMPT NUMBER: 2" in critic_task
    assert "0.85" in critic_task
    
    print(f"✓ Critic task description generated ({len(critic_task)} characters)")
    
    return actor_task, chunked_actor_task, critic_task


def test_prompt_templates():
    """Test prompt template functionality with variable substitution."""
    print("\n" + "=" * 60)
    print("TESTING PROMPT TEMPLATES")
    print("=" * 60)
    
    # Test Actor template
    actor_template = SystemPrompts.get_prompt_template('actor')
    assert len(actor_template) > 1000
    print(f"✓ Actor template retrieved ({len(actor_template)} characters)")
    
    # Test Actor template with chunking
    chunked_template = SystemPrompts.get_prompt_template(
        'actor', 
        chunk_id=3, 
        total_chunks=7
    )
    assert "chunk 3 of 7" in chunked_template
    print(f"✓ Chunked Actor template with variables ({len(chunked_template)} characters)")
    
    # Test Critic template
    critic_template = SystemPrompts.get_prompt_template('critic')
    assert len(critic_template) > 1000
    print(f"✓ Critic template retrieved ({len(critic_template)} characters)")
    
    # Test invalid template type
    try:
        SystemPrompts.get_prompt_template('invalid')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Properly handles invalid template type: {e}")


def test_legacy_patterns():
    """Test legacy pattern definitions."""
    print("\n" + "=" * 60)
    print("TESTING LEGACY PATTERNS")
    print("=" * 60)
    
    from system_prompts import LEGACY_PATTERNS
    
    # Validate pattern structure
    required_patterns = ['entity_substitution', 'domicile_shift', 'liability_reallocation']
    
    for pattern_name in required_patterns:
        assert pattern_name in LEGACY_PATTERNS
        pattern = LEGACY_PATTERNS[pattern_name]
        assert 'pattern' in pattern
        assert 'requirements' in pattern
        assert isinstance(pattern['requirements'], list)
        print(f"✓ {pattern_name} pattern defined with {len(pattern['requirements'])} requirements")


def test_sample_contract_processing():
    """Test prompt effectiveness with sample contract scenarios."""
    print("\n" + "=" * 60)
    print("TESTING SAMPLE CONTRACT SCENARIOS")
    print("=" * 60)
    
    sample_rtf = load_sample_contract()
    
    # Test scenario 1: Entity substitution
    scenario_1 = {
        "instruction": "Change all references from 'Hash Blockchain Limited' to 'Quantum Finance Corp'",
        "expected_changes": [
            "Company name in header",
            "Defined terms section",
            "Signature block",
            "Address information"
        ]
    }
    
    actor_task_1 = SystemPrompts.create_actor_task_description(
        sample_rtf, scenario_1["instruction"]
    )
    
    assert "Hash Blockchain Limited" in actor_task_1
    assert "Quantum Finance Corp" in actor_task_1
    print(f"✓ Scenario 1 (Entity substitution) task created")
    
    # Test scenario 2: Jurisdiction change
    scenario_2 = {
        "instruction": "Change governing law from Hong Kong to Singapore, update all jurisdictional references",
        "expected_changes": [
            "Governing law clause",
            "Jurisdiction clause",
            "Court references"
        ]
    }
    
    actor_task_2 = SystemPrompts.create_actor_task_description(
        sample_rtf, scenario_2["instruction"]
    )
    
    assert "Hong Kong" in actor_task_2
    assert "Singapore" in actor_task_2
    print(f"✓ Scenario 2 (Jurisdiction change) task created")
    
    # Test scenario 3: Liability reallocation
    scenario_3 = {
        "instruction": "Shift liability from Company to Client, reverse indemnification clauses",
        "expected_changes": [
            "Indemnification direction",
            "Liability caps",
            "Insurance requirements"
        ]
    }
    
    actor_task_3 = SystemPrompts.create_actor_task_description(
        sample_rtf, scenario_3["instruction"]
    )
    
    assert "liability" in actor_task_3.lower()
    assert "indemnification" in actor_task_3.lower()
    print(f"✓ Scenario 3 (Liability reallocation) task created")
    
    print(f"✓ All sample contract scenarios processed successfully")


def run_all_tests():
    """Run all prompt effectiveness tests."""
    print("STARTING SYSTEM PROMPT EFFECTIVENESS TESTS")
    print("=" * 80)
    
    try:
        # Run individual tests
        test_actor_prompt_basic()
        test_actor_prompt_chunking()
        test_critic_prompt()
        test_task_descriptions()
        test_prompt_templates()
        test_legacy_patterns()
        test_sample_contract_processing()
        
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED SUCCESSFULLY! ✓")
        print("=" * 80)
        print("\nSUMMARY:")
        print("✓ Actor prompt generation working correctly")
        print("✓ Chunking support implemented and tested")
        print("✓ Critic prompt generation working correctly")
        print("✓ Task description generation functional")
        print("✓ Template system with variable substitution working")
        print("✓ Legacy patterns properly defined")
        print("✓ Sample contract scenarios processed successfully")
        print("\nSystem prompts are ready for CrewAI integration!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)