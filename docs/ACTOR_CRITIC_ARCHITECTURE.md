# Contract-Agent vNext: CrewAI Actor–Critic Architecture

## Abstract

This document presents the architecture of the Contract-Agent vNext system that implements an agentic actor–critic workflow for legal contract manipulation. The system integrates CrewAI for agent orchestration and AWS Bedrock models for language generation. We formalize the design choices—sequential actor–critic refinement with quality thresholds, chunk-based parallelism for large documents, and memory-backed job management—and explain the rationale with respect to correctness, scalability, and operational constraints.


## System Context and Goals

- Purpose: Given a contract (PDF/RTF/TXT) and a user instruction (e.g., counterparty substitution, governing-law change), produce a semantically correct, RTF-preserving revision.
- Constraints: Large documents (up to 200MB), strict formatting preservation, deterministic application of multi-step semantic edits, and measurable quality gates.
- Outcome: A final RTF that meets or exceeds a quality threshold evaluated by a critic agent; otherwise, a failure report with actionable diagnostics.


## High-Level Architecture

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


## Actor–Critic Workflow (Single-Document Path)

The orchestration is encapsulated in an agent orchestrator within the microservice. For non-chunked documents, the system executes a sequential loop of Actor (modify) followed by Critic (evaluate). The loop terminates early when the Critic’s evaluation satisfies the acceptance criteria.

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

Rationale:
- Sequential actor–critic loops improve correctness through bounded refinement while preventing unbounded cost/latency.
- Explicit JSON evaluation from the Critic ensures programmatic termination conditions and auditability.


## Chunked Workflow (Large Documents)

For large contracts, chunking is indispensable for tractability and model token limits. The manager dynamically decides based on content length, then applies chunk-level actor processing with prioritized parallelism, reassembles, and finally runs a global evaluation.

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

Rationale:
- Chunking reduces cognitive load per generation and respects model context windows while maintaining global coherence through overlap and prioritized ordering.
- Parallelization trades latency for bounded concurrency, respecting external throughput constraints and cost.


## Agents, Tasks, and Prompts

- Agents:
  - Actor: a precise legal editor responsible for applying semantic manipulations while preserving RTF fidelity.
  - Critic: a conservative evaluator that delivers structured, criterion-based assessments and actionable feedback.

- Tasks:
  - Modification task: enforces formatting-preservation constraints and applies requested changes at document or chunk granularity.
  - Evaluation task: computes weighted scores across criteria and determines satisfaction against a minimum threshold.
  - Chunk task: constrains scope to specific segments with boundary awareness and explicit change signals.

- Prompts:
  - Actor prompts encode invariants (no structural corruption, exact formatting preservation) and manipulation taxonomies (entity substitution, jurisdiction shifts, liability reallocations, clause operations).
  - Critic prompts encode evaluation dimensions, penalties, and a machine-readable output schema.

Rationale:
- Separating generation and evaluation yields a measurable control loop and facilitates diagnostics and governance.
- Centralized prompts provide a stable policy surface for tuning without code changes.


## Orchestration, Storage, and API Surface

- Orchestration: coordinates actor–critic cycles, chunk workers, iteration control, and quality thresholds.
- Storage: maintains thread-safe, in-memory job state (files, progress, results) with optional immediate cleanup after retrieval and operational statistics.
- API Surface:
  - `POST /process_contract`: enqueue a job with file and prompt, returning a `job_id` (202 Accepted).
  - `GET /job_status/<job_id>`: report progress, state, and partial metrics.
  - `GET /job_result/<job_id>`: return final artifact and metrics; may trigger session-based cleanup.
  - `GET /health`: report component readiness and queue size.

Rationale:
- Queue + background worker decouples ingress latency from processing duration, critical for large contracts.
- Memory-backed storage simplifies session locality and avoids premature persistence while still enabling observability.


## AWS Bedrock Integration

The platform integrates with AWS Bedrock for model invocation, token accounting, retry with exponential backoff, and model selection heuristics. Primary/fallback routing (e.g., Titan Premier vs. Mistral Large) balances accuracy, cost, and availability. While agents are configured declaratively, the provider layer offers policy control and observability for reliability engineering.

Rationale:
- Abstracting provider concerns isolates retries, throttling, and topology from agent logic, enabling policy evolution without refactoring the actor–critic core.


## Quality Gate, Termination, and Parsing

- Thresholding: minimum acceptable quality and maximum iteration counts are externalized in configuration and enforced by the orchestrator.
- Parsing Strategy: outputs are robustly parsed to separate the Actor’s RTF artifact from the Critic’s machine-readable evaluation, even when interleaved with free text.

Rationale:
- Programmable gates are essential for deterministic service-level behavior, especially under variable model outputs.


## Error Handling and Resilience

- API-level errors: semantic error bodies with appropriate HTTP codes ensure predictable integration semantics.
- Agent failures: captured at orchestration boundaries with clear failure states; background processing safeguards queue continuity.
- Chunk timeouts/failures: degraded-mode behavior returns original segments on failure or timeout, preferring availability over partial corruption.
- Provider failures: retry and fallback policies maintain graceful performance under throttling or outages; health signals expose component readiness.

Rationale:
- Prefer graceful degradation and traceability over silent corruption in legal documents.


## Configuration and Extensibility

- Environment-scoped settings control model selection, concurrency, and retry budgets.
- Externalized configuration centralizes quality gates, evaluation weights, and penalties.
- Dependency injection eliminates hardcoding of tools and enables testability and policy swaps.

Rationale:
- Externalizing control knobs enables A/B testing and environment-specific tuning without code changes.


## Security and Operations

- Secrets are not embedded; credentials are provided via secure environment configuration.
- Size limits and timeouts are tuned for large contracts while preserving API protections and concurrency caps.
- Memory cleanup policies (session-based vs. scheduled) control lifecycle costs.


## Limitations and Future Directions

- Tightened Bedrock coupling: While agents use CrewAI’s `LLM` interface, migrating to explicit `BedrockModelManager` invocation per task may yield tighter control over telemetry and retry policies.
- Overlap-aware reassembly: Current reassembly is concatenation; enhancing with overlap reconciliation and diff-based stitching would reduce boundary artifacts.
- Learned prioritization: Replace heuristic chunk prioritization with learned relevance models and retrieval-augmented context windows where applicable.
- Streaming deltas: Expose intermediate actor iterations for streaming UI and human-in-the-loop corrections.

## Appendix: Acceptance Criteria (Critic)

The Critic conducts a structured, weighted assessment with conservative scoring and explicit failure penalties.

- Weights (overall score is a weighted sum):
  - Entity substitution completeness — 25%
  - Jurisdiction transformation accuracy — 20%
  - Liability reallocation correctness — 20%
  - Clause operations success — 20%
  - Legal coherence maintenance — 15%

- Minimum acceptable overall score: 0.85 (85%).

- Critical failure triggers (automatic deductions):
  - Any broken cross-reference: −0.20
  - Missing entity updates: −0.15 per instance
  - Incorrect liability direction: −0.20
  - Orphaned clauses or definitions: −0.10 per instance
  - RTF formatting corruption: −0.10

- Evaluation process:
  1. Compare original and modified documents systematically.
  2. Verify each instruction was implemented completely and correctly.
  3. Detect unintended changes or omissions.
  4. Assess legal validity and enforceability post-modification.
  5. Check formatting and structural integrity, including cross-references and numbering.

- Output format (machine-readable JSON):

```json
{
  "overall_score": 0.92,
  "criteria_scores": {
    "entity_substitution": 0.95,
    "jurisdiction_transformation": 0.88,
    "liability_reallocation": 0.90,
    "clause_operations": 0.93,
    "legal_coherence": 0.91
  },
  "satisfied": true,
  "unmet_criteria": [],
  "feedback": "Targeted, actionable guidance for any deficiencies",
  "attempt_number": 2,
  "revision_suggestions": [
    {
      "reason": "why change is needed",
      "target_section": "specific location identifier",
      "action": "add/delete/replace/edit",
      "instruction": "precise edit instruction",
      "text_to_insert": "RTF snippet if applicable",
      "constraints": ["maintain numbering", "update cross-references"]
    }
  ],
  "red_flags": ["potential legal risks introduced by modifications"]
}
```

- Constraints on evaluation:
  - Base scoring strictly on provided instructions and acceptance criteria.
  - Provide specific evidence for scoring and feedback.
  - If uncertain, score conservatively and mark as failed with reasons.

Satisfaction terminates the loop early; sub-threshold outcomes trigger bounded refinement or a structured failure report with actionable feedback.
