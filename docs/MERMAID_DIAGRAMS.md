# Contract-Agent Mermaid Diagrams Collection

This document contains all Mermaid diagrams for the Contract-Agent system. Each diagram can be tested individually on https://mermaid.js.org/

## Instructions for Testing
1. Copy each diagram code block below
2. Go to https://mermaid.js.org/
3. Paste the code into the live editor
4. Verify the diagram renders correctly

---

## 1. High-Level System Architecture

```mermaid
graph TB
  subgraph Client (nxtApp)
    U[Upload file + instructions]
    P[Poll job status]
  end

  subgraph Contract-Agent Microservice
    A[Flask API: /process_contract, /job_status, /job_result, /health]
    M[MemoryStorage: jobs, progress, results]
    C[ContractProcessingCrew]
    AC[Actor Agent]
    CR[Critic Agent]
    DCM[DocumentChunkingManager]
    BRM[BedrockModelManager]
  end

  subgraph AWS Bedrock
    T[Titan Text Premier v1:0]
    ML[Mistral Large 2402 v1:0]
  end

  U --> A --> M
  A --> C
  C --> AC
  C --> CR
  C --> DCM
  AC --> BRM
  CR --> BRM
  BRM --> T
  BRM --> ML
  C --> M
  P --> A
```

---

## 2. Actor-Critic Workflow (Single Document)

```mermaid
sequenceDiagram
  participant API as API Server
  participant Crew as ContractProcessingCrew
  participant Actor as Actor Agent
  participant Critic as Critic Agent
  participant Bedrock as AWS Bedrock

  API->>Crew: process_contract(original_rtf, user_prompt)
  loop up to max_iterations (config)
    Crew->>Actor: contract_modification_task(context)
    Actor->>Bedrock: generate modified RTF
    Bedrock-->>Actor: modified RTF

    Crew->>Critic: contract_evaluation_task(context)
    Critic->>Bedrock: evaluate changes
    Bedrock-->>Critic: JSON evaluation

    Critic-->>Crew: overall_score, satisfied?
    alt satisfied == true
      break Success
    else score < threshold
      Crew->>Actor: iterate with feedback context
    end
  end
  Crew-->>API: CrewProcessingResult
```

---

## 3. Chunked Processing Workflow

```mermaid
sequenceDiagram
  participant API as API Server
  participant Crew as ContractProcessingCrew
  participant DCM as DocumentChunkingManager
  participant Worker as Parallel Actor Workers (<=5)
  participant Critic as Critic Agent

  API->>Crew: process_contract(original_rtf, user_prompt)
  Crew->>DCM: should_chunk_document()
  alt needs chunking
    Crew->>DCM: split_document()
    Crew->>DCM: find_instruction_targets(); prioritize_chunks()
    par up to 5 workers
      Crew->>Worker: chunk_processing_task(chunk_i)
      Worker-->>Crew: (processed_chunk_i, changed?)
    end
    Crew->>DCM: reassemble_chunks(processed_chunks)
    Crew->>Critic: contract_evaluation_task(final_rtf)
    Critic-->>Crew: evaluation JSON
    Crew-->>API: CrewProcessingResult
  else no chunking
    Crew->>Crew: fallback to single-document loop
  end
```

---

## 4. Detailed Class Diagram

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

    Flask_API --> ContractProcessingCrew
    Flask_API --> MemoryStorage
    ContractProcessingCrew --> ContractAgents
    ContractProcessingCrew --> ContractTasks
    ContractProcessingCrew --> DocumentChunkingManager
    ContractProcessingCrew --> BedrockModelManager
    ContractTasks --> ContractAgents
```

---

## 5. Data Flow Diagram

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

---

## 6. Job State Machine

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

---

## 7. Actor-Critic Feedback Loop Detail

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

---

## Testing Instructions

To test these diagrams:

1. **Visit https://mermaid.js.org/**
2. **Click "Try it online" or go to the live editor**
3. **Clear the existing content**
4. **Copy and paste each diagram code block above**
5. **Verify the diagram renders correctly**
6. **Check for any syntax errors or rendering issues**

## Common Issues and Solutions

- **Syntax Errors**: Check for missing quotes, brackets, or semicolons
- **Rendering Issues**: Ensure proper spacing and indentation
- **Arrow Connections**: Verify all node references are correctly spelled
- **Subgraph Syntax**: Check subgraph closing braces and proper nesting

If any diagram fails to render, the syntax may need adjustment for the latest Mermaid version.
