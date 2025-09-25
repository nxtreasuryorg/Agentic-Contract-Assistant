# Contract-Agent: Detailed Code Walkthrough and Architecture Diagrams

## Overview

This document provides a comprehensive code walkthrough of the Contract-Agent vNext system, including detailed Mermaid diagrams for component interactions, data flow, and processing workflows.

## System Components Analysis

### 1. Class Diagram - Component Relationships

```mermaid
classDiagram
    class Flask_API {
        +application: Flask
        +process_contract()
        +job_status()
        +job_result()
        +health()
        +start_processing_thread()
        +extract_text_from_file()
    }
    
    class ContractProcessingCrew {
        -tasks: ContractTasks
        -agents: ContractAgents
        -chunking_manager: DocumentChunkingManager
        -bedrock_manager: BedrockModelManager
        -system_prompts: SystemPrompts
        -config: Dict
        +build_actor_critic_crew()
        +build_chunk_processing_crew()
        +process_contract()
        +_process_single_document()
        +_process_chunks_parallel()
    }
    
    class ContractAgents {
        -_actor_model: str
        -_critic_model: str
        -_actor_llm: LLM
        -_critic_llm: LLM
        +contract_actor(): Agent
        +contract_critic(): Agent
    }
    
    class ContractTasks {
        -agents: ContractAgents
        -system_prompts: SystemPrompts
        +contract_modification_task()
        +contract_evaluation_task()
        +chunk_processing_task()
    }
    
    class DocumentChunkingManager {
        -chunk_size: int
        -chunk_overlap: int
        -text_splitter: RecursiveCharacterTextSplitter
        +should_chunk_document()
        +split_document()
        +find_instruction_targets()
        +prioritize_chunks()
        +reassemble_chunks()
    }
    
    class MemoryStorage {
        -storage: Dict[str, JobData]
        -max_age_hours: int
        -_lock: Lock
        +create_job()
        +get_job()
        +update_job_status()
        +store_result()
        +cleanup_expired_jobs()
    }
    
    class BedrockModelManager {
        -region_name: str
        -max_concurrent_requests: int
        -bedrock_client: boto3.client
        +invoke_model()
        +select_model_for_task()
        +_retry_with_backoff()
    }
    
    class JobData {
        +job_id: str
        +file_data: bytes
        +filename: str
        +user_prompt: str
        +status: str
        +created_at: datetime
        +result: CrewProcessingResult
        +progress: int
    }
    
    class SystemPrompts {
        +get_actor_prompt()
        +get_critic_prompt()
        +get_chunk_prompt()
    }

    Flask_API --> ContractProcessingCrew
    Flask_API --> MemoryStorage
    ContractProcessingCrew --> ContractAgents
    ContractProcessingCrew --> ContractTasks
    ContractProcessingCrew --> DocumentChunkingManager
    ContractProcessingCrew --> BedrockModelManager
    ContractProcessingCrew --> SystemPrompts
    ContractTasks --> ContractAgents
    ContractTasks --> SystemPrompts
    MemoryStorage --> JobData
    ContractAgents --> BedrockModelManager
```

### 2. Data Flow Diagram

```mermaid
flowchart TD
    A[Client Upload] --> B[Flask API /process_contract]
    B --> C[MemoryStorage.create_job]
    C --> D[Job Queue]
    D --> E[Background Processing Thread]
    E --> F[Extract Text from File]
    F --> G{Document Size Check}
    
    G -->|Small Document| H[ContractProcessingCrew.process_contract]
    G -->|Large Document| I[DocumentChunkingManager.should_chunk_document]
    
    I --> J[DocumentChunkingManager.split_document]
    J --> K[DocumentChunkingManager.find_instruction_targets]
    K --> L[DocumentChunkingManager.prioritize_chunks]
    L --> M[Parallel Chunk Processing]
    
    H --> N[Actor-Critic Sequential Loop]
    M --> O[DocumentChunkingManager.reassemble_chunks]
    O --> P[Final Critic Evaluation]
    
    N --> Q{Quality Threshold Met?}
    P --> Q
    Q -->|Yes| R[Success - Store Result]
    Q -->|No| S[Refinement Iteration]
    S --> N
    
    R --> T[MemoryStorage.store_result]
    T --> U[Client Polling /job_status]
    U --> V[Client Retrieval /job_result]
```

### 3. Job State Machine

```mermaid
stateDiagram-v2
    [*] --> queued : create_job()
    queued --> processing : start_processing()
    processing --> evaluating : actor_complete()
    evaluating --> processing : refinement_needed()
    evaluating --> completed : quality_satisfied()
    processing --> failed : error_occurred()
    evaluating --> failed : max_iterations_exceeded()
    completed --> [*] : cleanup()
    failed --> [*] : cleanup()
    
    note right of processing : Actor agent modifying contract
    note right of evaluating : Critic agent scoring quality
    note right of completed : Result available for retrieval
```

### 4. Detailed Chunked Processing Workflow

```mermaid
sequenceDiagram
    participant Client
    participant API as Flask API
    participant Queue as Job Queue
    participant Worker as Background Worker
    participant Crew as ContractProcessingCrew
    participant DCM as DocumentChunkingManager
    participant Pool as ThreadPool (max 5)
    participant Actor as Actor Agents
    participant Critic as Critic Agent
    participant Storage as MemoryStorage
    
    Client->>API: POST /process_contract (large file)
    API->>Storage: create_job()
    Storage-->>API: job_id
    API-->>Client: 202 Accepted {job_id}
    API->>Queue: enqueue job
    
    Queue->>Worker: get job from queue
    Worker->>Storage: update_job_status("processing", 10)
    Worker->>Worker: extract_text_from_file()
    Worker->>Storage: update_job_status("processing", 30)
    
    Worker->>Crew: process_contract()
    Crew->>DCM: should_chunk_document()
    DCM-->>Crew: true (large document)
    
    Crew->>DCM: split_document()
    DCM-->>Crew: chunks[]
    Crew->>DCM: find_instruction_targets()
    DCM-->>Crew: target_sections[]
    Crew->>DCM: prioritize_chunks()
    DCM-->>Crew: prioritized_chunks[]
    
    Crew->>Pool: submit chunk tasks (parallel, max 5)
    
    par Chunk 1
        Pool->>Actor: chunk_processing_task(chunk_1)
        Actor-->>Pool: processed_chunk_1
    and Chunk 2
        Pool->>Actor: chunk_processing_task(chunk_2)
        Actor-->>Pool: processed_chunk_2
    and Chunk N
        Pool->>Actor: chunk_processing_task(chunk_n)
        Actor-->>Pool: processed_chunk_n
    end
    
    Pool-->>Crew: all_processed_chunks[]
    Crew->>DCM: reassemble_chunks()
    DCM-->>Crew: final_document
    
    Crew->>Critic: contract_evaluation_task()
    Critic-->>Crew: evaluation_json
    Crew-->>Worker: CrewProcessingResult
    
    Worker->>Storage: store_result()
    Worker->>Storage: update_job_status("completed", 100)
    
    loop Client Polling
        Client->>API: GET /job_status/{job_id}
        API->>Storage: get_job()
        Storage-->>API: job_data
        API-->>Client: status_response
    end
    
    Client->>API: GET /job_result/{job_id}
    API->>Storage: get_result()
    Storage-->>API: result_data
    API-->>Client: final_result
```

### 5. Actor-Critic Feedback Loop Detail

```mermaid
flowchart TD
    A[Start Processing] --> B[Load Configuration]
    B --> C[Initialize Context]
    C --> D[Actor: Generate Modified RTF]
    D --> E[Critic: Evaluate Modifications]
    E --> F{Overall Score >= 0.85?}
    
    F -->|Yes| G[Success: Return Result]
    F -->|No| H{Iteration < Max?}
    
    H -->|Yes| I[Update Context with Feedback]
    I --> J[Increment Attempt Counter]
    J --> D
    
    H -->|No| K[Failure: Return Error Report]
    
    subgraph "Evaluation Criteria"
        L[Entity Substitution 25%]
        M[Jurisdiction Transform 20%]
        N[Liability Reallocation 20%]
        O[Clause Operations 20%]
        P[Legal Coherence 15%]
    end
    
    E --> L
    E --> M
    E --> N
    E --> O
    E --> P
```

## Code Analysis Summary

### Key Findings from Code Walkthrough:

1. **Modular Architecture**: Clean separation between API layer, orchestration, agents, and infrastructure
2. **Configurable Design**: All critical parameters externalized in config/prompt_config.json
3. **Robust Error Handling**: Comprehensive exception handling and graceful degradation
4. **Scalable Processing**: Parallel chunk processing with rate limiting (max 5 workers)
5. **Memory Management**: Thread-safe in-memory storage with configurable cleanup policies

### Critical Code Paths:

1. **Main Processing Flow**: `application.py` → `crew_manager.py` → `agents.py` → `bedrock_client.py`
2. **Chunking Pipeline**: `document_chunking.py` → parallel processing → reassembly
3. **Quality Control**: Actor-Critic loop with configurable thresholds and iteration limits
4. **Job Management**: `memory_storage.py` with thread-safe operations and automatic cleanup

### Configuration Dependencies:

- AWS Bedrock models (Titan Premier, Mistral Large)
- Environment variables for authentication and limits
- JSON configuration for prompts and evaluation criteria
- Dynamic chunk size and overlap settings

### Performance Considerations:

- Maximum file size: 200MB
- Chunk size: 25,000 characters with 5,000 overlap
- Concurrent requests: Limited to 5 (Bedrock rate limits)
- Processing timeout: 180 seconds per request
- Memory cleanup: Session-based or scheduled (48-hour retention)
