# Quick Start Guide

Get the DevOps Intelligence Agent running in 5 minutes!

## Prerequisites

- AWS Account with Bedrock access
- Python 3.11+
- Node.js 18+

## Fastest Setup

### 1. Clone and Install

```bash
git clone https://github.com/yourusername/devops-intelligence-agent.git
cd devops-intelligence-agent

# Python backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..
```

### 2. Configure AWS

```bash
# Enable Bedrock models in AWS Console
# Then configure credentials
aws configure
```

### 3. Deploy Infrastructure

```bash
python infrastructure/deploy.py --environment development --region us-east-1
```

### 4. Setup Environment

```bash
cp .env.example .env
# Edit .env with your AWS details from CloudFormation outputs
```

### 5. Run

```bash
# Terminal 1: Backend
python src/main.py

# Terminal 2: Frontend
cd frontend && npm start
```

### 6. Use

Open `http://localhost:3000` and try:

- "List my EC2 instances"
- "Analyze my AWS costs"
- "Review this code: [paste code]"

## Docker Alternative

```bash
docker-compose up --build
```

Access at `http://localhost:3000`

## Need Help?

- 📖 Full Setup: [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)
- 🏗️ Architecture: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 🎬 Demo Script: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md)

## Test It Works

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status": "healthy", "service": "devops-intelligence-agent"}
```

## Example Queries

1. **Infrastructure**: "Show me all my AWS resources"
2. **Cost**: "What are my biggest cost drivers?"
3. **Code**: "Review this Python code for security issues"
4. **Troubleshooting**: "Why is my Lambda function timing out?"
5. **Deployment**: "Deploy my application to production"

## Common Issues

**Bedrock Access Denied**: Enable models in Bedrock console  
**Table Not Found**: Run CloudFormation deployment  
**Connection Refused**: Check both backend and frontend are running

---

**Ready to Build!** 🚀

For the hackathon submission, see [docs/SUBMISSION.md](docs/SUBMISSION.md)

