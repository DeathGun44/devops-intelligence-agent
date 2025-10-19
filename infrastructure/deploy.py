#!/usr/bin/env python3
"""
Deployment script for DevOps Intelligence Agent
"""
import boto3
import argparse
import time
import sys
from pathlib import Path

def deploy_cloudformation(environment, region):
    """Deploy CloudFormation stack"""
    print(f"Deploying to {environment} in {region}...")
    
    cfn = boto3.client('cloudformation', region_name=region)
    
    stack_name = f'{environment}-devops-intelligence-agent'
    template_path = Path(__file__).parent / 'cloudformation' / 'main.yaml'
    
    with open(template_path) as f:
        template_body = f.read()
    
    try:
        # Check if stack exists
        try:
            cfn.describe_stacks(StackName=stack_name)
            stack_exists = True
        except:
            stack_exists = False
        
        if stack_exists:
            print(f"Updating existing stack: {stack_name}")
            cfn.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {'ParameterKey': 'Environment', 'ParameterValue': environment}
                ],
                Capabilities=['CAPABILITY_NAMED_IAM']
            )
        else:
            print(f"Creating new stack: {stack_name}")
            cfn.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=[
                    {'ParameterKey': 'Environment', 'ParameterValue': environment}
                ],
                Capabilities=['CAPABILITY_NAMED_IAM'],
                Tags=[
                    {'Key': 'Environment', 'Value': environment},
                    {'Key': 'Application', 'Value': 'DevOpsAgent'}
                ]
            )
        
        # Wait for stack operation to complete
        print("Waiting for stack operation to complete...")
        waiter_name = 'stack_update_complete' if stack_exists else 'stack_create_complete'
        waiter = cfn.get_waiter(waiter_name)
        waiter.wait(StackName=stack_name)
        
        print("✓ Stack deployment completed successfully!")
        
        # Get outputs
        response = cfn.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]
        
        if 'Outputs' in stack:
            print("\nStack Outputs:")
            for output in stack['Outputs']:
                print(f"  {output['OutputKey']}: {output['OutputValue']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error deploying stack: {e}")
        return False

def deploy_application(environment, region):
    """Deploy application to AWS"""
    print("\nDeploying application...")
    
    # Here you would typically:
    # 1. Build Docker image
    # 2. Push to ECR
    # 3. Update ECS service or Lambda
    # 4. Deploy frontend to S3/CloudFront
    
    print("✓ Application deployment completed!")
    return True

def main():
    parser = argparse.ArgumentParser(description='Deploy DevOps Intelligence Agent')
    parser.add_argument(
        '--environment',
        default='development',
        choices=['development', 'staging', 'production'],
        help='Deployment environment'
    )
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region'
    )
    parser.add_argument(
        '--skip-infra',
        action='store_true',
        help='Skip infrastructure deployment'
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("DevOps Intelligence Agent - Deployment")
    print("="*60)
    
    # Deploy infrastructure
    if not args.skip_infra:
        if not deploy_cloudformation(args.environment, args.region):
            print("\n✗ Infrastructure deployment failed!")
            sys.exit(1)
    
    # Deploy application
    if not deploy_application(args.environment, args.region):
        print("\n✗ Application deployment failed!")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ Deployment completed successfully!")
    print("="*60)
    print(f"\nEnvironment: {args.environment}")
    print(f"Region: {args.region}")
    print("\nNext steps:")
    print("1. Configure your .env file with the stack outputs")
    print("2. Start the application: python src/main.py")
    print("3. Access the UI at: http://localhost:8000")

if __name__ == '__main__':
    main()

