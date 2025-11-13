# Step-by-Step Setup Guide

This guide walks you through setting up the entire DevOps pipeline from scratch.

## Phase 1: Initial Setup

### 1.1 Prerequisites Installation

```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://www.terraform.io/downloads

# Install Ansible
pip install ansible

# Install AWS CLI
pip install awscli
# or brew install awscli

# Verify installations
terraform version
ansible --version
aws --version
```

### 1.2 AWS Account Setup

1. Create an AWS account if you don't have one
2. Create an IAM user with programmatic access
3. Attach policies:
   - `AmazonEC2FullAccess`
   - `AmazonRDSFullAccess`
   - `AmazonVPCFullAccess`
   - `AmazonEC2ContainerRegistryFullAccess`
   - `CloudWatchFullAccess`
   - `IAMFullAccess` (or create custom policy with least privilege)

4. Configure AWS CLI:
```bash
aws configure
```

### 1.3 GitHub Repository Setup

1. Create a new GitHub repository
2. Push this code to the repository
3. Enable GitHub Actions in repository settings

## Phase 2: Infrastructure Deployment

### 2.1 Configure Terraform

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
aws_region      = "us-east-1"
project_name    = "flask-app"
vpc_cidr        = "10.0.0.0/16"
instance_type   = "t3.micro"
min_size        = 1
max_size        = 3
desired_capacity = 2
db_instance_class = "db.t3.micro"
db_name         = "flaskapp"
db_username     = "postgres"
db_password     = "YOUR_SECURE_PASSWORD_HERE"  # Change this!
```

### 2.2 Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan  # Review the plan
terraform apply  # Type 'yes' when prompted
```

**Important:** Save the outputs:
- `alb_dns_name` - You'll need this to access your app
- `rds_endpoint` - Database connection endpoint
- `ecr_repository_url` - Container registry URL

### 2.3 Create ECR Repository (if not created by Terraform)

```bash
aws ecr create-repository --repository-name flask-app --region us-east-1
```

## Phase 3: Build and Push Docker Image

### 3.1 Get ECR Login

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
```

### 3.2 Build and Push Image

```bash
cd ..  # Back to project root

# Build image
docker build -t flask-app .

# Tag for ECR
docker tag flask-app:latest \
  ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest

# Push to ECR
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest
```

## Phase 4: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

1. **AWS_ACCESS_KEY_ID** - Your AWS access key
2. **AWS_SECRET_ACCESS_KEY** - Your AWS secret key
3. **EC2_HOST** - Get from Terraform output or AWS Console
4. **SSH_PRIVATE_KEY** - Your SSH private key content (for EC2 access)
5. **DB_HOST** - RDS endpoint from Terraform output
6. **DB_PORT** - `5432`
7. **DB_NAME** - `flaskapp` (or from terraform.tfvars)
8. **DB_USER** - `postgres` (or from terraform.tfvars)
9. **DB_PASSWORD** - Your database password

## Phase 5: Configure Ansible

### 5.1 Update Inventory

Edit `ansible-deploy/inventory.ini`:
```ini
[web]
YOUR_EC2_IP ansible_user=ubuntu ansible_ssh_private_key_file=~/path/to/your-key.pem
```

### 5.2 Test Ansible Connection

```bash
cd ansible-deploy
ansible -i inventory.ini web -m ping
```

## Phase 6: First Manual Deployment

### 6.1 Deploy with Ansible

```bash
cd ansible-deploy

ansible-playbook -i inventory.ini playbook.yml \
  -e "ecr_registry=${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com" \
  -e "image_tag=latest" \
  -e "aws_access_key_id=YOUR_AWS_KEY" \
  -e "aws_secret_access_key=YOUR_AWS_SECRET" \
  -e "db_host=YOUR_RDS_ENDPOINT" \
  -e "db_port=5432" \
  -e "db_name=flaskapp" \
  -e "db_user=postgres" \
  -e "db_password=YOUR_DB_PASSWORD" \
  -e "aws_region=us-east-1"
```

### 6.2 Verify Deployment

```bash
# Get ALB DNS from Terraform
cd terraform
terraform output alb_dns_name

# Test the application
curl http://YOUR_ALB_DNS_NAME
curl http://YOUR_ALB_DNS_NAME/health
```

## Phase 7: Set Up Monitoring

### 7.1 Create CloudWatch Dashboard

1. Go to AWS CloudWatch Console
2. Click "Dashboards" → "Create dashboard"
3. Name it "Flask-App-Dashboard"
4. Click "Add widget" → "Custom widget"
5. Import JSON from `monitoring/cloudwatch-dashboard.json`

### 7.2 Set Up CloudWatch Alarms

```bash
cd monitoring

# Update variables
# Edit cloudwatch-alarms-variables.tf or create terraform.tfvars

terraform init
terraform apply
```

### 7.3 Set Up Slack Alerts (Optional)

1. Create Slack webhook:
   - Go to https://api.slack.com/apps
   - Create new app
   - Enable "Incoming Webhooks"
   - Create webhook URL

2. Update `monitoring/cloudwatch-alarms-variables.tf`:
   ```hcl
   slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. Apply:
   ```bash
   terraform apply
   ```

## Phase 8: Test CI/CD Pipeline

### 8.1 Make a Change

```bash
# Edit app.py
echo "# Test change" >> app.py
git add .
git commit -m "Test CI/CD pipeline"
git push origin main
```

### 8.2 Monitor GitHub Actions

1. Go to your GitHub repository
2. Click "Actions" tab
3. Watch the pipeline run:
   - Lint
   - Test
   - Build
   - Deploy

### 8.3 Verify Deployment

After pipeline completes:
```bash
curl http://YOUR_ALB_DNS_NAME
```

## Phase 9: Local Development Setup

### 9.1 Using Docker Compose

```bash
# Create .env file
cat > .env << EOF
DB_NAME=flaskapp
DB_USER=postgres
DB_PASSWORD=postgres
AWS_REGION=us-east-1
EOF

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Test
curl http://localhost
```

## Phase 10: Kubernetes Deployment (Optional)

### 10.1 Prerequisites

- Kubernetes cluster (EKS, GKE, or minikube)
- kubectl configured

### 10.2 Update Kubernetes Manifests

1. Edit `k8s/flask-deployment.yaml`:
   - Replace `YOUR_ECR_REGISTRY` with your ECR URL

2. Edit `k8s/secret.yaml`:
   - Update database credentials

### 10.3 Deploy

```bash
cd k8s
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f flask-deployment.yaml
kubectl apply -f nginx-deployment.yaml

# Check status
kubectl get all -n flask-app

# Get service URL
kubectl get svc nginx-service -n flask-app
```

## Troubleshooting Common Issues

### Issue: Terraform fails with permission errors

**Solution:** Ensure your IAM user has the required permissions listed in Phase 1.2

### Issue: Docker push fails

**Solution:** 
- Verify ECR login
- Check repository exists: `aws ecr describe-repositories`
- Ensure image is tagged correctly

### Issue: Ansible can't connect to EC2

**Solution:**
- Verify security group allows SSH from your IP
- Check SSH key permissions: `chmod 400 your-key.pem`
- Verify inventory.ini has correct IP and key path

### Issue: Application returns 502 Bad Gateway

**Solution:**
- Check target group health in ALB
- SSH to EC2 and check container: `docker ps` and `docker logs flask-app`
- Verify database connection from EC2

### Issue: GitHub Actions fails

**Solution:**
- Verify all secrets are set correctly
- Check AWS credentials have proper permissions
- Verify ECR repository exists

## Next Steps

1. **Add SSL/TLS:**
   - Request ACM certificate
   - Update ALB listener to HTTPS
   - Redirect HTTP to HTTPS

2. **Improve Security:**
   - Use AWS Secrets Manager for passwords
   - Enable VPC Flow Logs
   - Set up AWS WAF

3. **Add More Features:**
   - Implement authentication
   - Add more API endpoints
   - Set up Redis caching

4. **Optimize Costs:**
   - Use Reserved Instances
   - Set up cost alerts
   - Review and optimize resource sizes

## Cleanup

When you're done testing:

```bash
cd terraform
terraform destroy  # This will delete everything!
```

**Warning:** This permanently deletes all resources including the database. Backup any important data first.

