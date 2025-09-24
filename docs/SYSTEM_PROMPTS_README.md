# System Prompts Implementation

## Overview

This implementation provides legacy-based system prompts for the Contract Assistant vNext, derived from:
- **nxtChat legacy implementation** - Contract processing patterns and RTF formatting preservation
- **Experiment framework evaluation logic** - Comprehensive quality assessment and scoring criteria
- **CrewAI agent framework requirements** - Task-based agent orchestration and communication

## Files Created

### Core Implementation
- `system_prompts.py` - Main system prompts with Actor and Critic implementations
- `prompt_manager.py` - Configuration-driven prompt management and template system
- `config/prompt_config.json` - Configurable settings for prompts, models, and evaluation criteria

### Test Data and Validation
- `test_data/sample_contract.rtf` - Sample contract for testing prompt effectiveness
- `test_prompts.py` - Basic prompt generation and functionality tests
- `test_prompt_effectiveness.py` - Comprehensive scenario-based testing

## Key Features Implemented

### 1. Actor System Prompt (Legacy-Based)
- **RTF Formatting Preservation** - Maintains exact RTF structure and formatting codes
- **Semantic Manipulation Focus** - Counterparty changes, domicile shifts, liability reallocation
- **Chunking Support** - Handles large documents (>25k characters) with context awareness
- **Entity Transformation** - Complete entity substitution including defined terms and signatures
- **Cross-Reference Integrity** - Updates all internal references and maintains numbering
- **Legal Coherence** - Preserves enforceability and document structure

### 2. Critic System Prompt (Evaluation-Based)
- **5-Criteria Evaluation System** with weighted scoring:
  - Entity Substitution Completeness (25%)
  - Jurisdiction Transformation Accuracy (20%)
  - Liability Reallocation Correctness (20%)
  - Clause Operations Success (20%)
  - Legal Coherence Maintenance (15%)
- **Quality Threshold** - 0.85 minimum acceptable score
- **JSON Output Format** - Structured evaluation with specific feedback
- **Revision Suggestions** - Actionable improvement recommendations
- **Critical Failure Detection** - Automatic penalties for broken references

### 3. Configuration Management
- **External Configuration** - JSON-based settings for easy customization
- **Model Selection** - Primary (Titan Premier) and fallback (Mistral Large) models
- **Chunking Parameters** - Configurable chunk size and overlap settings
- **Evaluation Criteria** - Customizable weights and thresholds
- **Legacy Patterns** - Reference patterns for common manipulation types

### 4. Template System
- **Variable Substitution** - Dynamic prompt generation with context variables
- **Chunking Context** - Automatic chunk information injection
- **Task Descriptions** - Complete CrewAI task generation for both agents
- **Prompt Validation** - Comprehensive testing and effectiveness validation

## Usage Examples

### Basic Actor Prompt
```python
from system_prompts import SystemPrompts

# Get basic Actor prompt
actor_prompt = SystemPrompts.get_actor_prompt()

# Get Actor prompt with chunking
chunked_prompt = SystemPrompts.get_actor_prompt(chunk_id=2, total_chunks=5)
```

### Using Prompt Manager
```python
from prompt_manager import PromptManager

# Initialize with configuration
manager = PromptManager()

# Create Actor task
actor_task = manager.create_actor_task(
    original_rtf="contract content",
    user_prompt="Change entity from ABC to XYZ"
)

# Create Critic task
critic_task = manager.create_critic_task(
    original_rtf="original content",
    modified_rtf="modified content", 
    user_prompt="Change entity from ABC to XYZ",
    attempt_number=1
)
```

### Configuration Customization
```python
# Load custom configuration
manager = PromptManager("custom_config.json")

# Check if document should be chunked
should_chunk = manager.should_chunk_document(document_content)

# Get evaluation criteria
criteria = manager.get_evaluation_criteria()
```

## Test Results

All comprehensive tests passed successfully:

✅ **Entity Substitution Scenario**
- Actor task generation with entity transformation requirements
- Critic evaluation with all 5 criteria and 0.85 threshold

✅ **Jurisdiction Change Scenario**  
- Governing law, venue, and dispute resolution updates
- Chunking support for large documents

✅ **Liability Reallocation Scenario**
- Indemnification reversal and liability cap modifications
- Attempt tracking and revision suggestions

✅ **Configuration Effectiveness**
- External configuration loading and validation
- Prompt template system with variable substitution

## Integration with CrewAI

The system prompts are designed for seamless CrewAI integration:

```python
from crewai import Agent, Task, Crew
from system_prompts import SystemPrompts

# Create Actor Agent
actor_agent = Agent(
    role="Contract Modification Specialist",
    goal="Apply semantic manipulations with precision",
    backstory="Expert in legal document modification",
    llm=bedrock_model,
    system_prompt=SystemPrompts.get_actor_prompt()
)

# Create Critic Agent  
critic_agent = Agent(
    role="Contract Quality Evaluator", 
    goal="Evaluate modifications for accuracy and compliance",
    backstory="Senior legal reviewer with quality assurance expertise",
    llm=bedrock_model,
    system_prompt=SystemPrompts.get_critic_prompt()
)

# Create tasks using prompt manager
actor_task = Task(
    description=SystemPrompts.create_actor_task_description(rtf, prompt),
    agent=actor_agent
)

critic_task = Task(
    description=SystemPrompts.create_critic_task_description(original, modified, prompt),
    agent=critic_agent
)
```

## Next Steps

1. **CrewAI Integration** - Connect prompts to CrewAI Agent framework
2. **Bedrock Integration** - Implement AWS Bedrock model communication
3. **Document Chunking** - Build chunking manager for large documents
4. **Memory Storage** - Implement temporary file management system
5. **API Server** - Create Flask endpoints for nxtApp integration

## Requirements Satisfied

This implementation satisfies the following requirements from the specification:

- **Requirement 2.1** - Actor agent semantic manipulations with legacy patterns
- **Requirement 2.2** - Chunking support for large documents  
- **Requirement 2.5** - Critic evaluation with structured feedback and quality thresholds

The system prompts are now ready for integration with the CrewAI framework and AWS Bedrock models as specified in the Contract Assistant vNext design.