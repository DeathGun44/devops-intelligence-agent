# DevOps Intelligence Agent - Setup Guide

## Prerequisites

Before you begin, ensure you have:

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Python 3.11+** installed
4. **Node.js 18+** and npm installed
5. **Docker** (optional, for containerized deployment)
6. **Git** for version control

## AWS Services Required

Ensure you have access to:
- AWS Bedrock (with model access enabled)
- Amazon DynamoDB
- Amazon S3
- AWS Lambda (optional)
- AWS Secrets Manager
- Amazon CloudWatch

## Step-by-Step Setup

### 1. Enable AWS Bedrock Models

```bash
# Navigate to AWS Bedrock console
# Enable model access for:
# - Anthropic Claude 3 Sonnet
# - Amazon Nova Pro (if available)

# Or use AWS CLI
aws bedrock list-foundation-models --region us-east-1
```

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/devops-intelligence-agent.git
cd devops-intelligence-agent
```

### 3. Deploy AWS Infrastructure

```bash
# Deploy using CloudFormation
cd infrastructure
python deploy.py --environment development --region us-east-1

# Or manually deploy
aws cloudformation create-stack \
  --stack-name devops-agent-dev \
  --template-body file://cloudformation/main.yaml \
  --parameters ParameterKey=Environment,ParameterValue=development \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### 4. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your AWS configuration
nano .env
```

Required environment variables:
```bash
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

DYNAMODB_CONVERSATIONS_TABLE=development-devops-agent-conversations
DYNAMODB_SESSIONS_TABLE=development-devops-agent-sessions
DYNAMODB_ACTIONS_TABLE=development-devops-agent-actions

S3_KNOWLEDGE_BASE_BUCKET=development-devops-agent-knowledge-base-your-account-id
S3_LOGS_BUCKET=development-devops-agent-logs-your-account-id
```

### 5. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
cp .env.example .env
# Edit .env
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env
```

### 7. Run the Application

#### Option A: Local Development

Terminal 1 (Backend):
```bash
# From project root
python src/main.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

Access the application at: `http://localhost:3000`

#### Option B: Docker Compose

```bash
# From project root
docker-compose up --build
```

Access the application at: `http://localhost:3000`

### 8. Verify Setup

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "devops-intelligence-agent"
}
```

## Configuration Options

### Feature Flags

In `.env`, you can enable/disable features:

```bash
ENABLE_CODE_EXECUTION=true          # Allow code execution
ENABLE_AWS_ACTIONS=true             # Allow AWS resource modifications
ENABLE_HUMAN_APPROVAL=true          # Require approval for critical actions
REQUIRE_APPROVAL_FOR_DESTRUCTIVE=true  # Always approve destructive actions
```

### Model Selection

Choose your preferred LLM:

```bash
# Claude 3 Sonnet (recommended)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Claude 3 Haiku (faster, cheaper)
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Nova Pro (AWS native)
BEDROCK_MODEL_ID=amazon.nova-pro-v1:0
```

### Logging

Configure logging level:

```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## Troubleshooting

### Issue: Bedrock Access Denied

**Solution**: Ensure you've enabled model access in the Bedrock console.

```bash
# Check model access
aws bedrock list-foundation-models --region us-east-1
```

### Issue: DynamoDB Table Not Found

**Solution**: Ensure CloudFormation stack deployed successfully.

```bash
# Check stack status
aws cloudformation describe-stacks --stack-name devops-agent-dev
```

### Issue: Frontend Can't Connect to Backend

**Solution**: Check CORS configuration and API URL.

In `.env`:
```bash
CORS_ORIGINS=["http://localhost:3000"]
```

In `frontend/.env`:
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
```

### Issue: AWS Credentials Not Found

**Solution**: Configure AWS CLI credentials.

```bash
aws configure
# Enter your:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

## Production Deployment

### 1. Build Docker Images

```bash
# Backend
docker build -t devops-agent-backend .

# Frontend
cd frontend
docker build -t devops-agent-frontend .
```

### 2. Push to Amazon ECR

```bash
# Create ECR repositories
aws ecr create-repository --repository-name devops-agent-backend
aws ecr create-repository --repository-name devops-agent-frontend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  your-account-id.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag devops-agent-backend:latest \
  your-account-id.dkr.ecr.us-east-1.amazonaws.com/devops-agent-backend:latest
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/devops-agent-backend:latest

docker tag devops-agent-frontend:latest \
  your-account-id.dkr.ecr.us-east-1.amazonaws.com/devops-agent-frontend:latest
docker push your-account-id.dkr.ecr.us-east-1.amazonaws.com/devops-agent-frontend:latest
```

### 3. Deploy to ECS/Lambda

Follow AWS documentation for:
- ECS Fargate deployment
- Lambda containerized functions
- API Gateway configuration
- CloudFront distribution

### 4. Configure Custom Domain

```bash
# Request SSL certificate
aws acm request-certificate \
  --domain-name yourdomain.com \
  --validation-method DNS

# Update CloudFront/Load Balancer with certificate
```

## Next Steps

1. **Populate Knowledge Base**: Upload documentation to S3 knowledge base bucket
2. **Configure Integrations**: Add GitHub tokens, Slack webhooks to Secrets Manager
3. **Set Up Monitoring**: Create CloudWatch dashboards
4. **Enable Backup**: Configure DynamoDB point-in-time recovery
5. **Test Agent**: Run through example scenarios

## Support

For issues or questions:
- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review [Architecture Documentation](ARCHITECTURE.md)
- Open an issue on GitHub
- Contact the team

## Security Notes

🔒 **Important Security Practices:**

1. Never commit `.env` files to version control
2. Rotate AWS credentials regularly
3. Use IAM roles with least privilege
4. Enable MFA for AWS accounts
5. Review CloudWatch logs regularly
6. Keep dependencies updated

## Performance Optimization

For better performance:

1. **Use CloudFront**: Cache static assets
2. **Enable DynamoDB DAX**: In-memory caching
3. **Optimize Model Selection**: Use Haiku for simple queries
4. **Implement Caching**: Cache frequent queries
5. **Parallel Processing**: Execute independent tools in parallel

## Cost Management

Monitor and optimize costs:

1. **Use AWS Cost Explorer**: Track spending
2. **Set Billing Alerts**: Get notified of unusual costs
3. **Right-size Resources**: Match capacity to demand
4. **Use Spot Instances**: For non-critical workloads
5. **Enable Auto-scaling**: Scale down when not in use

---

**Ready to go!** 🚀

Start the agent and ask: "List my AWS resources and suggest optimizations"

