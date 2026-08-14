#!/bin/bash
# EC2 user-data script (Amazon Linux 2023).
# Paste this into the "User data" field when launching the instance --
# it runs automatically on first boot and brings the whole stack up.

set -euxo pipefail

# 1. Install Docker + the Compose plugin
dnf update -y
dnf install -y docker git
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user

DOCKER_CONFIG=/usr/local/lib/docker/cli-plugins
mkdir -p $DOCKER_CONFIG
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o $DOCKER_CONFIG/docker-compose
chmod +x $DOCKER_CONFIG/docker-compose

# 2. Pull the project
cd /home/ec2-user
git clone https://github.com/aadhya-code/repopulse.git repopulse-mvp
cd repopulse-mvp

# 3. Env files -- fill these in before launch, or SSH in and edit them,
# then re-run `docker compose up -d --build` manually.
cp node-service/.env.example node-service/.env
cp python-service/.env.example python-service/.env
# sed -i 's/your_github_personal_access_token/PASTE_TOKEN_HERE/' node-service/.env

# 4. Bring the stack up
docker compose up -d --build
