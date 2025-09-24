# Contract-Agent vNext

A modern, microservice-based contract processing application using agentic actor-critic patterns with AWS Bedrock and CrewAI integration.

## Project Structure

```
Contract-Agent/
├── app.py                         # Development Flask server
├── application.py                 # Production/EB Flask server (root level for deployment)
├── app/                           # Flask Application Support (empty - could contain helpers)
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
│   └── prompts/                  # AI Prompt Management
│       ├── __init__.py
│       ├── system_prompts.py     # System prompt definitions
│       └── prompt_manager.py     # Prompt management utilities
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
│   └── test_data/                # Test contract samples
│
├── tests/                        # Test Suite
│   └── ... (various test files)
│
├── docs/                         # Documentation
│   ├── spec/                     # Project specifications
│   └── ... (various documentation)
│
├── scripts/                      # Utility Scripts
│   └── examples/                 # Example usage scripts
│
├── deployment/                   # Deployment Configuration
│   ├── .ebignore                 # Elastic Beanstalk ignore file
│   ├── .elasticbeanstalk/        # EB configuration
│   └── DEPLOYMENT.md             # Deployment documentation
│
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
├── requirements.txt              # Python dependencies
└── README.md                     # This file
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