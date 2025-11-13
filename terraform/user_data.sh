#!/bin/bash
set -e

# Update system
apt-get update
apt-get install -y docker.io awscli python3-pip

# Start Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
dpkg -i -E ./amazon-cloudwatch-agent.deb

# Login to ECR
aws ecr get-login-password --region ${aws_region} | docker login --username AWS --password-stdin ${ecr_registry} || true

# Pull and run the application
docker pull ${ecr_registry}/${app_name}:latest || true

# Stop existing container if running
docker stop ${app_name} || true
docker rm ${app_name} || true

# Run the container
docker run -d \
  --name ${app_name} \
  --restart always \
  -p 5000:5000 \
  -e DB_HOST=${db_host} \
  -e DB_PORT=${db_port} \
  -e DB_NAME=${db_name} \
  -e DB_USER=${db_user} \
  -e DB_PASSWORD=${db_password} \
  -e AWS_REGION=${aws_region} \
  --log-driver awslogs \
  --log-opt awslogs-group=/ec2/flask-app \
  --log-opt awslogs-region=${aws_region} \
  --log-opt awslogs-stream=${app_name}-$(hostname) \
  ${ecr_registry}/${app_name}:latest

# Health check script
cat > /usr/local/bin/health-check.sh << 'EOF'
#!/bin/bash
if ! docker ps | grep -q flask-app; then
  docker start flask-app
fi
EOF
chmod +x /usr/local/bin/health-check.sh

# Add to crontab for health checks
(crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/health-check.sh") | crontab -

