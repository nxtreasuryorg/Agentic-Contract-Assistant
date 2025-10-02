# Contract-Agent vNext

A modern, microservice-based contract processing application using agentic actor-critic patterns with AWS Bedrock and CrewAI integration.

## Project Structure

```
Contract-Agent/
├── app.py                         # Development Flask server
├── application.py                 # Production/EB Flask server (root level for deployment)
├── README.md                      # Project overview (this file)
├── SYSTEM_HANDOFF_GUIDE.md        # Operational guide and system status
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (DO NOT COMMIT!)
├── .gitignore                     # Git ignore rules
│
├── app/                           # Flask Application Support
│   └── __init__.py               # App package initialization
│
├── core/                          # Business Logic & Domain
│   ├── __init__.py               # Core package initialization
│   ├── types.py                  # Shared data types and models
│   ├── agents/                   # CrewAI Agent Definitions
│   │   ├── __init__.py
│   │   ├── agents.py             # Contract processing agents
│   │   └── tasks.py              # CrewAI task definitions
│   ├── crew/                     # CrewAI Orchestration
│   │   ├── __init__.py
│   │   └── crew_manager.py       # Actor-critic workflow manager
│   ├── document_processing/      # Document Processing Logic
│   │   ├── __init__.py
│   │   ├── document_chunking.py  # Large document chunking
│   │   └── pdf_utils.py          # PDF processing utilities
│   ├── prompts/                  # AI Prompt Management
│   │   ├── __init__.py
│   │   ├── system_prompts.py     # System prompt definitions
│   │   └── prompt_manager.py     # Prompt management utilities
│   └── utils/                    # Core Utilities
│       └── monitoring.py         # Performance monitoring
│
├── infrastructure/               # External Integrations
│   ├── __init__.py               # Infrastructure package initialization
│   ├── aws/                      # AWS Service Integrations
│   │   ├── __init__.py
│   │   └── bedrock_client.py     # AWS Bedrock client
│   └── storage/                  # Storage Systems
│       ├── __init__.py
│       └── memory_storage.py     # In-memory job storage
│
├── config/                       # Configuration Files
│   └── prompt_config.json        # AI prompt configuration
│
├── data/                         # Runtime Data Directories
│   ├── uploads/                  # Uploaded contract files
│   ├── generated/                # Generated RTF outputs
│   ├── temp/                     # Temporary processing files
│   └── test_data/                # Test contract samples (10 samples)
│       ├── sample_*.txt          # Test contracts (1.8KB - 55KB)
│       ├── EVALUATION_PROMPTS.md # 40 test scenarios
│       └── README.md             # Test data documentation
│
├── tests/                        # Test Suite (14 test files)
│   ├── test_api_server.py        # API endpoint testing
│   ├── test_bedrock.py           # AWS Bedrock connectivity
│   ├── test_comprehensive_integration.py  # Full workflow tests
│   ├── test_document_chunking.py # Chunking algorithms
│   ├── test_end_to_end_integration.py     # E2E scenarios
│   ├── test_memory_storage.py    # Job storage tests
│   ├── test_performance_evaluation.py     # Performance benchmarks
│   └── ... (additional test files)
│
├── scripts/                      # Utility Scripts
│   ├── ledgar_evaluation_FIXED.py  # LEDGAR benchmark evaluation
│   ├── simple_test.py            # Quick contract processing test
│   ├── test_fixed_version.py     # Fixed version testing
│   └── examples/                 # Example usage scripts
│
├── docs/                         # Documentation
│   ├── API_REFERENCE.md          # Complete API documentation
│   ├── ENVIRONMENT_SETUP.md      # Environment configuration
│   ├── LOCAL_DEVELOPMENT.md      # Developer setup guide
│   ├── TESTING_GUIDE.md          # Testing and LEDGAR evaluation
│   ├── CICD_DEVOPS_GUIDE.md      # CI/CD and deployment
│   ├── TROUBLESHOOTING.md        # Common issues and solutions
│   ├── SECURITY.md               # Security best practices
│   ├── DOCUMENTATION_INDEX.md    # Documentation index
│   ├── ACTOR_CRITIC_ARCHITECTURE.md  # Architecture details
│   ├── EVALUATION_METHODOLOGY.md # Quality scoring methodology
│   ├── MERMAID_DIAGRAMS.md       # System diagrams
│   ├── diagrams/                 # Mermaid diagram files
│   ├── png/                      # Generated PNG diagrams
│   └── specs/                    # Project specifications
│
├── deployment/                   # Deployment Configuration
│   ├── DEPLOYMENT.md             # Deployment documentation
│   └── ... (EB configuration files)
│
├── evaluation_results/           # Test Results
│   ├── MODEL_COMPARISON_SUMMARY.md
│   ├── nova-pro/                 # Nova Pro evaluation results
│   └── mistral-large/            # Mistral Large evaluation results
│
├── .ebextensions/                # Elastic Beanstalk extensions
├── .elasticbeanstalk/            # EB configuration
└── .ebignore                     # EB deployment exclusions
```

## Key Features

- **Actor-Critic Pattern**: Advanced AI workflow for contract processing
- **Large Document Support**: Intelligent chunking for contracts up to 200MB
- **AWS Bedrock Integration**: Titan Premier and Mistral Large models
- **Enhanced Timeouts**: Optimized for large contract processing (up to 2 hours)
- **Microservice Architecture**: Clean separation of concerns
- **Production Ready**: Deployed on AWS Elastic Beanstalk

## Quick Start

### Development
```bash
python app.py
```

### Production
```bash
cd deployment
eb deploy
```

## API Endpoints

- `GET /health` - Health check
- `POST /process_contract` - Submit contract for processing
- `GET /job_status/{job_id}` - Check processing status
- `GET /job_result/{job_id}` - Get processing results

## Architecture Benefits

1. **Modular Design**: Clear separation between application, business logic, and infrastructure
2. **Testable**: Business logic isolated from external dependencies
3. **Scalable**: Microservice-ready architecture
4. **Maintainable**: Well-organized codebase with clear responsibilities
5. **Production Ready**: Proper configuration management and deployment setup