# Deploying RepoPulse to AWS

Two options are documented here. **Do the EC2 path first** — it's simpler,
genuinely how a lot of real MVPs get deployed, and gives you a working
demo URL fast. Only move to ECS/Fargate if you have time left and want a
stronger "I understand container orchestration" story for interviews.

Neither of these has been run against a live AWS account from this
environment (no AWS credentials/network access here) — treat the steps
as a correct, ready-to-follow template, but budget time to debug small
things when you actually run them.

---

## Option A: Single EC2 instance + Docker Compose (do this one)

This runs the exact same `docker-compose.yml` you already have, just on
a cloud box instead of your laptop.

1. **Launch an instance**
   - AMI: Amazon Linux 2023
   - Type: `t3.small` (t2.micro is too small for Mongo + two services)
   - Key pair: create/download one so you can SSH in
   - Security group: allow inbound
     - `22` (SSH) from your IP
     - `4000` (Node API) from anywhere, for the demo
     - `8000` (Python API) from anywhere, for the demo
   - Under "Advanced details → User data", paste `deploy/aws/ec2-user-data.sh`
     (edit the `git clone` line to point at your actual repo URL first,
     and push this project to GitHub if you haven't)

2. **Launch it, wait ~2 minutes**, then SSH in:
   ```bash
   ssh -i your-key.pem ec2-user@<instance-public-ip>
   ```

3. **Fill in the real env values** (the bootstrap script copies the
   `.env.example` files but doesn't have your GitHub token):
   ```bash
   cd repopulse-mvp
   nano node-service/.env   # paste your GitHub token
   docker compose up -d --build
   ```

4. **Verify:**
   ```bash
   curl http://<instance-public-ip>:4000/health
   curl http://<instance-public-ip>:8000/health
   ```

5. **Stop paying for it when you're not demoing it** — stop (not
   terminate, if you want to keep the disk) the instance from the EC2
   console. A `t3.small` running 24/7 is a real (small) cost.

This alone is legitimate, sayable AWS experience: EC2, security groups,
and deploying a multi-container app to it.

---

## Option B: ECR + ECS Fargate (stretch goal, more "production-grade")

Only attempt this if Option A works and you have time left. It's the
pattern larger companies actually use, so it's a stronger interview
story, but has real setup overhead (IAM roles, task definitions, a
VPC/subnet, a load balancer if you want one URL for both services).

High-level steps (not scripted here — this needs your AWS account's
specific IDs filled in):

1. Create two ECR repositories (`repopulse-node`, `repopulse-python`),
   build and push each image:
   ```bash
   aws ecr create-repository --repository-name repopulse-node
   aws ecr get-login-password | docker login --username AWS \
     --password-stdin <account-id>.dkr.ecr.<region>.amazonaws.com
   docker build -t <account-id>.dkr.ecr.<region>.amazonaws.com/repopulse-node ./node-service
   docker push <account-id>.dkr.ecr.<region>.amazonaws.com/repopulse-node
   # repeat for python-service
   ```
2. Create an ECS cluster (Fargate launch type).
3. Write a task definition per service (a starting template is in
   `deploy/aws/ecs-task-definition.node.json`) referencing the ECR
   image URIs and setting the same env vars as the `.env` files.
4. For MongoDB in this path, don't containerize it yourself — use
   **MongoDB Atlas's free tier** or **Amazon DocumentDB**. Running a
   stateful database in Fargate without persistent storage set up
   correctly is a common beginner mistake worth avoiding.
5. Create an ECS service per task definition, put an Application Load
   Balancer in front if you want stable URLs.

Be honest in interviews about which path you actually deployed —
"I deployed it on EC2 and documented the ECS/Fargate path as a next
step" is a completely respectable, true answer.
