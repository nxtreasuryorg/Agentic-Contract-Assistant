# Security Guide

**Version:** 1.0.0  
**Last Updated:** 2025-10-02  
**Security Level:** Production

---

## Table of Contents

1. [Security Overview](#security-overview)
2. [Critical Security Issues](#critical-security-issues)
3. [Credential Management](#credential-management)
4. [Application Security](#application-security)
5. [Infrastructure Security](#infrastructure-security)
6. [Data Protection](#data-protection)
7. [Network Security](#network-security)
8. [Compliance & Standards](#compliance--standards)
9. [Security Monitoring](#security-monitoring)
10. [Incident Response](#incident-response)

---

## Security Overview

### Security Posture

Contract-Agent processes sensitive legal documents and must maintain high security standards.

**Security Priorities:**
1. 🔴 **Critical:** Credential protection, data encryption, access control
2. 🟠 **High:** Input validation, secure communications, audit logging
3. 🟡 **Medium:** Rate limiting, session management, error handling
4. 🟢 **Low:** Logging verbosity, performance optimization

### Threat Model

**Assets to Protect:**
- Contract documents (potentially confidential)
- AWS credentials and API keys
- Processing results and metadata
- System configuration and prompts

**Threat Actors:**
- External attackers (internet-facing services)
- Malicious file uploads
- Credential theft/exposure
- Data exfiltration attempts

**Attack Vectors:**
- Exposed credentials in code/logs
- Malicious PDF/file uploads
- API abuse and DoS attacks
- Injection attacks (prompt injection, XSS)
- Man-in-the-middle attacks

---

## Critical Security Issues

### 🔴 CRITICAL: Hardcoded Credentials in Repository

**Issue:** The `.env` file contains hardcoded AWS credentials committed to git.

**Current State:**
```bash
# SECURITY VIOLATION - NEVER DO THIS!
AWS_ACCESS_KEY_ID=AKIA****************
AWS_SECRET_ACCESS_KEY=****************************************
```

**Immediate Actions Required:**

```bash
# 1. Rotate compromised credentials IMMEDIATELY
aws iam create-access-key --user-name your-username
aws iam delete-access-key --access-key-id AKIA****************

# 2. Remove from git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 3. Add .env to .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore

# 4. Use secure alternatives (see Credential Management section)
```

**Long-term Solution:**

**Production (AWS):**
```bash
# Use IAM roles instead of access keys
# Attach IAM role to EC2/ECS/Lambda/EB instance
# boto3 automatically uses instance metadata

# No credentials needed in application!
# Remove AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY entirely
```

**Development:**
```bash
# Use AWS CLI credentials
aws configure
# Credentials stored in ~/.aws/credentials (not in git)

# Or use environment variables (not in .env file)
export AWS_ACCESS_KEY_ID=xxx
export AWS_SECRET_ACCESS_KEY=xxx
```

---

## Credential Management

### Best Practices

#### ✅ DO

1. **Use IAM Roles in Production**
   ```bash
   # Attach role to resource
   # No hardcoded credentials needed
   ```

2. **Use AWS Secrets Manager**
   ```python
   import boto3
   import json
   
   def get_secrets():
       client = boto3.client('secretsmanager', region_name='us-east-1')
       response = client.get_secret_value(SecretId='contract-agent/prod')
       return json.loads(response['SecretString'])
   ```

3. **Use Environment Variables**
   ```bash
   # Set at system level, not in files
   export AWS_ACCESS_KEY_ID=xxx
   export AWS_SECRET_ACCESS_KEY=xxx
   ```

4. **Rotate Credentials Regularly**
   ```bash
   # Rotate every 90 days
   aws iam create-access-key --user-name contract-agent
   aws iam delete-access-key --access-key-id OLD_KEY_ID
   ```

#### ❌ DON'T

1. **Never commit credentials to git**
   ```bash
   # BAD - Never do this!
   git add .env
   ```

2. **Never log credentials**
   ```python
   # BAD - Never do this!
   print(f"Using key: {os.getenv('AWS_SECRET_ACCESS_KEY')}")
   ```

3. **Never hardcode in source**
   ```python
   # BAD - Never do this!
   AWS_KEY = "AKIA****************"
   ```

4. **Never share credentials**
   - Don't send via email/Slack/chat
   - Don't store in shared documents
   - Use secure vaults only

### Secure Credential Storage

#### AWS Secrets Manager (Recommended)

```python
# Store secrets
import boto3
import json

secrets_client = boto3.client('secretsmanager', region_name='us-east-1')

secrets = {
    "primary_model": "us.amazon.nova-pro-v1:0",
    "api_keys": {
        "external_api": "secret_key_here"
    }
}

secrets_client.create_secret(
    Name='contract-agent/config',
    SecretString=json.dumps(secrets),
    Description='Contract-Agent configuration secrets'
)

# Retrieve secrets
def load_secrets():
    response = secrets_client.get_secret_value(
        SecretId='contract-agent/config'
    )
    return json.loads(response['SecretString'])

# Use in application
config = load_secrets()
PRIMARY_MODEL = config['primary_model']
```

#### AWS Parameter Store (Alternative)

```python
import boto3

ssm = boto3.client('ssm', region_name='us-east-1')

# Store parameter
ssm.put_parameter(
    Name='/contract-agent/primary-model',
    Value='us.amazon.nova-pro-v1:0',
    Type='SecureString',
    Tier='Standard'
)

# Retrieve parameter
def get_parameter(name):
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

PRIMARY_MODEL = get_parameter('/contract-agent/primary-model')
```

---

## Application Security

### Input Validation

#### File Upload Security

```python
# In app.py - Already implemented
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.rtf'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

def validate_file_upload(file):
    """Secure file upload validation"""
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {file_ext}")
    
    # Check file size
    if file.content_length and file.content_length > MAX_FILE_SIZE:
        raise ValueError("File too large")
    
    # Sanitize filename
    filename = secure_filename(file.filename)
    
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename")
    
    return filename
```

#### Prompt Injection Prevention

```python
# In app.py - Already implemented
def sanitize_prompt(user_prompt):
    """Prevent prompt injection attacks"""
    
    # Check length
    if len(user_prompt) > 10000:
        raise ValueError("Prompt too long")
    
    # Block malicious patterns
    malicious_patterns = [
        '<script>',
        '</script>',
        'javascript:',
        'data:',
        'onerror=',
        'onclick='
    ]
    
    prompt_lower = user_prompt.lower()
    for pattern in malicious_patterns:
        if pattern in prompt_lower:
            raise ValueError("Invalid characters in prompt")
    
    return user_prompt.strip()
```

#### Job ID Validation

```python
# In app.py - Already implemented
def validate_job_id(job_id):
    """Validate job ID format for security"""
    
    # Check not empty
    if not job_id or not job_id.strip():
        return False
    
    # Check for path traversal
    if ".." in job_id or "/" in job_id or "\\" in job_id:
        return False
    
    # Check for HTML/script tags
    if "<" in job_id or ">" in job_id:
        return False
    
    # Validate UUID format
    try:
        uuid.UUID(job_id)
        return True
    except (ValueError, TypeError):
        return False
```

### Output Sanitization

```python
def sanitize_output(text):
    """Sanitize output to prevent XSS"""
    import html
    return html.escape(text)

# Use in API responses
response_data = {
    "final_rtf": sanitize_output(result.final_rtf),
    "crew_output": sanitize_output(result.crew_output)
}
```

### Error Handling

```python
# Good: Generic error messages
@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "error": "Internal server error occurred",
        "success": False
    }), 500

# Bad: Leaking implementation details
# DON'T expose stack traces, file paths, or config
```

---

## Infrastructure Security

### IAM Permissions (Least Privilege)

**Minimal Required Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvokeOnly",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/us.amazon.nova-pro-v1:0",
        "arn:aws:bedrock:us-east-1::foundation-model/mistral.mistral-large-2402-v1:0"
      ]
    },
    {
      "Sid": "LogsWrite",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:*:log-group:/aws/elasticbeanstalk/contract-agent/*"
    }
  ]
}
```

**❌ Avoid Overly Permissive Policies:**

```json
// BAD - Never use this!
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

### Network Security

#### Firewall Rules

```bash
# Security Group Configuration
# Allow only necessary ports

# HTTP (redirect to HTTPS)
Port 80: 0.0.0.0/0

# HTTPS
Port 443: 0.0.0.0/0

# SSH (restrict to your IP)
Port 22: YOUR_IP/32

# Application port (internal only)
Port 5002: VPC only (not public)
```

#### TLS/SSL Configuration

```yaml
# .ebextensions/https.config
option_settings:
  aws:elbv2:listener:443:
    Protocol: HTTPS
    SSLCertificateArns: arn:aws:acm:us-east-1:xxx:certificate/xxx
    SSLPolicy: ELBSecurityPolicy-TLS-1-2-2017-01
  
  # Redirect HTTP to HTTPS
  aws:elbv2:listener:80:
    DefaultProcess: default
    ListenerEnabled: 'true'
    Protocol: HTTP
    Rules: 'redirect-to-https'
```

#### CORS Configuration

```python
# In app.py
from flask_cors import CORS

# Development: Allow all origins
CORS(app, origins=["*"])

# Production: Restrict origins
CORS(app, origins=[
    "https://yourdomain.com",
    "https://app.yourdomain.com"
], 
methods=["GET", "POST"],
allow_headers=["Content-Type", "Authorization"])
```

---

## Data Protection

### Data Classification

| Data Type | Classification | Protection Level |
|-----------|---------------|------------------|
| Contract documents | Confidential | Encrypt at rest & in transit |
| Processing results | Confidential | Encrypt at rest & in transit |
| Job metadata | Internal | Encrypt in transit |
| System logs | Internal | Sanitize, encrypt |
| Configuration | Secret | AWS Secrets Manager |

### Encryption

#### At Rest

```python
# S3 encryption (if using S3 storage)
import boto3

s3 = boto3.client('s3')
s3.put_object(
    Bucket='contract-agent-documents',
    Key='contract.pdf',
    Body=file_data,
    ServerSideEncryption='AES256',  # Or 'aws:kms'
    ACL='private'
)
```

#### In Transit

```python
# Always use HTTPS
# In production, configure ALB to enforce HTTPS

# Verify TLS
import ssl
context = ssl.create_default_context()
context.check_hostname = True
context.verify_mode = ssl.CERT_REQUIRED
```

### Data Retention

```python
# Implement data retention policy
class MemoryStorage:
    def __init__(self):
        self.retention_period = 48  # hours
    
    def cleanup_old_jobs(self):
        """Delete jobs older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_period)
        
        for job_id, job_data in list(self.jobs.items()):
            if job_data.created_at < cutoff_time:
                del self.jobs[job_id]
                logger.info(f"Deleted old job: {job_id}")
```

### Data Sanitization

```python
def sanitize_logs(log_entry):
    """Remove sensitive data from logs"""
    
    # Patterns to redact
    patterns = [
        (r'AWS_ACCESS_KEY_ID=\w+', 'AWS_ACCESS_KEY_ID=[REDACTED]'),
        (r'AWS_SECRET_ACCESS_KEY=\w+', 'AWS_SECRET_ACCESS_KEY=[REDACTED]'),
        (r'\b\d{16}\b', '[CREDIT_CARD_REDACTED]'),
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]')
    ]
    
    for pattern, replacement in patterns:
        log_entry = re.sub(pattern, replacement, log_entry)
    
    return log_entry
```

---

## Network Security

### Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

# Apply to endpoints
@app.route('/process_contract', methods=['POST'])
@limiter.limit("20 per hour")  # Limit contract processing
def process_contract():
    pass
```

### DDoS Protection

```yaml
# AWS WAF configuration
# Create Web ACL for Elastic Beanstalk

Rules:
  - Rate-based rule: 2000 requests per 5 minutes per IP
  - Geographic blocking: Block high-risk countries (optional)
  - Known bad inputs: Block SQL injection patterns
  - IP reputation: Block known malicious IPs
```

### API Authentication (Future Implementation)

```python
# JWT-based authentication
from flask_jwt_extended import JWTManager, jwt_required, create_access_token

app.config['JWT_SECRET_KEY'] = get_secret('jwt-secret')
jwt = JWTManager(app)

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    # Validate credentials
    if authenticate(username, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token)
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/process_contract', methods=['POST'])
@jwt_required()
def process_contract():
    # Protected endpoint
    pass
```

---

## Compliance & Standards

### Compliance Frameworks

#### GDPR Compliance

```python
# Data Subject Rights
class GDPRCompliance:
    def right_to_access(self, user_id):
        """Provide all data about user"""
        return get_all_user_data(user_id)
    
    def right_to_erasure(self, user_id):
        """Delete all user data"""
        delete_user_data(user_id)
        log_deletion(user_id)
    
    def right_to_portability(self, user_id):
        """Export data in machine-readable format"""
        return export_user_data_json(user_id)
```

#### SOC 2 Controls

1. **Access Control:** IAM roles and policies
2. **Encryption:** At rest and in transit
3. **Monitoring:** CloudWatch logs and metrics
4. **Incident Response:** Documented procedures
5. **Change Management:** Git version control

### Audit Logging

```python
import logging
import json
from datetime import datetime

audit_logger = logging.getLogger('audit')
audit_logger.setLevel(logging.INFO)

handler = logging.FileHandler('logs/audit.log')
audit_logger.addHandler(handler)

def log_audit_event(event_type, user_id, details):
    """Log security-relevant events"""
    audit_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': request.remote_addr,
        'details': details
    }
    audit_logger.info(json.dumps(audit_entry))

# Use in application
@app.route('/process_contract', methods=['POST'])
def process_contract():
    log_audit_event('CONTRACT_UPLOAD', user_id, {
        'filename': file.filename,
        'size': file.content_length
    })
```

---

## Security Monitoring

### CloudWatch Alarms

```bash
# CPU utilization
aws cloudwatch put-metric-alarm \
  --alarm-name contract-agent-high-cpu \
  --alarm-description "CPU over 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold

# Error rate
aws cloudwatch put-metric-alarm \
  --alarm-name contract-agent-high-errors \
  --alarm-description "Error rate over 5%" \
  --metric-name ErrorRate \
  --namespace ContractAgent \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### Security Events to Monitor

```python
# Log security events
SECURITY_EVENTS = [
    'FAILED_LOGIN_ATTEMPT',
    'INVALID_FILE_UPLOAD',
    'PROMPT_INJECTION_DETECTED',
    'RATE_LIMIT_EXCEEDED',
    'UNAUTHORIZED_ACCESS',
    'SUSPICIOUS_ACTIVITY',
    'CREDENTIAL_ROTATION',
    'CONFIGURATION_CHANGE'
]

def monitor_security_event(event_type, details):
    """Monitor and alert on security events"""
    if event_type in SECURITY_EVENTS:
        log_audit_event(event_type, details)
        
        # Send alert for critical events
        if event_type in ['UNAUTHORIZED_ACCESS', 'CREDENTIAL_ROTATION']:
            send_security_alert(event_type, details)
```

---

## Incident Response

### Incident Response Plan

#### 1. Detection

```bash
# Monitor for security incidents
# - Failed authentication attempts
# - Unusual traffic patterns
# - Error rate spikes
# - Unauthorized access attempts

# Check CloudWatch logs
aws logs tail /aws/elasticbeanstalk/contract-agent/var/log/eb-engine.log --follow
```

#### 2. Containment

```bash
# Immediate actions for security incident

# Isolate affected resources
eb terminate contract-agent-prod-compromised

# Rotate all credentials
aws iam delete-access-key --access-key-id COMPROMISED_KEY
aws iam create-access-key --user-name contract-agent

# Block malicious IPs
aws wafv2 create-ip-set \
  --name blocked-ips \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses 1.2.3.4/32
```

#### 3. Investigation

```bash
# Collect evidence
# - Application logs
# - CloudWatch logs
# - Access logs
# - Network traffic logs

# Analyze logs
eb logs --all > incident_logs.txt

# Review access patterns
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=InvokeModel \
  --start-time 2025-10-01 \
  --end-time 2025-10-02
```

#### 4. Recovery

```bash
# Deploy clean environment
eb create contract-agent-prod-new \
  --instance-type t3.small \
  --envvars $(cat secure_env_vars.txt)

# Verify security
python security_audit.py

# Restore data from backup
aws s3 sync s3://contract-agent-backups/latest/ ./
```

#### 5. Post-Incident

```markdown
## Incident Report Template

**Date:** 2025-10-02
**Incident Type:** [e.g., Credential Exposure]
**Severity:** [Critical/High/Medium/Low]

**Timeline:**
- Detection: [Time]
- Containment: [Time]
- Recovery: [Time]
- Resolution: [Time]

**Root Cause:**
[Description]

**Impact:**
[Description]

**Actions Taken:**
1. [Action 1]
2. [Action 2]

**Lessons Learned:**
[What we learned]

**Preventive Measures:**
[How to prevent recurrence]
```

---

## Security Checklist

### Development

- [ ] Never commit credentials to git
- [ ] Use `.env.example` for documentation only
- [ ] Validate all user inputs
- [ ] Sanitize all outputs
- [ ] Use parameterized queries (if using database)
- [ ] Implement error handling without leaking info
- [ ] Use security linters (bandit, safety)

### Deployment

- [ ] Use IAM roles instead of access keys
- [ ] Enable HTTPS/TLS encryption
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Enable CloudWatch logging
- [ ] Set up security monitoring
- [ ] Configure automated backups
- [ ] Test disaster recovery plan

### Operations

- [ ] Rotate credentials every 90 days
- [ ] Review IAM permissions monthly
- [ ] Monitor security alerts daily
- [ ] Apply security patches weekly
- [ ] Audit logs regularly
- [ ] Test incident response plan quarterly
- [ ] Review access control lists monthly

---

## Security Tools

### Static Analysis

```bash
# Python security linter
pip install bandit
bandit -r core/ infrastructure/ -f json -o security_report.json

# Dependency vulnerability scanner
pip install safety
safety check --json
```

### Penetration Testing

```bash
# OWASP ZAP
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://your-app.elasticbeanstalk.com

# Nikto web scanner
nikto -h https://your-app.elasticbeanstalk.com
```

### Secrets Scanning

```bash
# GitGuardian
pip install ggshield
ggshield secret scan repo .

# TruffleHog
docker run --rm -v $(pwd):/proj dxa4481/trufflehog \
  file:///proj --json
```

---

## Security Contacts

### Reporting Security Vulnerabilities

**Email:** security@yourdomain.com  
**PGP Key:** [Public key fingerprint]  
**Response Time:** 24 hours for critical issues

### Escalation

- **Critical:** Immediate response, page on-call engineer
- **High:** 4-hour response
- **Medium:** 24-hour response
- **Low:** 1-week response

---

**Last Updated:** 2025-10-02  
**Security Review:** Required quarterly  
**Status:** Security Hardening In Progress ⚠️

**Action Required:**
1. ✅ Rotate exposed AWS credentials IMMEDIATELY
2. ✅ Remove credentials from git history
3. ✅ Implement IAM roles for production
4. ✅ Enable HTTPS/TLS encryption
5. ✅ Set up security monitoring

**Related Documentation:**
- [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) - Secure configuration
- [CICD_DEVOPS_GUIDE.md](./CICD_DEVOPS_GUIDE.md) - Secure deployment
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Security issue resolution
