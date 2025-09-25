# Contract-Agent Documentation Index

This document provides a complete index of all documentation for the Contract-Agent vNext system.

## Architecture & Design Documents

### Core Architecture
- **[ACTOR_CRITIC_ARCHITECTURE.md](./ACTOR_CRITIC_ARCHITECTURE.md)** - Main architecture document with system overview, actor-critic workflow, and acceptance criteria
- **[DETAILED_CODE_WALKTHROUGH.md](./DETAILED_CODE_WALKTHROUGH.md)** - Comprehensive code analysis with detailed component interactions
- **[MERMAID_DIAGRAMS.md](./MERMAID_DIAGRAMS.md)** - Collection of all Mermaid diagrams for system visualization

### Implementation Details
- **[EVALUATION_METHODOLOGY.md](./EVALUATION_METHODOLOGY.md)** - Formal evaluation criteria and scoring methodology
- **[API_INTEGRATION_GUIDE.md](./API_INTEGRATION_GUIDE.md)** - Conceptual API integration patterns and lifecycle
- **[CHUNKING_IMPLEMENTATION_SUMMARY.md](./CHUNKING_IMPLEMENTATION_SUMMARY.md)** - Document chunking strategy and implementation
- **[SYSTEM_PROMPTS_README.md](./SYSTEM_PROMPTS_README.md)** - System prompts documentation and governance

## Project Root Documentation
- **[README.md](../README.md)** - Project overview, structure, and quick start guide

## Configuration References
- **[config/prompt_config.json](../config/prompt_config.json)** - Master configuration file with:
  - Evaluation criteria weights and penalties
  - Model settings and parameters
  - Test scenarios and patterns
  - Legacy manipulation patterns

## Key Implementation Files Reference

### API Layer
- `application.py` - Production Flask server with AWS EB compatibility
- `app.py` - Development Flask server

### Core Business Logic
- `core/crew/crew_manager.py` - Main orchestration and actor-critic workflow
- `core/agents/agents.py` - CrewAI agent definitions (Actor & Critic)
- `core/agents/tasks.py` - Task definitions for contract processing workflow
- `core/document_processing/document_chunking.py` - Large document chunking logic
- `core/prompts/system_prompts.py` - AI prompt definitions and management

### Infrastructure
- `infrastructure/aws/bedrock_client.py` - AWS Bedrock integration and model management
- `infrastructure/storage/memory_storage.py` - In-memory job storage with thread safety

### Configuration & Types
- `config/prompt_config.json` - Master configuration file
- `core/types.py` - Shared data types and models

## Architecture Diagrams Summary

The system includes the following Mermaid diagrams (all testable on https://mermaid.js.org/):

1. **High-Level System Architecture** - Shows client, microservice, and AWS Bedrock interactions
2. **Actor-Critic Workflow (Single Document)** - Sequential processing for small documents  
3. **Chunked Processing Workflow** - Parallel processing for large documents
4. **Detailed Class Diagram** - Component relationships and dependencies
5. **Data Flow Diagram** - End-to-end data movement through the system
6. **Job State Machine** - Job lifecycle and status transitions
7. **Actor-Critic Feedback Loop** - Detailed refinement process with evaluation criteria

## Key Configuration Parameters

From `config/prompt_config.json`:

### Document Processing
- **Max chunk size**: 25,000 characters
- **Chunk overlap**: 5,000 characters  
- **Max iterations**: 5 per document
- **Quality threshold**: 0.85 (85%)

### Evaluation Criteria (Weights)
- **Entity substitution**: 25%
- **Jurisdiction transformation**: 20%
- **Liability reallocation**: 20%
- **Clause operations**: 20%
- **Legal coherence**: 15%

### Critical Failure Penalties
- **Broken cross-reference**: -0.2
- **Missing entity update**: -0.15 per instance
- **Incorrect liability direction**: -0.2
- **Orphaned clause**: -0.1 per instance
- **RTF formatting corruption**: -0.1

### AWS Bedrock Models
- **Primary**: amazon.titan-text-premier-v1:0
- **Fallback**: mistral.mistral-large-2402-v1:0
- **Max tokens**: 4,000
- **Temperature**: 0.1

## API Contract

### Endpoints
- `GET /health` - Health check and component status
- `POST /process_contract` - Submit contract processing job (multipart form)
- `GET /job_status/{job_id}` - Poll job progress and status
- `GET /job_result/{job_id}` - Retrieve final results

### Error Response Format
```json
{
  "success": false,
  "error": "Human-readable error message",
  "code": "MACHINE_READABLE_CODE",
  "details": { "additional": "context" }
}
```

### Job States
- `queued` → `processing` → `evaluating` → `completed` | `failed`

## System Capabilities

### Document Processing
- **File formats**: PDF, RTF, TXT
- **Maximum size**: 200MB
- **Processing timeout**: 180 seconds per request
- **Concurrent workers**: Max 5 (Bedrock rate limits)

### Semantic Manipulations
- **Entity substitution** (counterparty name changes)
- **Jurisdiction transformation** (governing law changes)
- **Liability reallocation** (responsibility shifts)  
- **Clause operations** (add/delete/modify clauses)

### Quality Assurance
- **Bounded refinement**: Up to 5 iterations per document
- **Structured evaluation**: JSON-formatted scoring with detailed feedback
- **RTF integrity**: Strict formatting preservation requirements
- **Legal coherence**: Enforceability and consistency validation

## Development and Testing

### Test Scenarios (from config)
1. **Counterparty Substitution**: Entity name replacement throughout document
2. **Domicile Shift**: Jurisdiction change from Hong Kong to Singapore
3. **Liability Reallocation**: Shift responsibility with indemnification reversal

### Memory Management
- **Storage**: Thread-safe in-memory job storage
- **Cleanup**: Session-based (immediate) or scheduled (48-hour retention)
- **Concurrency**: Full thread safety for concurrent job processing

## Next Steps for Documentation

Consider adding these documents for complete coverage:
- **DEPLOYMENT_GUIDE.md** - AWS Elastic Beanstalk deployment procedures
- **TESTING_STRATEGY.md** - Comprehensive testing approach and test data
- **TROUBLESHOOTING.md** - Common issues and solutions
- **PERFORMANCE_TUNING.md** - Optimization guidelines for large contracts
- **SECURITY_COMPLIANCE.md** - Security measures and compliance considerations
