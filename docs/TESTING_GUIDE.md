# Testing Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-02

---

## Table of Contents

1. [Overview](#overview)
2. [Test Suite Structure](#test-suite-structure)
3. [Running Tests](#running-tests)
4. [LEDGAR Evaluation System](#ledgar-evaluation-system)
5. [Test Data Management](#test-data-management)
6. [Writing New Tests](#writing-new-tests)
7. [Interpreting Results](#interpreting-results)
8. [Performance Benchmarking](#performance-benchmarking)
9. [Continuous Testing](#continuous-testing)
10. [Troubleshooting](#troubleshooting)

---

## Overview

Contract-Agent includes a comprehensive testing infrastructure with:

- **14 test files** covering unit, integration, and end-to-end tests
- **LEDGAR evaluation system** for standardized contract processing benchmarks
- **40 detailed test prompts** across 10 sample contracts
- **Performance monitoring** and quality scoring
- **Automated test runners** for CI/CD integration

### Testing Philosophy

1. **Test early, test often** - Catch issues before production
2. **Quality over speed** - Prioritize test coverage and reliability
3. **Real-world scenarios** - Use production-like test data
4. **Automated validation** - Minimize manual verification
5. **Performance tracking** - Monitor regression over time

---

## Test Suite Structure

### Test Files Overview

```
tests/
├── test_api_server.py                    # API endpoint testing
├── test_bedrock.py                       # AWS Bedrock connectivity
├── test_bedrock_connectivity.py          # Bedrock connection validation
├── test_chunking_simple.py               # Document chunking logic
├── test_comprehensive_integration.py     # Full workflow integration
├── test_document_chunking.py             # Chunking algorithms
├── test_end_to_end_integration.py        # E2E scenarios (32KB file)
├── test_integration.py                   # Component integration
├── test_memory_storage.py                # Job storage & cleanup
├── test_performance_evaluation.py        # Performance benchmarks
├── test_prompt_effectiveness.py          # Prompt quality testing
├── test_prompts.py                       # Prompt validation
├── test_real_contract.py                 # Real contract processing
├── test_security_and_reliability.py      # Security & reliability
└── performance_evaluation.py             # Performance metrics collection
```

### Test Categories

| Category | Files | Purpose |
|----------|-------|---------|
| **Unit Tests** | `test_chunking_simple.py`, `test_document_chunking.py` | Individual component testing |
| **Integration Tests** | `test_integration.py`, `test_comprehensive_integration.py` | Multi-component interaction |
| **API Tests** | `test_api_server.py` | Endpoint validation |
| **E2E Tests** | `test_end_to_end_integration.py`, `test_real_contract.py` | Full workflow validation |
| **Infrastructure Tests** | `test_bedrock.py`, `test_memory_storage.py` | External dependencies |
| **Performance Tests** | `test_performance_evaluation.py`, `performance_evaluation.py` | Benchmarking |
| **Quality Tests** | `test_prompt_effectiveness.py`, `test_prompts.py` | Output quality validation |

---

## Running Tests

### Prerequisites

```bash
# Ensure dependencies are installed
pip install pytest pytest-cov pytest-asyncio

# Activate virtual environment
conda activate contract-agent  # or: source venv/bin/activate

# Verify test data exists
ls -lh data/test_data/
```

### Running All Tests

```bash
# Run entire test suite
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=core --cov=infrastructure --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Running Specific Test Files

```bash
# Run API tests only
python -m pytest tests/test_api_server.py -v

# Run integration tests
python -m pytest tests/test_comprehensive_integration.py -v

# Run E2E tests
python -m pytest tests/test_end_to_end_integration.py -v
```

### Running Specific Test Cases

```bash
# Run single test function
python -m pytest tests/test_api_server.py::test_health_endpoint -v

# Run tests matching pattern
python -m pytest tests/ -k "bedrock" -v

# Run tests with specific markers
python -m pytest tests/ -m "slow" -v
```

### Test Output Verbosity

```bash
# Minimal output
python -m pytest tests/ -q

# Normal output
python -m pytest tests/

# Verbose output (recommended)
python -m pytest tests/ -v

# Very verbose (show print statements)
python -m pytest tests/ -vv -s
```

---

## LEDGAR Evaluation System

### Overview

The LEDGAR evaluation system provides standardized benchmarking for contract processing using real legal contracts and comprehensive test prompts.

**Components:**
- **10 sample contracts** (1.8KB to 55KB)
- **40 detailed test prompts** (simple to complex modifications)
- **Automated quality scoring** (0.0 to 1.0)
- **Performance metrics** (processing time, iterations, success rate)

### Running LEDGAR Evaluation

```bash
# Full evaluation with all test cases
python scripts/ledgar_evaluation_FIXED.py

# Expected output:
# 🚀 Starting Contract-Agent LEDGAR Evaluation...
# 📋 Testing 15 scenarios across 3 contracts
# [Progress bar and real-time results]
# ✅ Evaluation complete: evaluation_results/ledgar_evaluation_[timestamp].json
```

### Evaluation Structure

```python
# Evaluation runs 15 test scenarios:
# - 5 scenarios × 3 contract sizes (small, medium, large)

Test Matrix:
┌─────────────────────┬────────┬────────┬────────┐
│ Modification Type   │ Small  │ Medium │ Large  │
├─────────────────────┼────────┼────────┼────────┤
│ Jurisdiction Change │   ✓    │   ✓    │   ✓    │
│ Payment Terms       │   ✓    │   ✓    │   ✓    │
│ Confidentiality     │   ✓    │   ✓    │   ✓    │
│ Indemnification     │   ✓    │   ✓    │   ✓    │
│ Multi-Provision     │   ✓    │   ✓    │   ✓    │
└─────────────────────┴────────┴────────┴────────┘
```

### Test Contracts

Located in `data/test_data/`:

| File | Type | Size | Description |
|------|------|------|-------------|
| `sample_01_converted.txt` | Small | 1.8KB | Basic service agreement |
| `sample_02_converted.txt` | Medium | 2.7KB | KYC/AML service terms |
| `sample_03_converted.txt` | Large | 55KB | Corporate sponsorship agreement |

### Test Prompts

All test prompts documented in `data/test_data/EVALUATION_PROMPTS.md`:

**Complexity Levels:**
- **Level 1-2 (Simple):** Entity changes, jurisdiction shifts
- **Level 3-4 (Intermediate):** Multi-parameter changes, service additions
- **Level 5 (Complex):** Complete regulatory migrations, technology upgrades

**Example Prompts:**

```text
Simple:
"Change jurisdiction from New York to Delaware"

Intermediate:
"Change jurisdiction to Delaware, extend payment terms from 30 to 45 days, 
and reduce late payment penalty from 1.5% to 1.0%"

Complex:
"Change governing law from Swiss law to Singapore law, transfer operations 
to Singapore entity, update regulatory framework from FINMA to MAS, and add 
comprehensive digital asset compliance under Singapore Payment Services Act"
```

### Evaluation Metrics

Each test produces:

```json
{
  "test_id": "sample_01_jurisdiction",
  "contract_file": "sample_01_converted.txt",
  "prompt": "Change jurisdiction...",
  "success": true,
  "processing_time": 52.7,
  "iterations_used": 2,
  "final_score": 0.85,
  "ledgar_score": 0.800,
  "semantic_accuracy": 0.810,
  "model_used": "us.amazon.nova-pro-v1:0"
}
```

### Quality Scoring Criteria

Based on LEDGAR methodology:

| Criteria | Weight | Description |
|----------|--------|-------------|
| **Provision Identification** | 25% | Correctly identifies relevant clauses |
| **Semantic Understanding** | 25% | Understands modification intent |
| **Modification Accuracy** | 20% | Makes precise changes |
| **Legal Coherence** | 15% | Maintains legal validity |
| **Format Preservation** | 15% | Preserves RTF formatting |

**Penalties:**
- Broken cross-reference: -0.2
- Missing entity update: -0.15 per instance
- Incorrect liability direction: -0.2
- Orphaned clause: -0.1 per instance
- RTF corruption: -0.1

---

## Test Data Management

### Test Data Location

```
data/test_data/
├── sample_01_converted.txt          # Basic service agreement (1.8KB)
├── sample_02_converted.txt          # KYC/AML terms (2.7KB)
├── sample_03_converted.txt          # Large sponsorship (55KB)
├── sample_04_converted.txt          # Swiss-Ireland financial
├── sample_05_converted.txt          # Crypto trading HBL
├── sample_06_converted.txt          # XYZ financial product
├── sample_07_converted.txt          # Virtual asset brokerage
├── sample_08_converted.txt          # HBL extended
├── sample_09_converted.txt          # Financial services pt1
├── sample_10_converted.txt          # Financial services pt2
├── EVALUATION_PROMPTS.md            # All test prompts (40 scenarios)
├── CONVERSION_SUMMARY.md            # Data conversion details
└── README.md                        # Test data documentation
```

### Adding New Test Contracts

```bash
# 1. Add contract file to test_data/
cp your_contract.pdf data/test_data/

# 2. Convert to text format if needed
python -c "
import fitz
doc = fitz.open('data/test_data/your_contract.pdf')
text = ''
for page in doc:
    text += page.get_text()
with open('data/test_data/your_contract.txt', 'w') as f:
    f.write(text)
"

# 3. Create test prompts
# Edit data/test_data/EVALUATION_PROMPTS.md

# 4. Add to evaluation script
# Edit ledgar_evaluation_FIXED.py
```

### Test Data Best Practices

1. **Anonymize sensitive data** - Remove real PII, account numbers
2. **Use realistic data** - Test with production-like complexity
3. **Vary contract sizes** - Small (1-5KB), Medium (5-20KB), Large (50KB+)
4. **Document test cases** - Clear descriptions in EVALUATION_PROMPTS.md
5. **Version control** - Track test data changes in git

---

## Writing New Tests

### Test Template (pytest)

```python
import pytest
from core.crew.crew_manager import ContractProcessingCrew

class TestContractProcessing:
    """Test suite for contract processing functionality"""
    
    @pytest.fixture
    def crew_manager(self):
        """Setup crew manager for tests"""
        return ContractProcessingCrew()
    
    def test_simple_jurisdiction_change(self, crew_manager):
        """Test basic jurisdiction modification"""
        # Arrange
        original_text = "This agreement is governed by New York law."
        prompt = "Change jurisdiction from New York to Delaware"
        
        # Act
        result = crew_manager.process_contract(
            original_rtf=original_text,
            user_prompt=prompt,
            job_id="test-001"
        )
        
        # Assert
        assert result.success is True
        assert "Delaware" in result.final_rtf
        assert "New York" not in result.final_rtf
        assert result.final_score >= 0.70
```

### API Test Template

```python
import pytest
import requests

BASE_URL = "http://localhost:5002"

class TestAPIEndpoints:
    """Test suite for API endpoints"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["components"]["bedrock_available"] is True
    
    def test_process_contract_endpoint(self):
        """Test contract processing endpoint"""
        with open("data/test_data/sample_01_converted.txt", "rb") as f:
            files = {"file": f}
            data = {"prompt": "Change jurisdiction to Delaware"}
            
            response = requests.post(
                f"{BASE_URL}/process_contract",
                files=files,
                data=data
            )
        
        assert response.status_code == 202
        job_data = response.json()
        assert "job_id" in job_data
        assert job_data["success"] is True
```

### Integration Test Template

```python
import pytest
import time
from infrastructure.storage.memory_storage import MemoryStorage
from core.crew.crew_manager import ContractProcessingCrew

class TestEndToEndWorkflow:
    """End-to-end workflow testing"""
    
    @pytest.fixture
    def setup_components(self):
        """Setup all required components"""
        storage = MemoryStorage()
        crew = ContractProcessingCrew()
        return storage, crew
    
    def test_full_contract_processing_workflow(self, setup_components):
        """Test complete workflow from submission to result"""
        storage, crew = setup_components
        
        # Read test contract
        with open("data/test_data/sample_01_converted.txt") as f:
            contract_text = f.read()
        
        # Create job
        job_id = "test-workflow-001"
        storage.create_job(
            file_data=contract_text.encode(),
            filename="test_contract.txt",
            user_prompt="Change jurisdiction to Delaware",
            job_id=job_id
        )
        
        # Process contract
        result = crew.process_contract(
            original_rtf=contract_text,
            user_prompt="Change jurisdiction to Delaware",
            job_id=job_id
        )
        
        # Store result
        storage.store_result(job_id, result)
        
        # Retrieve and verify
        job_data = storage.get_job(job_id)
        assert job_data is not None
        assert job_data.status == "completed"
        assert result.success is True
```

### Test Fixtures

```python
import pytest
from infrastructure.aws.bedrock_client import BedrockModelManager

@pytest.fixture(scope="session")
def bedrock_client():
    """Session-wide Bedrock client"""
    return BedrockModelManager()

@pytest.fixture(scope="function")
def sample_contract():
    """Function-scoped test contract"""
    with open("data/test_data/sample_01_converted.txt") as f:
        return f.read()

@pytest.fixture
def mock_job_id():
    """Generate test job ID"""
    return "test-job-12345"
```

---

## Interpreting Results

### Test Execution Results

```bash
# Example pytest output
tests/test_api_server.py::test_health_endpoint PASSED                    [ 10%]
tests/test_api_server.py::test_process_contract PASSED                   [ 20%]
tests/test_bedrock.py::test_connection PASSED                            [ 30%]
tests/test_integration.py::test_full_workflow PASSED                     [ 40%]
...
===================== 10 passed, 0 failed in 45.32s =====================
```

### Understanding Test Failures

**Common Failure Patterns:**

```python
# Assertion Error
AssertionError: assert 0.65 >= 0.70
# Meaning: Quality score below threshold (65% vs 70% minimum)

# Connection Error
botocore.exceptions.NoCredentialsError
# Meaning: AWS credentials not configured

# Timeout Error
TimeoutError: Job processing exceeded 300 seconds
# Meaning: Processing took too long, check chunk_timeout config
```

### LEDGAR Evaluation Results

Example output:

```
📊 LEDGAR Evaluation Results
════════════════════════════════════════════════════════════

Overall Performance:
✅ Success Rate: 100% (15/15 tests passed)
⏱️  Average Processing Time: 52.7 seconds
🎯 Average LEDGAR Score: 0.800
🧠 Average Semantic Accuracy: 0.810
🔄 Average Iterations: 1.8

By Contract Size:
┌──────────┬──────────┬──────────┬──────────┐
│ Size     │ Tests    │ Avg Time │ Avg Score│
├──────────┼──────────┼──────────┼──────────┤
│ Small    │ 5/5      │ 18.2s    │ 0.820    │
│ Medium   │ 5/5      │ 42.5s    │ 0.810    │
│ Large    │ 5/5      │ 97.4s    │ 0.770    │
└──────────┴──────────┴──────────┴──────────┘

By Modification Type:
┌─────────────────────┬──────────┬──────────┐
│ Type                │ Success  │ Avg Score│
├─────────────────────┼──────────┼──────────┤
│ Jurisdiction        │ 3/3      │ 0.850    │
│ Payment Terms       │ 3/3      │ 0.820    │
│ Confidentiality     │ 3/3      │ 0.790    │
│ Indemnification     │ 3/3      │ 0.770    │
│ Multi-Provision     │ 3/3      │ 0.750    │
└─────────────────────┴──────────┴──────────┘

Model Performance:
Primary (Nova Pro):     15 tests, 52.7s avg
Fallback (Mistral):     0 tests (not used)

✅ SYSTEM STATUS: PRODUCTION READY
```

### Performance Thresholds

| Metric | Minimum | Target | Current |
|--------|---------|--------|---------|
| Success Rate | 80% | 95% | 100% ✅ |
| LEDGAR Score | 0.70 | 0.80 | 0.800 ✅ |
| Semantic Accuracy | 0.70 | 0.80 | 0.810 ✅ |
| Avg Processing Time | <180s | <60s | 52.7s ✅ |
| Small Contract | <30s | <20s | 18.2s ✅ |
| Large Contract | <180s | <120s | 97.4s ✅ |

### Quality Score Interpretation

| Score Range | Quality | Action |
|-------------|---------|--------|
| 0.90 - 1.00 | Excellent | Deploy with confidence |
| 0.80 - 0.89 | Good | Deploy after review |
| 0.70 - 0.79 | Acceptable | Review and improve |
| 0.60 - 0.69 | Poor | Fix before deployment |
| < 0.60 | Failing | Do not deploy |

---

## Performance Benchmarking

### Running Performance Tests

```bash
# Run performance evaluation
python tests/performance_evaluation.py

# Run with custom parameters
python tests/performance_evaluation.py --iterations 10 --contracts all

# Run specific performance test
python -m pytest tests/test_performance_evaluation.py -v
```

### Performance Metrics Collected

```python
Performance Metrics:
- Total processing time (seconds)
- Time per iteration (seconds)
- Memory usage (MB)
- API call latency (milliseconds)
- Document size vs processing time correlation
- Throughput (contracts per hour)
- Queue wait time (seconds)
- Thread utilization (%)
```

### Benchmarking Best Practices

1. **Run on consistent hardware** - Same machine for comparisons
2. **Clear cache between runs** - Avoid cached results
3. **Test with real data** - Production-like contracts
4. **Multiple iterations** - Run 5-10 times for average
5. **Monitor resources** - CPU, memory, network during tests

### Performance Regression Detection

```bash
# Run baseline benchmark
python scripts/ledgar_evaluation_FIXED.py > baseline_results.json

# After code changes, run again
python scripts/ledgar_evaluation_FIXED.py > new_results.json

# Compare results
python scripts/compare_benchmarks.py baseline_results.json new_results.json
```

---

## Continuous Testing

### Pre-Commit Testing

```bash
# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running tests before commit..."
python -m pytest tests/ -q
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
EOF

chmod +x .git/hooks/pre-commit
```

### CI/CD Integration

**GitHub Actions Example:**

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: python -m pytest tests/ -v --cov=core --cov=infrastructure
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

### Automated LEDGAR Evaluation

```bash
# Schedule daily evaluation
# Add to crontab: crontab -e
0 2 * * * cd /home/ec2-user/cb/Contract-Agent && python scripts/ledgar_evaluation_FIXED.py
```

---

## Troubleshooting

### Common Test Issues

#### Issue: Tests fail with AWS credentials error

```bash
# Solution: Configure AWS credentials
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

#### Issue: Import errors

```bash
# Solution: Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/ec2-user/cb/Contract-Agent"

# Or install in development mode
pip install -e .
```

#### Issue: Test data not found

```bash
# Solution: Verify test data exists
ls -lh data/test_data/
# If missing, restore from backup or regenerate
```

#### Issue: Tests hang or timeout

```bash
# Solution: Increase timeout
python -m pytest tests/ --timeout=300

# Or check for infinite loops in code
# Add timeout to specific test:
@pytest.mark.timeout(60)
def test_long_running():
    pass
```

#### Issue: Bedrock connection fails

```bash
# Solution: Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Check if models are accessible
python -c "
from infrastructure.aws.bedrock_client import BedrockModelManager
manager = BedrockModelManager()
print(manager.test_connection())
"
```

### Debugging Failed Tests

```bash
# Run with debugging output
python -m pytest tests/ -vv -s

# Run with pdb on failure
python -m pytest tests/ --pdb

# Run specific test with detailed output
python -m pytest tests/test_api_server.py::test_health_endpoint -vv -s
```

### Test Environment Validation

```bash
# Validate test environment
python -c "
import sys
print('Python:', sys.version)

import pytest
print('pytest:', pytest.__version__)

from core.crew.crew_manager import ContractProcessingCrew
print('CrewManager: OK')

from infrastructure.aws.bedrock_client import BedrockModelManager
print('Bedrock: OK')

print('\n✅ Test environment is ready')
"
```

---

## Testing Checklist

### Before Committing Code

- [ ] All tests pass locally: `python -m pytest tests/ -v`
- [ ] Code coverage acceptable: `python -m pytest --cov=core --cov-report=html`
- [ ] LEDGAR evaluation successful: `python scripts/ledgar_evaluation_FIXED.py`
- [ ] No regression in performance metrics
- [ ] New functionality has tests
- [ ] Test data is up to date

### Before Deploying

- [ ] Full test suite passes in staging
- [ ] LEDGAR evaluation meets thresholds (80%+ success, 0.80+ score)
- [ ] Performance benchmarks acceptable
- [ ] Integration tests successful
- [ ] Security tests pass
- [ ] Load testing completed (if applicable)

---

## Quick Reference

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=core --cov=infrastructure --cov-report=html

# Run LEDGAR evaluation
python scripts/ledgar_evaluation_FIXED.py

# Run specific test file
python -m pytest tests/test_api_server.py -v

# Run specific test
python -m pytest tests/test_api_server.py::test_health_endpoint -v

# Run performance tests
python tests/performance_evaluation.py

# Debug failed test
python -m pytest tests/test_api_server.py -vv -s --pdb
```

---

**Last Updated:** 2025-10-02  
**Test Coverage:** 14 test files, 40 evaluation prompts  
**Status:** Comprehensive Test Suite ✅

**Related Documentation:**
- [API_REFERENCE.md](./API_REFERENCE.md) - API testing endpoints
- [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md) - Development setup
- [EVALUATION_METHODOLOGY.md](./EVALUATION_METHODOLOGY.md) - Quality criteria
- [SYSTEM_HANDOFF_GUIDE.md](../SYSTEM_HANDOFF_GUIDE.md) - System overview
