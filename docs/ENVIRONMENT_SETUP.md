# Environment Setup Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-02

---

## Table of Contents

1. [Overview](#overview)
2. [Environment Variables](#environment-variables)
3. [Security Best Practices](#security-best-practices)
4. [Configuration Files](#configuration-files)
5. [Development vs Production](#development-vs-production)
6. [AWS Configuration](#aws-configuration)
7. [Model Configuration](#model-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Overview

Contract-Agent requires specific environment variables and configuration to connect to AWS Bedrock, manage AI models, and process contracts. This guide covers:

- **Required environment variables**
- **Security best practices** for credential management
- **Configuration file setup**
- **Development and production configurations**

---

## Environment Variables

### Required Variables

The following environment variables **must** be set for the application to function:

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key (⚠️ See Security Notes) | Yes | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key (⚠️ See Security Notes) | Yes | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_REGION_NAME` | AWS region for Bedrock | Yes | `us-east-1` |
| `CONTRACT_PRIMARY_MODEL` | Primary AI model identifier | Yes | `us.amazon.nova-pro-v1:0` |
| `CONTRACT_FALLBACK_MODEL` | Fallback AI model identifier | Yes | `mistral.mistral-large-2402-v1:0` |
| `ACTOR_MODEL` | Model for Actor agent | Yes | `us.amazon.nova-pro-v1:0` |
| `CRITIC_MODEL` | Model for Critic agent | Yes | `us.amazon.nova-pro-v1:0` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PORT` | Flask server port | `5002` | `8080` |
| `FLASK_ENV` | Flask environment mode | `production` | `development` |
| `MAX_CONTENT_LENGTH` | Maximum upload size (bytes) | `209715200` | `104857600` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG` |

---

## Security Best Practices

### ⚠️ CRITICAL: Never Commit Credentials to Git

**Current Issue:** The `.env` file in this repository contains hardcoded AWS credentials. This is a **major security vulnerability**.

### Recommended Approaches

#### Option 1: AWS IAM Roles (PRODUCTION - BEST PRACTICE)

For production deployments on AWS (EC2, ECS, Lambda, Elastic Beanstalk), use **IAM roles** instead of access keys:

1. **Create IAM Role** with Bedrock permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "*"
       }
     ]
   }
   ```

2. **Attach role to EC2/ECS instance**

3. **Remove AWS credentials from environment variables**:
   ```bash
   # .env file - NO credentials needed!
   AWS_REGION_NAME=us-east-1
   CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0
   # ... other non-sensitive config
   ```

4. **boto3 automatically uses IAM role credentials**

#### Option 2: AWS Secrets Manager (PRODUCTION)

Store credentials in AWS Secrets Manager and retrieve at runtime:

```python
import boto3
import json

def get_aws_credentials():
    """Retrieve credentials from Secrets Manager"""
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='contract-agent/credentials')
    secrets = json.loads(response['SecretString'])
    return secrets

# In your application startup
secrets = get_aws_credentials()
os.environ['AWS_ACCESS_KEY_ID'] = secrets['access_key_id']
os.environ['AWS_SECRET_ACCESS_KEY'] = secrets['secret_access_key']
```

#### Option 3: Environment Variables (DEVELOPMENT ONLY)

For local development, use environment variables **without** storing in `.env` file:

**macOS/Linux:**
```bash
# Set in shell session (not persisted)
export AWS_ACCESS_KEY_ID="your_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_here"
export AWS_REGION_NAME="us-east-1"

# Or create a .env.local file (add to .gitignore!)
echo ".env.local" >> .gitignore
```

**Windows (PowerShell):**
```powershell
$env:AWS_ACCESS_KEY_ID="your_key_here"
$env:AWS_SECRET_ACCESS_KEY="your_secret_here"
$env:AWS_REGION_NAME="us-east-1"
```

#### Option 4: AWS CLI Configuration (DEVELOPMENT)

Use AWS CLI credentials instead of explicit environment variables:

```bash
# Configure AWS CLI
aws configure

# boto3 automatically uses ~/.aws/credentials
# No need to set AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY
```

---

## Configuration Files

### .env File Structure

Create a `.env` file in the project root (ensure it's in `.gitignore`):

```bash
# AWS Configuration (DO NOT COMMIT REAL CREDENTIALS)
AWS_REGION_NAME=us-east-1

# Model Configuration
CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0
CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0
ACTOR_MODEL=us.amazon.nova-pro-v1:0
CRITIC_MODEL=us.amazon.nova-pro-v1:0

# Server Configuration
PORT=5002
FLASK_ENV=development

# Logging
LOG_LEVEL=INFO
```

### .env.example Template

Create a `.env.example` file for documentation (safe to commit):

```bash
# AWS Configuration
# For production, use IAM roles instead of credentials
# For development, use AWS CLI or local env vars
AWS_REGION_NAME=us-east-1

# Model Configuration
CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0
CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0
ACTOR_MODEL=us.amazon.nova-pro-v1:0
CRITIC_MODEL=us.amazon.nova-pro-v1:0

# Server Configuration
PORT=5002
FLASK_ENV=development

# Optional: Logging
LOG_LEVEL=INFO
```

### .gitignore Configuration

Ensure these files are **never** committed:

```gitignore
# Environment variables with credentials
.env
.env.local
.env.*.local

# AWS credentials
.aws/
credentials

# Python cache
__pycache__/
*.pyc
*.pyo
```

---

## Development vs Production

### Development Environment

```bash
# .env.development
AWS_REGION_NAME=us-east-1
CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0
CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0
ACTOR_MODEL=us.amazon.nova-pro-v1:0
CRITIC_MODEL=us.amazon.nova-pro-v1:0
PORT=5002
FLASK_ENV=development
LOG_LEVEL=DEBUG
```

**Usage:**
```bash
# Load development config
cp .env.development .env
python app.py
```

### Production Environment

#### AWS Elastic Beanstalk

Set environment variables via EB CLI:

```bash
eb setenv \
  AWS_REGION_NAME=us-east-1 \
  CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0 \
  CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0 \
  ACTOR_MODEL=us.amazon.nova-pro-v1:0 \
  CRITIC_MODEL=us.amazon.nova-pro-v1:0 \
  FLASK_ENV=production \
  LOG_LEVEL=INFO
```

Or via AWS Console:
1. Navigate to Elastic Beanstalk environment
2. Configuration → Software → Environment properties
3. Add each variable

#### Docker/ECS

Use environment variable files or secrets:

```yaml
# docker-compose.yml
services:
  contract-agent:
    image: contract-agent:latest
    environment:
      - AWS_REGION_NAME=${AWS_REGION_NAME}
      - CONTRACT_PRIMARY_MODEL=${CONTRACT_PRIMARY_MODEL}
      # ... other vars
    env_file:
      - .env.production
```

#### Kubernetes

Use ConfigMaps and Secrets:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: contract-agent-config
data:
  AWS_REGION_NAME: "us-east-1"
  CONTRACT_PRIMARY_MODEL: "us.amazon.nova-pro-v1:0"
  PORT: "5002"
---
apiVersion: v1
kind: Secret
metadata:
  name: contract-agent-secrets
type: Opaque
stringData:
  AWS_ACCESS_KEY_ID: "your-key-here"
  AWS_SECRET_ACCESS_KEY: "your-secret-here"
```

---

## AWS Configuration

### Required AWS Permissions

The AWS credentials or IAM role must have these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockModelInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:GetFoundationModel",
        "bedrock:ListFoundationModels"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/amazon.nova-pro-v1:0",
        "arn:aws:bedrock:*::foundation-model/mistral.mistral-large-2402-v1:0"
      ]
    }
  ]
}
```

### Supported AWS Regions

AWS Bedrock is available in specific regions. Verify your models are available:

| Region | Region Name | Nova Pro | Mistral Large |
|--------|-------------|----------|---------------|
| `us-east-1` | US East (N. Virginia) | ✅ | ✅ |
| `us-west-2` | US West (Oregon) | ✅ | ✅ |
| `eu-west-1` | Europe (Ireland) | ✅ | ❌ |
| `ap-northeast-1` | Asia Pacific (Tokyo) | ✅ | ❌ |

**Note:** Model availability changes frequently. Check AWS Bedrock documentation.

### Testing AWS Connection

Use the health endpoint to verify AWS connectivity:

```bash
curl http://localhost:5002/health | jq '.components.bedrock_available'
# Should return: true
```

---

## Model Configuration

### Available Models

#### Amazon Nova Pro (Recommended)
- **Model ID:** `us.amazon.nova-pro-v1:0`
- **Performance:** 29% faster than Mistral Large
- **Quality:** LEDGAR score 0.800
- **Context Window:** 300K tokens
- **Best For:** Primary contract processing

#### Mistral Large (Fallback)
- **Model ID:** `mistral.mistral-large-2402-v1:0`
- **Performance:** Slower but reliable
- **Quality:** LEDGAR score 0.800 (same quality)
- **Context Window:** 128K tokens
- **Best For:** Fallback when Nova Pro is unavailable

### Model Selection Strategy

The application uses a **fallback model strategy**:

1. **Primary attempt** with `CONTRACT_PRIMARY_MODEL` (Nova Pro)
2. **Fallback** to `CONTRACT_FALLBACK_MODEL` if primary fails
3. **Retry logic** with 2 attempts per model

### Custom Model Configuration

To use different models, update environment variables:

```bash
# Example: Use Claude Sonnet instead
CONTRACT_PRIMARY_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
CONTRACT_FALLBACK_MODEL=anthropic.claude-3-haiku-20240307-v1:0
ACTOR_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
CRITIC_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

**⚠️ Warning:** Different models may require prompt adjustments and re-evaluation.

---

## Troubleshooting

### Issue: "AWS credentials not found"

**Solution:**
```bash
# Check environment variables
echo $AWS_ACCESS_KEY_ID
echo $AWS_SECRET_ACCESS_KEY

# Verify .env file is loaded
cat .env | grep AWS

# Test AWS CLI connection
aws sts get-caller-identity
```

### Issue: "Bedrock model not found"

**Solution:**
```bash
# Verify model is available in your region
aws bedrock list-foundation-models --region us-east-1 \
  | jq '.modelSummaries[] | select(.modelId | contains("nova-pro"))'

# Check if you have model access
# Visit AWS Bedrock Console → Model access → Request access
```

### Issue: "Access Denied" when invoking Bedrock

**Solution:**
1. Verify IAM permissions (see AWS Configuration section)
2. Check if Bedrock is enabled in your AWS account
3. Verify model access has been granted in AWS Console

### Issue: Environment variables not loading

**Solution:**
```bash
# Verify python-dotenv is installed
pip install python-dotenv

# Check .env file location (must be in project root)
ls -la .env

# Load environment manually in Python
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('AWS_REGION_NAME'))"
```

### Issue: Different behavior in development vs production

**Causes:**
- Different environment variable values
- Missing variables in production
- IAM role vs access keys differences

**Solution:**
```bash
# Compare environments
# Development
cat .env

# Production (EB)
eb printenv

# Ensure all required variables are set in both
```

---

## Configuration Validation

### Startup Validation

The application validates configuration on startup:

```python
# From app.py - validate_configuration()
✅ AWS_REGION_NAME is set
✅ CONTRACT_PRIMARY_MODEL is set
✅ Upload folder is writable
✅ Configuration validation passed
```

If validation fails, the server won't start.

### Manual Validation Script

Create a validation script:

```python
#!/usr/bin/env python3
"""Validate Contract-Agent environment configuration"""

import os
from dotenv import load_dotenv

def validate_env():
    load_dotenv()
    
    required = [
        'AWS_REGION_NAME',
        'CONTRACT_PRIMARY_MODEL',
        'CONTRACT_FALLBACK_MODEL',
        'ACTOR_MODEL',
        'CRITIC_MODEL'
    ]
    
    missing = []
    for var in required:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Missing required variables: {', '.join(missing)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == '__main__':
    validate_env()
```

---

## Quick Reference

### Development Setup (macOS/Linux)

```bash
# 1. Create .env file (without credentials)
cp .env.example .env

# 2. Use AWS CLI credentials
aws configure

# 3. Set model configuration
cat >> .env << EOF
AWS_REGION_NAME=us-east-1
CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0
CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0
ACTOR_MODEL=us.amazon.nova-pro-v1:0
CRITIC_MODEL=us.amazon.nova-pro-v1:0
PORT=5002
EOF

# 4. Verify configuration
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('Region:', os.getenv('AWS_REGION_NAME'))"

# 5. Start server
python app.py
```

### Production Setup (AWS EB)

```bash
# 1. Set environment variables (no credentials needed with IAM role)
eb setenv \
  AWS_REGION_NAME=us-east-1 \
  CONTRACT_PRIMARY_MODEL=us.amazon.nova-pro-v1:0 \
  CONTRACT_FALLBACK_MODEL=mistral.mistral-large-2402-v1:0 \
  ACTOR_MODEL=us.amazon.nova-pro-v1:0 \
  CRITIC_MODEL=us.amazon.nova-pro-v1:0

# 2. Deploy
eb deploy

# 3. Verify
eb printenv
curl https://your-app.elasticbeanstalk.com/health
```

---

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] No credentials committed to git repository
- [ ] Production uses IAM roles (not access keys)
- [ ] Development uses AWS CLI or local env vars
- [ ] Secrets are encrypted at rest
- [ ] Access keys are rotated regularly (if used)
- [ ] Minimum required IAM permissions configured
- [ ] Environment variables validated on startup

---

**Last Updated:** 2025-10-02  
**Status:** Production Ready with Security Improvements Needed ⚠️

**Next Steps:**
1. Migrate production to IAM roles
2. Remove hardcoded credentials from `.env` in git
3. Implement AWS Secrets Manager for sensitive config
4. Add environment variable validation script to CI/CD
