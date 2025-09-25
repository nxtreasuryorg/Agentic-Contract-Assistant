# Implementation Plan

- [x] 1. Set up AWS Bedrock integration foundation
  - Create BedrockModelManager with Titan Premier and Mistral Large support
  - Implement retry logic and error handling for model calls
  - Test Bedrock connectivity and authentication with sample prompts
  - Add model selection logic based on task complexity
  - _Requirements: 1.2, 1.3, 4.3_

- [x] 2. Create legacy-based system prompts
  - Design Actor system prompt based on nxtChat legacy implementation
  - Design Critic system prompt based on experiment framework evaluation logic
  - Implement prompt templates with variable substitution for contract content
  - Test prompt effectiveness with sample contract text
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 3. Implement document chunking system (based on nxtChat)
  - Create DocumentChunkingManager with RecursiveCharacterTextSplitter (25k chars, 5k overlap)
  - Implement find_instruction_targets function to identify relevant sections from user prompts
  - Add prioritize_chunks function to reorder chunks based on target relevance
  - Test chunking with large contract documents and various instruction types
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 4. Implement CrewAI Actor Agent with chunking support
  - Create ContractActorAgent class with legacy-derived system prompt enhanced for chunking
  - Integrate with Bedrock models for semantic manipulation processing (depends on tasks 1-2)
  - Add document chunking logic for large contracts using DocumentChunkingManager (depends on task 3)
  - Implement parallel chunk processing with rate limiting (max 5 concurrent)
  - Test actor agent with sample counterparty/domicile/liability changes on both small and large documents
  - _Requirements: 2.1, 2.2, 7.4, 7.5_

- [x] 5. Implement CrewAI Critic Agent with chunk-aware evaluation
  - Create ContractCriticAgent class with evaluation system prompt
  - Integrate with Bedrock models for quality assessment across multiple chunks (depends on tasks 1-2)
  - Implement structured scoring against acceptance criteria (0.85 threshold) for reassembled documents
  - Generate specific feedback for actor refinement iterations considering chunk boundaries
  - Test critic evaluation with both chunked and non-chunked document processing
  - _Requirements: 2.3, 2.4, 2.5, 7.4_

- [x] 6. Create CrewAI orchestration and test complete actor-critic workflow
  - Implement ContractProcessingCrew combining Actor and Critic agents (depends on tasks 4-5)
  - Add iteration loop control with 5-attempt maximum and failure handling
  - Implement chunk reassembly validation to ensure no content loss
  - Test complete actor-critic workflow with both small and large sample contracts
  - Validate quality threshold checking and refinement loops across chunked processing
  - _Requirements: 2.3, 2.4, 2.5, 7.4, 7.6_

- [x] 7. Implement memory storage system with chunking support
  - Create MemoryStorage class for temporary file management including chunked data
  - Implement automatic cleanup scheduler for expired jobs and intermediate chunk data
  - Add memory optimization for large document handling and chunk storage
  - Test storage operations with various file sizes including very large contracts
  - _Requirements: 1.4, 4.1, 4.2, 7.4_

- [x] 8. Build Contract-Agent API server with chunking support
  - Create Flask API server with /process_contract, /job_status, /health endpoints
  - Integrate CrewAI workflow with API endpoints supporting chunked document processing
  - Add progress tracking for chunked document processing stages
  - Implement proper HTTP status codes and error responses including chunking failures
  - Test API endpoints with both small and large document uploads
  - _Requirements: 1.1, 1.2, 1.5, 7.4_

- [x] 9. Update nxtApp contract assistant backend integration
  - Modify existing nxtApp/nxtAppCore/contract_assistant.py to integrate with new Contract-Agent microservice
  - Replace legacy model server communication with Contract-Agent API calls
  - Update process_document function to use new chunking-aware endpoints
  - Add support for large document processing with progress tracking
  - Maintain backward compatibility with existing nxtApp authentication and session management
  - _Requirements: 8.1, 8.2_

- [x] 10. Update nxtApp contract assistant frontend interface
  - Enhance existing nxtApp/nxtAppCore/templates/crypto/contract-assistant.html with new Contract-Agent features
  - Update file upload interface to support large document processing with chunking progress tracking
  - Add real-time status polling and progress updates for chunked document processing
  - Improve RTF download functionality to handle results from new Contract-Agent microservice
  - Maintain existing UI/UX design consistency with nxtApp styling and layout
  - _Requirements: 3.1, 3.2, 6.1, 8.3_

- [x] 11. Implement end-to-end integration testing with chunking scenarios
  - Test complete workflow from nxtApp upload to RTF display with both small and large documents
  - Validate error handling and recovery scenarios including chunking failures
  - Test automatic cleanup after processing completion including chunk data cleanup
  - Verify API synchronization between nxtApp and Contract-Agent with chunked processing
  - Test document integrity after chunk reassembly
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.4, 7.6_

- [x] 11.5. Comprehensive Contract-Agent integration testing and validation
  - Create comprehensive integration test suite validating all implemented components (Tasks 1-8)
  - Test complete workflow: Bedrock → System Prompts → Document Chunking → CrewAI Agents → Memory Storage → API Server
  - Validate component interactions: BedrockModelManager ↔ ContractAgents ↔ DocumentChunkingManager ↔ MemoryStorage
  - Test error propagation and recovery across all system layers
  - Validate memory cleanup and resource management under load
  - Test concurrent processing scenarios with multiple jobs and chunked documents
  - Benchmark performance with various document sizes (small, medium, large, very large)
  - Validate API endpoints with real contract processing workflows
  - Test system resilience with network failures, timeout scenarios, and resource constraints
  - Create integration test report documenting system readiness for deployment
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.2, 4.3, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 12. Set up Contract-Agent deployment configuration with chunking parameters
  - Create external configuration files for agents, models, and chunking parameters
  - Set up environment variable management for AWS credentials and chunking limits
  - Add deployment scripts and documentation including chunking configuration
  - Configure memory limits and cleanup policies for chunked data management
  - _Requirements: 4.1, 4.2, 4.3, 7.5_

- [x] 13. Deploy and test Contract-Agent microservice with chunking capabilities
  - Deploy Contract-Agent as separate microservice with chunking support
  - Test deployment connectivity and health endpoints
  - Validate AWS Bedrock integration in deployed environment with rate limiting
  - Test nxtApp-Contract-Agent communication in production setup with large documents
  - Validate chunking performance and memory usage in production environment
  - _Requirements: 4.1, 4.2, 4.3, 7.5_