# Troubleshooting Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-02

---

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Configuration Problems](#configuration-problems)
4. [AWS & Bedrock Issues](#aws--bedrock-issues)
5. [Application Errors](#application-errors)
6. [Performance Issues](#performance-issues)
7. [Deployment Problems](#deployment-problems)
8. [Data & Storage Issues](#data--storage-issues)
9. [Testing Failures](#testing-failures)
10. [Getting Help](#getting-help)

---

## Quick Diagnostics

### Health Check Script

Run this comprehensive diagnostic script:

```bash
#!/bin/bash
# diagnose.sh - Quick system diagnostics

echo "=== Contract-Agent Diagnostics ==="
echo ""

# Python version
echo "Python Version:"
python --version
echo ""

# Environment
echo "Virtual Environment:"
which python
echo ""

# Dependencies
echo "Critical Dependencies:"
pip list | grep -E "Flask|boto3|crewai|langchain" || echo "❌ Dependencies missing"
echo ""

# AWS Configuration
echo "AWS Configuration:"
aws sts get-caller-identity 2>&1 || echo "❌ AWS credentials not configured"
echo ""

# Environment Variables
echo "Environment Variables:"
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print(f'AWS_REGION_NAME: {os.getenv(\"AWS_REGION_NAME\") or \"❌ Not set\"}')
print(f'CONTRACT_PRIMARY_MODEL: {os.getenv(\"CONTRACT_PRIMARY_MODEL\") or \"❌ Not set\"}')
print(f'PORT: {os.getenv(\"PORT\", \"5002\")}')
"
echo ""

# File Permissions
echo "Data Directories:"
ls -ld data/uploads data/generated data/temp 2>&1 || echo "❌ Data directories missing"
echo ""

# Server Status
echo "Server Status:"
curl -s http://localhost:5002/health | jq '.status' 2>&1 || echo "❌ Server not running"
echo ""

echo "=== Diagnostics Complete ==="
```

Save and run:
```bash
chmod +x diagnose.sh
./diagnose.sh
```

---

## Installation Issues

### Issue: pip install fails with dependency conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages
ERROR: Cannot install crewai and langchain due to conflicting dependencies
```

**Solutions:**

```bash
# Solution 1: Use fresh virtual environment
conda deactivate
conda remove -n contract-agent --all
conda create -n contract-agent python=3.11
conda activate contract-agent
pip install -r requirements.txt

# Solution 2: Install with --no-deps for problematic packages
pip install --no-deps crewai
pip install -r requirements.txt

# Solution 3: Use specific versions
pip install crewai==0.40.0 langchain==0.1.0
```

---

### Issue: Python version mismatch

**Symptoms:**
```
python: command not found
or
Python 2.7.18 (expected 3.11+)
```

**Solutions:**

```bash
# macOS/Linux
# Install Python 3.11
sudo apt-get install python3.11  # Ubuntu/Debian
brew install python@3.11         # macOS

# Update alternatives
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Verify
python --version
```

---

### Issue: Permission denied errors

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages'
```

**Solutions:**

```bash
# Use --user flag
pip install --user -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Fix permissions
sudo chown -R $USER:$USER /path/to/Contract-Agent
```

---

## Configuration Problems

### Issue: Environment variables not loading

**Symptoms:**
```
Configuration validation failed:
  - AWS_REGION_NAME not set
  - CONTRACT_PRIMARY_MODEL not set
```

**Diagnostic:**

```bash
# Check if .env file exists
ls -la .env

# Check file contents (sanitized)
cat .env | grep -v SECRET | grep -v KEY

# Test loading
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Loaded:', os.getenv('AWS_REGION_NAME'))
"
```

**Solutions:**

```bash
# Solution 1: Create .env file
cp .env.example .env
# Edit with your values

# Solution 2: Export environment variables
export AWS_REGION_NAME=us-east-1
export CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0

# Solution 3: Use AWS CLI configuration
aws configure
# Credentials will be read from ~/.aws/credentials

# Solution 4: Verify .env location
# Must be in project root, same directory as app.py
pwd  # Should be /home/ec2-user/cb/Contract-Agent
ls .env
```

---

### Issue: Wrong AWS region or model

**Symptoms:**
```
botocore.exceptions.ClientError: Model 'amazon.nova-pro-v1:0' not found in region
```

**Solutions:**

```bash
# Check available models in your region
aws bedrock list-foundation-models --region us-east-1 \
  | jq '.modelSummaries[] | select(.modelId | contains("nova"))'

# Update region in .env
AWS_REGION_NAME=us-east-1  # Change to your region

# Verify Bedrock availability
aws bedrock list-foundation-models --region us-east-1 --query 'modelSummaries[].modelId'
```

**Supported Regions:**
- `us-east-1` - US East (N. Virginia) ✅ Recommended
- `us-west-2` - US West (Oregon)
- `eu-west-1` - Europe (Ireland)

---

## AWS & Bedrock Issues

### Issue: AWS credentials not found

**Symptoms:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Diagnostic:**

```bash
# Test AWS credentials
aws sts get-caller-identity

# Check credential files
cat ~/.aws/credentials
cat ~/.aws/config
```

**Solutions:**

```bash
# Solution 1: Configure AWS CLI
aws configure
# Enter your credentials when prompted

# Solution 2: Set environment variables
export AWS_ACCESS_KEY_ID=your_key_here
export AWS_SECRET_ACCESS_KEY=your_secret_here
export AWS_REGION_NAME=us-east-1

# Solution 3: Use IAM role (for EC2/ECS)
# No credentials needed - boto3 uses instance metadata

# Solution 4: Verify credentials work
aws bedrock list-foundation-models --region us-east-1
```

---

### Issue: Access Denied to Bedrock

**Symptoms:**
```
botocore.exceptions.ClientError: An error occurred (AccessDeniedException) when calling the InvokeModel operation
```

**Diagnostic:**

```bash
# Check IAM permissions
aws iam get-user-policy --user-name your-user --policy-name your-policy

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

**Solutions:**

1. **Request Model Access:**
   - Go to AWS Console → Bedrock
   - Click "Model access" in left sidebar
   - Request access to Amazon Nova Pro and Mistral Large
   - Wait for approval (usually instant for AWS models)

2. **Update IAM Policy:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

3. **Use IAM Role (Production):**

```bash
# Attach IAM role to EC2 instance
aws iam attach-role-policy \
  --role-name contract-agent-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonBedrockFullAccess
```

---

### Issue: Bedrock throttling errors

**Symptoms:**
```
botocore.exceptions.ClientError: ThrottlingException
Rate exceeded for operation InvokeModel
```

**Solutions:**

```bash
# Implement exponential backoff (already in code)
# Reduce concurrent requests
# Increase timeout settings in config/prompt_config.json

# Check your Bedrock quotas
aws service-quotas list-service-quotas \
  --service-code bedrock \
  --region us-east-1

# Request quota increase if needed
aws service-quotas request-service-quota-increase \
  --service-code bedrock \
  --quota-code L-xxx \
  --desired-value 100
```

---

## Application Errors

### Issue: Server won't start

**Symptoms:**
```
Address already in use: ('0.0.0.0', 5002)
```

**Diagnostic:**

```bash
# Check what's using port 5002
lsof -i :5002
netstat -tuln | grep 5002
```

**Solutions:**

```bash
# Solution 1: Kill existing process
kill -9 $(lsof -t -i:5002)

# Solution 2: Use different port
export PORT=5003
python app.py

# Solution 3: Find and stop previous instance
ps aux | grep app.py
kill <process_id>
```

---

### Issue: Processing thread not starting

**Symptoms:**
```
⚠️ Processing thread is dead, restarting...
Jobs stuck in 'queued' status
```

**Diagnostic:**

```bash
# Check thread status
curl http://localhost:5002/debug/queue | jq '.processing_thread_alive'

# Check logs for thread errors
tail -f logs/server.log | grep "thread"
```

**Solutions:**

```bash
# Solution 1: Restart server
# Press Ctrl+C and restart
python app.py

# Solution 2: Check for exceptions in process_jobs()
# Review logs for error messages

# Solution 3: Increase thread timeout
# In app.py, modify job_queue.get(timeout=120)
```

---

### Issue: Jobs fail with timeout

**Symptoms:**
```
TimeoutError: Job processing exceeded 300 seconds
```

**Solutions:**

```bash
# Solution 1: Increase chunk timeout
# Edit config/prompt_config.json
{
  "processing": {
    "chunk_timeout": 600  # Increase from 300 to 600
  }
}

# Solution 2: Check document size
# Very large contracts (>100KB) may need more time
ls -lh data/uploads/

# Solution 3: Optimize chunking
# Reduce chunk size in document_chunking.py
```

---

### Issue: Low quality scores

**Symptoms:**
```
final_score: 0.45 (below 0.70 threshold)
```

**Diagnostic:**

```bash
# Review evaluation details
curl http://localhost:5002/job_result/<job_id> | jq '.processing_results'

# Check prompt effectiveness
python tests/test_prompt_effectiveness.py
```

**Solutions:**

1. **Improve prompts** in `core/prompts/system_prompts.py`
2. **Adjust evaluation criteria** in `config/prompt_config.json`
3. **Test with different models**:
   ```bash
   export CONTRACT_PRIMARY_MODEL=mistral.mistral-large-2402-v1:0
   ```
4. **Review LEDGAR evaluation methodology** in docs

---

### Issue: Import errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'core'
ImportError: cannot import name 'ContractProcessingCrew'
```

**Solutions:**

```bash
# Solution 1: Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/ec2-user/cb/Contract-Agent"

# Solution 2: Run from project root
cd /home/ec2-user/cb/Contract-Agent
python app.py

# Solution 3: Install in development mode
pip install -e .

# Solution 4: Check directory structure
ls core/crew/crew_manager.py  # Should exist
```

---

## Performance Issues

### Issue: Slow processing times

**Symptoms:**
```
Processing time: 180+ seconds for small contracts
```

**Diagnostic:**

```bash
# Check system resources
top
htop

# Monitor during processing
curl http://localhost:5002/metrics | jq '.statistics.average_processing_time'
```

**Solutions:**

```bash
# Solution 1: Use faster model (Nova Pro)
export CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0

# Solution 2: Reduce max iterations
# Edit config/prompt_config.json
{
  "processing": {
    "max_iterations": 2  # Reduce from 3
  }
}

# Solution 3: Optimize chunking
# Increase chunk size for faster processing
# Edit core/document_processing/document_chunking.py

# Solution 4: Check network latency
ping bedrock-runtime.us-east-1.amazonaws.com
```

---

### Issue: High memory usage

**Symptoms:**
```
MemoryError: Unable to allocate memory
Server becomes unresponsive
```

**Diagnostic:**

```bash
# Monitor memory
free -h
watch -n 1 free -h

# Check application memory
ps aux | grep app.py
```

**Solutions:**

```bash
# Solution 1: Enable session cleanup
# In infrastructure/storage/memory_storage.py
# Ensure session_based_cleanup = True

# Solution 2: Clear old jobs manually
curl http://localhost:5002/debug/queue

# Solution 3: Restart server periodically
# Use supervisor or systemd for automatic restarts

# Solution 4: Increase system memory
# Upgrade to larger instance type (t3.small → t3.medium)
```

---

### Issue: Queue backlog

**Symptoms:**
```
Queue size: 50 jobs
Processing very slow
```

**Diagnostic:**

```bash
# Check queue status
curl http://localhost:5002/debug/queue | jq '.queue_size'

# Monitor job statistics
curl http://localhost:5002/debug/queue | jq '.job_statistics'
```

**Solutions:**

```bash
# Solution 1: Scale horizontally
# Add more instances behind load balancer

# Solution 2: Implement multiple processing threads
# Modify app.py to support concurrent processing

# Solution 3: Increase instance size
eb scale 1 --instance-type t3.medium

# Solution 4: Implement job prioritization
# Modify job_queue to use PriorityQueue
```

---

## Deployment Problems

### Issue: Elastic Beanstalk deployment fails

**Symptoms:**
```
ERROR: ServiceError - Configuration validation failed
Environment health: Red
```

**Diagnostic:**

```bash
# Check EB logs
eb logs

# Check environment health
eb health --refresh

# Check configuration
eb config
```

**Solutions:**

```bash
# Solution 1: Verify application.py exists
ls application.py  # Required for EB

# Solution 2: Check .ebignore
cat .ebignore  # Ensure critical files not excluded

# Solution 3: Validate environment variables
eb printenv

# Solution 4: Check Python version
cat .elasticbeanstalk/config.yml | grep platform
# Should be: Python 3.11

# Solution 5: Manually set platform
eb platform select "Python 3.11 running on 64bit Amazon Linux 2023"
```

---

### Issue: Health check failures

**Symptoms:**
```
Health check failed - 502 Bad Gateway
Environment shows "Degraded"
```

**Solutions:**

```bash
# Solution 1: Verify root endpoint
curl http://your-app.elasticbeanstalk.com/
# Should return 200 OK

# Solution 2: Check application logs
eb logs | grep "ERROR"

# Solution 3: Verify health check path
# In .ebextensions/healthcheck.config
# Application Healthcheck URL: /health

# Solution 4: Test health endpoint locally
python app.py
curl http://localhost:5002/health
```

---

### Issue: Docker container won't start

**Symptoms:**
```
docker: Error response from daemon
Container exits immediately
```

**Diagnostic:**

```bash
# View container logs
docker logs <container_id>

# Check container status
docker ps -a

# Inspect container
docker inspect <container_id>
```

**Solutions:**

```bash
# Solution 1: Check Dockerfile
# Ensure CMD is correct: CMD ["python", "application.py"]

# Solution 2: Verify port exposure
docker run -p 5002:5002 contract-agent:latest

# Solution 3: Check environment variables
docker run --env-file .env contract-agent:latest

# Solution 4: Run interactively for debugging
docker run -it contract-agent:latest /bin/bash
```

---

## Data & Storage Issues

### Issue: File upload fails

**Symptoms:**
```
413 Payload Too Large
File upload rejected
```

**Solutions:**

```bash
# Solution 1: Check file size
ls -lh your_contract.pdf
# Maximum: 200MB

# Solution 2: Increase limit (if needed)
# In app.py
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300MB

# Solution 3: Compress PDF
# Use ghostscript or similar tool
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed.pdf input.pdf
```

---

### Issue: Data directories not writable

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: 'data/uploads/file.pdf'
```

**Solutions:**

```bash
# Fix permissions
chmod -R 755 data/
chown -R $USER:$USER data/

# Verify
ls -ld data/uploads data/generated data/temp

# Create if missing
mkdir -p data/uploads data/generated data/temp
```

---

### Issue: Memory storage corruption

**Symptoms:**
```
Job data inconsistent
Jobs disappearing
KeyError in memory storage
```

**Solutions:**

```bash
# Solution 1: Restart server (clears in-memory data)
# Press Ctrl+C and restart

# Solution 2: Implement persistent storage
# Use Redis or database instead of in-memory storage

# Solution 3: Enable thread safety checks
# Review infrastructure/storage/memory_storage.py
# Ensure all operations use locks
```

---

## Testing Failures

### Issue: Tests fail with connection errors

**Symptoms:**
```
ConnectionRefusedError: [Errno 111] Connection refused
Tests fail on API endpoints
```

**Solutions:**

```bash
# Solution 1: Start server before running tests
# Terminal 1:
python app.py

# Terminal 2:
python -m pytest tests/test_api_server.py

# Solution 2: Use test fixtures
# Tests should start their own server instance

# Solution 3: Mock external dependencies
pip install pytest-mock
```

---

### Issue: LEDGAR evaluation fails

**Symptoms:**
```
0% success rate
All tests returning errors
```

**Diagnostic:**

```bash
# Run with verbose output
python scripts/ledgar_evaluation_FIXED.py --verbose

# Check test data exists
ls -lh data/test_data/*.txt
```

**Solutions:**

```bash
# Solution 1: Verify test data
ls data/test_data/sample_*.txt
# Should see 10 sample files

# Solution 2: Check prompts
cat data/test_data/EVALUATION_PROMPTS.md

# Solution 3: Test single contract first
python simple_test.py

# Solution 4: Review model configuration
echo $CONTRACT_PRIMARY_MODEL
```

---

## Getting Help

### Collect Diagnostic Information

```bash
# Generate diagnostic report
cat > diagnostic_report.txt << EOF
=== System Information ===
$(uname -a)
$(python --version)

=== Python Packages ===
$(pip list | grep -E "Flask|boto3|crewai|langchain")

=== Environment Variables ===
AWS_REGION_NAME: ${AWS_REGION_NAME}
CONTRACT_PRIMARY_MODEL: ${CONTRACT_PRIMARY_MODEL}

=== Server Status ===
$(curl -s http://localhost:5002/health | jq '.')

=== Recent Errors ===
$(tail -50 logs/server.log | grep ERROR)

=== Queue Status ===
$(curl -s http://localhost:5002/debug/queue | jq '.')
EOF

cat diagnostic_report.txt
```

### Support Channels

1. **Documentation:**
   - [API_REFERENCE.md](./API_REFERENCE.md)
   - [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md)
   - [SYSTEM_HANDOFF_GUIDE.md](../SYSTEM_HANDOFF_GUIDE.md)

2. **Logs:**
   ```bash
   # Application logs
   tail -f logs/server.log
   
   # EB logs
   eb logs --stream
   ```

3. **Debugging:**
   ```bash
   # Run with debug mode
   export FLASK_DEBUG=1
   export LOG_LEVEL=DEBUG
   python app.py
   ```

---

## Common Error Messages Reference

| Error Message | Likely Cause | Quick Fix |
|---------------|--------------|-----------|
| `NoCredentialsError` | AWS credentials not configured | Run `aws configure` |
| `AccessDeniedException` | No Bedrock access | Request model access in AWS Console |
| `ModuleNotFoundError` | Missing dependencies | Run `pip install -r requirements.txt` |
| `Address already in use` | Port conflict | Kill process: `kill -9 $(lsof -t -i:5002)` |
| `Configuration validation failed` | Missing env vars | Check `.env` file |
| `ThrottlingException` | Bedrock rate limit | Reduce request rate |
| `TimeoutError` | Processing too slow | Increase `chunk_timeout` in config |
| `MemoryError` | Out of memory | Enable session cleanup, restart server |
| `502 Bad Gateway` | App not responding | Check logs: `eb logs` |
| `Job not found` | Job expired/cleaned | Retrieve results faster after completion |

---

## Emergency Recovery

### Complete Reset

If all else fails, perform a clean reset:

```bash
# 1. Stop all processes
pkill -f "python app.py"
pkill -f "python application.py"

# 2. Remove virtual environment
conda deactivate
conda remove -n contract-agent --all

# 3. Clean data directories
rm -rf data/uploads/* data/generated/* data/temp/*

# 4. Reinstall
conda create -n contract-agent python=3.11
conda activate contract-agent
pip install -r requirements.txt

# 5. Reconfigure
aws configure
cp .env.example .env
# Edit .env with your values

# 6. Test
python app.py
curl http://localhost:5002/health
```

---

**Last Updated:** 2025-10-02  
**Status:** Comprehensive Troubleshooting Reference ✅

**Need More Help?**
- Run `./diagnose.sh` for automated diagnostics
- Check other docs in `/docs/` directory
- Review recent changes in git history
- Contact system administrator or AWS support
