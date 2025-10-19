"""
Configuration management using Pydantic Settings
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # AWS Configuration
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCOUNT_ID: str = Field(default="")
    
    # Bedrock Configuration
    BEDROCK_MODEL_ID: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0")
    BEDROCK_AGENT_ID: str = Field(default="")
    BEDROCK_AGENT_ALIAS_ID: str = Field(default="")
    
    # Application Configuration
    APP_NAME: str = Field(default="DevOps-Intelligence-Agent")
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = Field(default="INFO")
    
    # API Configuration
    API_PORT: int = Field(default=8000)
    API_HOST: str = Field(default="0.0.0.0")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    # DynamoDB Tables
    DYNAMODB_CONVERSATIONS_TABLE: str = Field(default="devops-agent-conversations")
    DYNAMODB_SESSIONS_TABLE: str = Field(default="devops-agent-sessions")
    DYNAMODB_ACTIONS_TABLE: str = Field(default="devops-agent-actions")
    
    # S3 Buckets
    S3_KNOWLEDGE_BASE_BUCKET: str = Field(default="devops-agent-knowledge-base")
    S3_LOGS_BUCKET: str = Field(default="devops-agent-logs")
    
    # Feature Flags
    ENABLE_CODE_EXECUTION: bool = Field(default=True)
    ENABLE_AWS_ACTIONS: bool = Field(default=True)
    ENABLE_HUMAN_APPROVAL: bool = Field(default=True)
    REQUIRE_APPROVAL_FOR_DESTRUCTIVE: bool = Field(default=True)
    
    # Security
    JWT_SECRET_KEY: str = Field(default="change-me-in-production")
    API_KEY_SECRET_NAME: str = Field(default="devops-agent-api-keys")
    
    # External APIs
    GITHUB_TOKEN_SECRET: str = Field(default="")
    SLACK_WEBHOOK_URL_SECRET: str = Field(default="")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

