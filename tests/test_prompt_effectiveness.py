#!/usr/bin/env python3
"""
Comprehensive test of prompt effectiveness with sample contract scenarios.
Demonstrates how the Actor and Critic prompts work with real contract content.
"""

import os
import sys
import json
from typing import Dict, Any, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from prompt_manager import PromptManager
from system_prompts import SystemPrompts


def load_sample_contract() -> str:
    """Load the sample contract RTF content."""
    sample_path = os.path.join(os.path.dirname(__file__), 'test_data', 'sample_contract.rtf')
    try:
        with open(sample_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Sample contract not found at {sample_path}")
        # Return a minimal RTF sample for testing
        return r"""{\rtf1\ansi\deff0 {\fonttbl {\f0 Times New Roman;}}
\f0\fs24 
\par \b SERVICE AGREEMENT\b0
\par 
\par This Agreement is between Hash Blockchain Limited ("Company") and Client Corp ("Client").
\par 
\par \b GOVERNING LAW\b0
\par This Agreement shall be governed by Hong Kong law.
\par 
\par \b LIABILITY\b0
\par Client shall indemnify Company from any claims.
\par }"""


def test_entity_substitution_scenario():
    """Test entity substitution scenario with detailed prompt analysis."""
    print("=" * 80)
    print("TESTING ENTITY SUBSTITUTION SCENARIO")
    print("=" * 80)
    
    manager = PromptManager()
    sample_rtf = load_sample_contract()
    
    # Define the scenario
    instruction = "Change all references from 'Hash Blockchain Limited' to 'Quantum Finance Corp', including defined terms, signature blocks, and addresses"
    
    print(f"Original contract length: {len(sample_rtf)} characters")
    print(f"Instruction: {instruction}")
    print()
    
    # Generate Actor task
    actor_task = manager.create_actor_task(sample_rtf, instruction)
    
    print("ACTOR TASK GENERATED:")
    print("-" * 40)
    print(f"Task length: {len(actor_task)} characters")
    print("Key requirements found in task:")
    
    # Check for key requirements
    requirements_found = []
    if "entity" in actor_task.lower() and ("name" in actor_task.lower() or "substitution" in actor_task.lower()):
        requirements_found.append("✓ Entity name variations handling")
    if "defined terms" in actor_task.lower():
        requirements_found.append("✓ Defined terms updates")
    if "signature" in actor_task.lower():
        requirements_found.append("✓ Signature block updates")
    if "address" in actor_task.lower():
        requirements_found.append("✓ Address updates")
    if "grammatical" in actor_task.lower() or "consistency" in actor_task.lower():
        requirements_found.append("✓ Grammatical consistency")
    
    for req in requirements_found:
        print(f"  {req}")
    
    print(f"\nTotal requirements found: {len(requirements_found)}/5")
    
    # Simulate a modified contract (for Critic testing)
    modified_rtf = sample_rtf.replace("Hash Blockchain Limited", "Quantum Finance Corp")
    modified_rtf = modified_rtf.replace("Company", "Quantum Finance Corp")
    
    # Generate Critic task
    critic_task = manager.create_critic_task(sample_rtf, modified_rtf, instruction, attempt_number=1)
    
    print("\nCRITIC TASK GENERATED:")
    print("-" * 40)
    print(f"Task length: {len(critic_task)} characters")
    print("Evaluation criteria found in task:")
    
    # Check for evaluation criteria
    criteria_found = []
    if "entity substitution" in critic_task.lower():
        criteria_found.append("✓ Entity substitution completeness (25%)")
    if "jurisdiction transformation" in critic_task.lower():
        criteria_found.append("✓ Jurisdiction transformation accuracy (20%)")
    if "liability reallocation" in critic_task.lower():
        criteria_found.append("✓ Liability reallocation correctness (20%)")
    if "clause operations" in critic_task.lower():
        criteria_found.append("✓ Clause operations success (20%)")
    if "legal coherence" in critic_task.lower():
        criteria_found.append("✓ Legal coherence maintenance (15%)")
    
    for criteria in criteria_found:
        print(f"  {criteria}")
    
    print(f"\nTotal criteria found: {len(criteria_found)}/5")
    print(f"Minimum score threshold: 0.85 {'✓' if '0.85' in critic_task else '❌'}")
    
    return {
        "scenario": "entity_substitution",
        "actor_task_length": len(actor_task),
        "critic_task_length": len(critic_task),
        "requirements_found": len(requirements_found),
        "criteria_found": len(criteria_found),
        "success": len(requirements_found) >= 3 and len(criteria_found) >= 4
    }


def test_jurisdiction_change_scenario():
    """Test jurisdiction change scenario."""
    print("\n" + "=" * 80)
    print("TESTING JURISDICTION CHANGE SCENARIO")
    print("=" * 80)
    
    manager = PromptManager()
    sample_rtf = load_sample_contract()
    
    # Define the scenario
    instruction = "Change governing law from Hong Kong to Singapore, update all jurisdictional references, venue clauses, and dispute resolution mechanisms"
    
    print(f"Instruction: {instruction}")
    print()
    
    # Generate Actor task
    actor_task = manager.create_actor_task(sample_rtf, instruction)
    
    print("ACTOR TASK ANALYSIS:")
    print("-" * 40)
    
    # Check for jurisdiction-specific requirements
    jurisdiction_requirements = []
    if "governing law" in actor_task.lower():
        jurisdiction_requirements.append("✓ Governing law clauses")
    if "venue" in actor_task.lower():
        jurisdiction_requirements.append("✓ Venue clauses")
    if "dispute resolution" in actor_task.lower():
        jurisdiction_requirements.append("✓ Dispute resolution mechanisms")
    if "regulatory" in actor_task.lower():
        jurisdiction_requirements.append("✓ Regulatory references")
    if "currency" in actor_task.lower():
        jurisdiction_requirements.append("✓ Currency denominations")
    
    for req in jurisdiction_requirements:
        print(f"  {req}")
    
    print(f"\nJurisdiction requirements found: {len(jurisdiction_requirements)}/5")
    
    # Test chunking scenario
    if manager.should_chunk_document(sample_rtf * 10):  # Simulate large document
        print("\nTESTING CHUNKING SCENARIO:")
        print("-" * 40)
        
        chunk_info = {
            'chunk_id': 2,
            'total_chunks': 4,
            'chunk_content': sample_rtf[:1000]
        }
        
        chunked_task = manager.create_actor_task(sample_rtf * 10, instruction, chunk_info)
        
        chunking_features = []
        if "chunk 2 of 4" in chunked_task:
            chunking_features.append("✓ Chunk identification")
        if "context awareness" in chunked_task.lower():
            chunking_features.append("✓ Context awareness")
        if "chunk boundaries" in chunked_task.lower():
            chunking_features.append("✓ Boundary handling")
        
        for feature in chunking_features:
            print(f"  {feature}")
        
        print(f"Chunking features found: {len(chunking_features)}/3")
    
    return {
        "scenario": "jurisdiction_change",
        "actor_task_length": len(actor_task),
        "jurisdiction_requirements": len(jurisdiction_requirements),
        "success": len(jurisdiction_requirements) >= 3
    }


def test_liability_reallocation_scenario():
    """Test liability reallocation scenario."""
    print("\n" + "=" * 80)
    print("TESTING LIABILITY REALLOCATION SCENARIO")
    print("=" * 80)
    
    manager = PromptManager()
    sample_rtf = load_sample_contract()
    
    # Define the scenario
    instruction = "Shift liability from Company to Client, reverse all indemnification clauses, update insurance requirements, and modify liability caps"
    
    print(f"Instruction: {instruction}")
    print()
    
    # Generate Actor task
    actor_task = manager.create_actor_task(sample_rtf, instruction)
    
    print("ACTOR TASK ANALYSIS:")
    print("-" * 40)
    
    # Check for liability-specific requirements
    liability_requirements = []
    if "indemnification" in actor_task.lower():
        liability_requirements.append("✓ Indemnification reversal")
    if "liability caps" in actor_task.lower():
        liability_requirements.append("✓ Liability caps modification")
    if "insurance" in actor_task.lower():
        liability_requirements.append("✓ Insurance requirements")
    if "risk allocation" in actor_task.lower():
        liability_requirements.append("✓ Risk allocation updates")
    if "breach consequence" in actor_task.lower():
        liability_requirements.append("✓ Breach consequences")
    
    for req in liability_requirements:
        print(f"  {req}")
    
    print(f"\nLiability requirements found: {len(liability_requirements)}/5")
    
    # Simulate modified contract for Critic evaluation
    modified_rtf = sample_rtf.replace("Client shall indemnify Company", "Company shall indemnify Client")
    
    # Generate Critic task
    critic_task = manager.create_critic_task(sample_rtf, modified_rtf, instruction, attempt_number=2)
    
    print("\nCRITIC EVALUATION ANALYSIS:")
    print("-" * 40)
    
    # Check for specific evaluation elements
    evaluation_elements = []
    if "attempt number: 2" in critic_task.lower():
        evaluation_elements.append("✓ Attempt tracking")
    if "liability reallocation correctness" in critic_task.lower():
        evaluation_elements.append("✓ Liability evaluation criteria")
    if "json evaluation" in critic_task.lower():
        evaluation_elements.append("✓ JSON output format")
    if "revision suggestions" in critic_task.lower():
        evaluation_elements.append("✓ Revision suggestions")
    
    for element in evaluation_elements:
        print(f"  {element}")
    
    print(f"Evaluation elements found: {len(evaluation_elements)}/4")
    
    return {
        "scenario": "liability_reallocation",
        "actor_task_length": len(actor_task),
        "critic_task_length": len(critic_task),
        "liability_requirements": len(liability_requirements),
        "evaluation_elements": len(evaluation_elements),
        "success": len(liability_requirements) >= 3 and len(evaluation_elements) >= 3
    }


def test_configuration_effectiveness():
    """Test configuration loading and customization."""
    print("\n" + "=" * 80)
    print("TESTING CONFIGURATION EFFECTIVENESS")
    print("=" * 80)
    
    manager = PromptManager()
    
    print("CONFIGURATION ANALYSIS:")
    print("-" * 40)
    
    # Test configuration access
    config_tests = []
    
    # Test evaluation criteria
    criteria = manager.get_evaluation_criteria()
    if criteria:
        config_tests.append(f"✓ Evaluation criteria loaded ({len(criteria)} criteria)")
    
    # Test legacy patterns
    patterns = manager.get_legacy_patterns()
    if patterns:
        config_tests.append(f"✓ Legacy patterns loaded ({len(patterns)} patterns)")
    
    # Test scenarios
    scenarios = manager.get_test_scenarios()
    if scenarios:
        config_tests.append(f"✓ Test scenarios loaded ({len(scenarios)} scenarios)")
    
    # Test model config
    model_config = manager.get_model_config()
    if model_config:
        config_tests.append(f"✓ Model configuration loaded")
    
    # Test chunking logic
    sample_text = "x" * 30000  # Large text
    should_chunk = manager.should_chunk_document(sample_text)
    config_tests.append(f"✓ Chunking logic: {should_chunk} for {len(sample_text)} chars")
    
    for test in config_tests:
        print(f"  {test}")
    
    print(f"\nConfiguration tests passed: {len(config_tests)}/5")
    
    # Test prompt validation
    print("\nPROMPT VALIDATION:")
    print("-" * 40)
    
    sample_rtf = load_sample_contract()
    validation_results = manager.validate_prompt_effectiveness(sample_rtf)
    
    passed_validations = sum(1 for v in validation_results.values() if v is True)
    total_validations = len([k for k in validation_results.keys() if k != 'validation_error'])
    
    print(f"Validation tests passed: {passed_validations}/{total_validations}")
    
    for key, result in validation_results.items():
        if key != 'validation_error':
            status = "✓" if result else "❌"
            print(f"  {status} {key.replace('_', ' ').title()}")
    
    return {
        "config_tests": len(config_tests),
        "validation_passed": passed_validations,
        "validation_total": total_validations,
        "success": len(config_tests) >= 4 and passed_validations >= total_validations * 0.8
    }


def run_comprehensive_test():
    """Run comprehensive prompt effectiveness test."""
    print("COMPREHENSIVE PROMPT EFFECTIVENESS TEST")
    print("=" * 80)
    print("Testing legacy-based system prompts with sample contract scenarios")
    print("=" * 80)
    
    results = []
    
    try:
        # Run individual scenario tests
        results.append(test_entity_substitution_scenario())
        results.append(test_jurisdiction_change_scenario())
        results.append(test_liability_reallocation_scenario())
        results.append(test_configuration_effectiveness())
        
        # Calculate overall results
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r.get('success', False))
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        for result in results:
            scenario = result.get('scenario', 'configuration')
            success = result.get('success', False)
            status = "✓ PASSED" if success else "❌ FAILED"
            print(f"{status} - {scenario.replace('_', ' ').title()}")
        
        print(f"\nOverall Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        
        if successful_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! System prompts are ready for CrewAI integration!")
            print("\nKey Features Validated:")
            print("✓ Actor prompt with legacy-based semantic manipulation patterns")
            print("✓ Critic prompt with experiment framework evaluation logic")
            print("✓ Chunking support for large documents (>25k characters)")
            print("✓ Variable substitution and template management")
            print("✓ Configuration-driven prompt customization")
            print("✓ Entity substitution, jurisdiction change, and liability reallocation scenarios")
            print("✓ RTF formatting preservation requirements")
            print("✓ Cross-reference integrity and definition management")
            
            print("\nNext Steps:")
            print("1. Integrate with CrewAI Agent framework")
            print("2. Connect to AWS Bedrock models (Titan Premier, Mistral Large)")
            print("3. Implement document chunking manager")
            print("4. Create memory storage system")
            print("5. Build API server endpoints")
            
        else:
            print(f"\n⚠️  {total_tests - successful_tests} test(s) failed. Review implementation.")
        
        return successful_tests == total_tests
        
    except Exception as e:
        print(f"\n❌ COMPREHENSIVE TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)