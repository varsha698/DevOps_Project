# Quick Start Guide - How to Run

This is a simplified guide to get you running quickly. For detailed explanations, see `SETUP_GUIDE.md`.

## Prerequisites Check

```bash
# Check if you have these installed
terraform version    # Should show >= 1.0
ansible --version    # Should show >= 2.9
docker --version     # Should show Docker installed
aws --version        # Should show AWS CLI installed
python3 --version    # Should show Python 3.9+
```

If any are missing, install them first.

## Step 1: Configure AWS

```bash
# Set up AWS credentials
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key  
# Enter default region (e.g., us-east-1)
# Enter default output format (just press Enter for json)
```

## Step 2: Deploy Infrastructure with Terraform

```bash
# Go to terraform directory
cd terraform

# Copy and edit the variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars - IMPORTANT: Change the db_password!
nano terraform.tfvars  # or use your preferred editor
```

**Edit these values in `terraform.tfvars`:**
```hcl
aws_region      = "us-east-1"           # Your AWS region
project_name    = "flask-app"
db_password     = "CHANGE_THIS_PASSWORD"  # ⚠️ CHANGE THIS!
```

```bash
# Initialize Terraform
terraform init

# Review what will be created
terraform plan

# Deploy everything (this takes 10-15 minutes)
terraform apply
# Type 'yes' when prompted
```

**⚠️ IMPORTANT:** Save the outputs! You'll see:
- `alb_dns_name` - Your app URL
- `rds_endpoint` - Database endpoint
- `ecr_repository_url` - Container registry URL

```bash
# Save outputs to a file
terraform output > ../terraform-outputs.txt
```

## Step 3: Build and Push Docker Image

```bash
# Go back to project root
cd ..

# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Your Account ID: $ACCOUNT_ID"

# Login to ECR (Amazon Container Registry)
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com

# Build the Docker image
docker build -t flask-app .

# Tag it for ECR
docker tag flask-app:latest \
  ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest

# Push to ECR (this may take a few minutes)
docker push ${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/flask-app:latest
```

## Step 4: Get EC2 Instance IP

After Terraform completes, you need the EC2 instance IP:

```bash
# Option 1: From Terraform output
cd terraform
terraform output

# Option 2: From AWS Console
# Go to EC2 → Instances → Find instance with name "flask-app-asg-instance"
# Copy the Private IP or Public IP

# Option 3: Using AWS CLI
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=flask-app-asg-instance" \
  --query "Reservations[*].Instances[*].[PublicIpAddress,PrivateIpAddress]" \
  --output table
```

## Step 5: Update Ansible Inventory

```bash
# Edit the inventory file
cd ../ansible-deploy
nano inventory.ini  # or use your preferred editor
```

**Update `inventory.ini` with your EC2 IP:**
```ini
[web]
YOUR_EC2_IP_HERE ansible_user=ubuntu ansible_ssh_private_key_file=~/path/to/your-key.pem
```

**If you don't have an SSH key:**
```bash
# Create a new key pair
aws ec2 create-key-pair --key-name flask-app-key --query 'KeyMaterial' --output text > ~/flask-app-key.pem
chmod 400 ~/flask-app-key.pem

# Then update inventory.ini to use: ~/flask-app-key.pem
```

## Step 6: Deploy with Ansible

```bash
# Get your values ready
ECR_REGISTRY="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
RDS_ENDPOINT=$(cd ../terraform && terraform output -raw rds_endpoint)
DB_PASSWORD=$(cd ../terraform && grep db_password terraform.tfvars | cut -d'"' -f2)

# Run Ansible playbook
ansible-playbook -i inventory.ini playbook.yml \
  -e "ecr_registry=${ECR_REGISTRY}" \
  -e "image_tag=latest" \
  -e "aws_access_key_id=$(aws configure get aws_access_key_id)" \
  -e "aws_secret_access_key=$(aws configure get aws_secret_access_key)" \
  -e "db_host=${RDS_ENDPOINT}" \
  -e "db_port=5432" \
  -e "db_name=flaskapp" \
  -e "db_user=postgres" \
  -e "db_password=${DB_PASSWORD}" \
  -e "aws_region=us-east-1"
```

**If Ansible can't connect:**
- Make sure your security group allows SSH from your IP
- Check the EC2 instance is running
- Verify the SSH key path is correct

## Step 7: Test Your Application

```bash
# Get the ALB DNS name
cd ../terraform
ALB_DNS=$(terraform output -raw alb_dns_name)
echo "Your app URL: http://${ALB_DNS}"

# Test it
curl http://${ALB_DNS}
curl http://${ALB_DNS}/health
curl http://${ALB_DNS}/visits
```

**Open in browser:**
```
http://YOUR_ALB_DNS_NAME
```

## Step 8: Set Up GitHub Actions (Optional but Recommended)

This enables automatic deployments when you push code.

1. **Push code to GitHub:**
```bash
cd ..
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

2. **Add GitHub Secrets:**
   - Go to your GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add these secrets:

| Secret Name | Value |
|------------|-------|
| `AWS_ACCESS_KEY_ID` | Your AWS access key |
| `AWS_SECRET_ACCESS_KEY` | Your AWS secret key |
| `EC2_HOST` | Your EC2 instance IP |
| `SSH_PRIVATE_KEY` | Contents of your SSH private key file |
| `DB_HOST` | RDS endpoint (from terraform output) |
| `DB_PORT` | `5432` |
| `DB_NAME` | `flaskapp` |
| `DB_USER` | `postgres` |
| `DB_PASSWORD` | Your database password |

3. **Test CI/CD:**
```bash
# Make a small change
echo "# Test" >> app.py
git add .
git commit -m "Test CI/CD"
git push
```

4. **Watch the pipeline:**
   - Go to GitHub → Actions tab
   - Watch your pipeline run!

## Alternative: Run Locally with Docker Compose

If you want to test locally first (without AWS):

```bash
# Create .env file
cat > .env << EOF
DB_NAME=flaskapp
DB_USER=postgres
DB_PASSWORD=postgres
AWS_REGION=us-east-1
EOF

# Start everything
docker-compose up -d

# Check logs
docker-compose logs -f

# Test
curl http://localhost
curl http://localhost/health

# Stop everything
docker-compose down
```

## Troubleshooting

### Terraform fails
- Check AWS credentials: `aws sts get-caller-identity`
- Verify you have required IAM permissions
- Check your region is correct

### Docker push fails
- Make sure you're logged into ECR
- Verify ECR repository exists: `aws ecr describe-repositories`
- Check image is tagged correctly

### Ansible can't connect
- Verify EC2 instance is running
- Check security group allows SSH from your IP
- Test SSH manually: `ssh -i your-key.pem ubuntu@EC2_IP`

### App returns 502 or not accessible
- Check ALB target group health in AWS Console
- SSH to EC2: `ssh -i your-key.pem ubuntu@EC2_IP`
- Check container: `docker ps` and `docker logs flask-app`
- Check database connection

### Database connection errors
- Verify RDS endpoint is correct
- Check security group allows access from app security group
- Test connection: `psql -h RDS_ENDPOINT -U postgres -d flaskapp`

## Quick Commands Reference

```bash
# View Terraform outputs
cd terraform && terraform output

# View running containers on EC2
ssh -i your-key.pem ubuntu@EC2_IP "docker ps"

# View application logs
ssh -i your-key.pem ubuntu@EC2_IP "docker logs flask-app"

# Restart container
ssh -i your-key.pem ubuntu@EC2_IP "docker restart flask-app"

# View CloudWatch logs
aws logs tail /ec2/flask-app --follow

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn YOUR_TG_ARN
```

## What's Next?

Once everything is running:
1. ✅ Your app is accessible via ALB DNS name
2. ✅ Auto-scaling is configured
3. ✅ Database is connected
4. ✅ Monitoring is set up (CloudWatch)
5. ✅ CI/CD is ready (after GitHub setup)

**Next steps:**
- Set up CloudWatch alarms (see `monitoring/` directory)
- Add Slack notifications
- Set up custom domain with SSL
- Review and optimize costs

## Need Help?

- Check `README.md` for detailed documentation
- Check `SETUP_GUIDE.md` for step-by-step instructions
- Check `IMPLEMENTATION_SUMMARY.md` for what was built

---

**Estimated Time:** 30-45 minutes for full setup
**Cost:** ~$50-100/month for AWS resources

