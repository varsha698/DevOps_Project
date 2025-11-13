# Production-Grade Flask DevOps Project

A comprehensive DevOps pipeline demonstrating industry best practices for deploying a Flask application on AWS with full CI/CD, monitoring, and scaling capabilities.

## 🚀 Features

### Infrastructure
- **Terraform** - Infrastructure as Code (VPC, ALB, Auto Scaling, RDS, ECR)
- **Application Load Balancer** - High availability and load distribution
- **Auto Scaling Group** - Automatic scaling based on CPU/memory metrics
- **RDS PostgreSQL** - Managed database with automated backups
- **ECR** - Container registry for Docker images

### Application
- **Flask** - Python web framework
- **Gunicorn** - Production WSGI server
- **PostgreSQL** - Relational database with SQLAlchemy ORM
- **NGINX** - Reverse proxy and load balancer
- **Docker** - Containerization with multi-stage builds

### CI/CD
- **GitHub Actions** - Automated CI/CD pipeline
  - Code linting (flake8, black)
  - Unit tests with pytest
  - Docker image build
  - Push to AWS ECR
  - Automated deployment via Ansible

### Deployment Options
- **Ansible** - Configuration management and deployment
- **Docker Compose** - Local development and testing
- **Kubernetes** - Container orchestration (manifests included)

### Monitoring & Alerting
- **CloudWatch** - Logs, metrics, and dashboards
- **CloudWatch Alarms** - CPU, memory, error rate monitoring
- **SNS** - Alert notifications
- **Slack Integration** - Real-time alert notifications

## 📋 Prerequisites

- AWS Account with appropriate IAM permissions
- Terraform >= 1.0
- Ansible >= 2.9
- Docker & Docker Compose
- Python 3.9+
- kubectl (for Kubernetes deployment)
- GitHub repository with Actions enabled

## 🏗️ Architecture

```
Internet
   │
   ▼
[Application Load Balancer]
   │
   ├─── [Auto Scaling Group]
   │       │
   ├─── [EC2 Instance 1] ──┐
   ├─── [EC2 Instance 2] ──┤
   └─── [EC2 Instance N] ───┘
           │
           ├─── [Docker Container: Flask App]
           │       │
           │       └─── [RDS PostgreSQL]
           │
           └─── [CloudWatch Logs]
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/DevOps_Project.git
cd DevOps_Project
```

### 2. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter default region (e.g., us-east-1)
```

### 3. Set Up Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

Required variables in `terraform.tfvars`:
```hcl
aws_region      = "us-east-1"
project_name    = "flask-app"
db_password     = "YOUR_SECURE_PASSWORD_HERE"
```

### 4. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This will create:
- VPC with public/private subnets
- Application Load Balancer
- Auto Scaling Group
- RDS PostgreSQL database
- ECR repository
- Security groups
- IAM roles and policies

**Note:** Save the Terraform outputs (especially `alb_dns_name` and `rds_endpoint`) for later use.

### 5. Configure GitHub Secrets

In your GitHub repository, go to Settings → Secrets and add:

- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `EC2_HOST` - Your EC2 instance IP (from Terraform output)
- `SSH_PRIVATE_KEY` - Your SSH private key for EC2 access
- `DB_HOST` - RDS endpoint (from Terraform output)
- `DB_PORT` - RDS port (usually 5432)
- `DB_NAME` - Database name (from terraform.tfvars)
- `DB_USER` - Database username
- `DB_PASSWORD` - Database password

### 6. Build and Push Docker Image Manually (First Time)

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t flask-app .

# Tag image
docker tag flask-app:latest YOUR_ECR_REGISTRY/flask-app:latest

# Push to ECR
docker push YOUR_ECR_REGISTRY/flask-app:latest
```

### 7. Deploy with Ansible

```bash
cd ansible-deploy

# Update inventory.ini with your EC2 instance IP
# Update playbook.yml variables if needed

ansible-playbook -i inventory.ini playbook.yml \
  -e "ecr_registry=YOUR_ECR_REGISTRY" \
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

### 8. Access Your Application

After deployment, access your application via the ALB DNS name:

```bash
# Get ALB DNS from Terraform output
terraform output alb_dns_name

# Or access directly
curl http://YOUR_ALB_DNS_NAME
```

## 🧪 Local Development

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Access application
curl http://localhost
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (EKS, GKE, or local with minikube)
- kubectl configured
- Docker image pushed to ECR (or another registry)

### Deploy to Kubernetes

```bash
cd k8s

# Update flask-deployment.yaml with your ECR registry
# Update secret.yaml with your database credentials

# Create namespace
kubectl apply -f namespace.yaml

# Create secrets and configmaps
kubectl apply -f secret.yaml
kubectl apply -f configmap.yaml

# Deploy PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Deploy Flask app
kubectl apply -f flask-deployment.yaml

# Deploy NGINX
kubectl apply -f nginx-deployment.yaml

# Check status
kubectl get all -n flask-app

# Get service URL
kubectl get svc nginx-service -n flask-app
```

## 📊 Monitoring Setup

### CloudWatch Dashboard

1. Go to AWS CloudWatch Console
2. Create a new dashboard
3. Import the JSON from `monitoring/cloudwatch-dashboard.json`

### CloudWatch Alarms

```bash
cd monitoring

# Update variables in cloudwatch-alarms-variables.tf
# Set your ASG name, ALB ARN suffix, RDS instance ID

terraform init
terraform apply
```

### Slack Integration

1. Create a Slack webhook URL:
   - Go to https://api.slack.com/apps
   - Create a new app
   - Enable Incoming Webhooks
   - Create a webhook URL

2. Update `monitoring/cloudwatch-alarms-variables.tf`:
   ```hcl
   slack_webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. Apply Terraform:
   ```bash
   cd monitoring
   terraform apply
   ```

## 🔧 Configuration

### Environment Variables

The Flask application uses the following environment variables:

- `DB_HOST` - Database host (default: localhost)
- `DB_PORT` - Database port (default: 5432)
- `DB_NAME` - Database name (default: flaskapp)
- `DB_USER` - Database user (default: postgres)
- `DB_PASSWORD` - Database password
- `AWS_REGION` - AWS region (default: us-east-1)

### Application Endpoints

- `GET /` - Main endpoint, logs visits to database
- `GET /health` - Health check endpoint
- `GET /visits` - Get recent visits (last 10)

## 📁 Project Structure

```
.
├── app.py                      # Flask application
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Local development setup
├── requirements.txt            # Python dependencies
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # GitHub Actions CI/CD
├── ansible-deploy/
│   ├── inventory.ini          # Ansible inventory
│   └── playbook.yml           # Deployment playbook
├── terraform/
│   ├── main.tf                # Main infrastructure
│   ├── variables.tf           # Variable definitions
│   ├── outputs.tf             # Output values
│   ├── user_data.sh           # EC2 user data script
│   └── terraform.tfvars.example
├── nginx/
│   ├── nginx.conf             # NGINX configuration
│   └── Dockerfile             # NGINX Docker image
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── postgres-deployment.yaml
│   ├── flask-deployment.yaml
│   └── nginx-deployment.yaml
├── monitoring/
│   ├── cloudwatch-alarms.tf
│   ├── cloudwatch-alarms-variables.tf
│   ├── slack_notifier.py
│   └── cloudwatch-dashboard.json
└── tests/
    ├── __init__.py
    └── test_app.py            # Unit tests
```

## 🔐 Security Best Practices

1. **Secrets Management**
   - Use AWS Secrets Manager or Parameter Store for production
   - Never commit secrets to version control
   - Use environment variables or secret management tools

2. **Network Security**
   - Application runs in private subnets
   - Security groups restrict access
   - RDS is not publicly accessible

3. **Container Security**
   - Multi-stage Docker builds
   - Non-root user in containers
   - Regular security scanning

4. **IAM**
   - Least privilege principle
   - Separate IAM roles for different services
   - Use IAM roles instead of access keys where possible

## 🚨 Troubleshooting

### Application not accessible

1. Check ALB target group health:
   ```bash
   aws elbv2 describe-target-health --target-group-arn YOUR_TG_ARN
   ```

2. Check EC2 instance logs:
   ```bash
   ssh -i your-key.pem ubuntu@EC2_IP
   docker logs flask-app
   ```

3. Check CloudWatch logs:
   - Go to CloudWatch → Log Groups → `/ec2/flask-app`

### Database connection issues

1. Verify RDS security group allows access from app security group
2. Check RDS endpoint and credentials
3. Test connection from EC2 instance:
   ```bash
   psql -h RDS_ENDPOINT -U postgres -d flaskapp
   ```

### CI/CD pipeline failures

1. Check GitHub Actions logs
2. Verify all secrets are set correctly
3. Ensure ECR repository exists
4. Check IAM permissions for GitHub Actions

## 📈 Scaling

### Manual Scaling

Update Auto Scaling Group:
```bash
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name flask-app-asg \
  --desired-capacity 5
```

### Auto Scaling

Auto Scaling is configured to:
- Scale up when CPU > 70% for 2 periods
- Scale down when CPU < 20% for 2 periods

Adjust thresholds in `terraform/main.tf` if needed.

## 🧹 Cleanup

To destroy all resources:

```bash
cd terraform
terraform destroy
```

**Warning:** This will delete all infrastructure including the database. Make sure to backup any important data first.

## 📝 Next Steps / Future Enhancements

- [ ] Add SSL/TLS certificates (ACM + HTTPS listener)
- [ ] Implement blue-green deployments
- [ ] Add Redis for caching
- [ ] Set up CI/CD for Kubernetes deployments
- [ ] Add distributed tracing (AWS X-Ray)
- [ ] Implement canary deployments
- [ ] Add frontend application (React/Vue)
- [ ] Set up S3 + CloudFront for static assets
- [ ] Implement service mesh (Istio/Linkerd)
- [ ] Add chaos engineering tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 👤 Author

Your Name - [GitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Flask community
- AWS documentation
- Terraform community
- Ansible community

---

**Note:** This is a demonstration project. For production use, ensure you:
- Use proper secrets management
- Enable encryption at rest and in transit
- Set up proper backup strategies
- Configure appropriate monitoring and alerting
- Follow your organization's security policies
