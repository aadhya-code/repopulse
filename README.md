# RepoPulse
> AI-powered GitHub repository analytics platform for semantic commit search and machine-learning-based pull request risk scoring.

## 🚀 Live Deployment

RepoPulse is deployed on an Azure VM using Docker Compose.

| Service | Live URL |
|---|---|
| Node.js API | http://20.197.28.7:4000 |
| Python/FastAPI API | http://20.197.28.7:8000 |

### Health Checks

- Node.js API: http://20.197.28.7:4000/health
- Python/FastAPI API: http://20.197.28.7:8000/health

The deployed services have been tested successfully from an external machine.

### Verified Deployment

- GitHub repository ingestion: tested with `facebook/react`
- Commits ingested: 30
- Pull requests ingested: 32
- Semantic search: tested successfully
- PR risk scoring: 32 PRs scored
- Risk scores persisted: 32/32 PRs
- Non-zero risk scores: 11/32 PRs
- Docker Compose services: MongoDB, Node.js, and Python/FastAPI
- Deployment platform: Microsoft Azure

An AI-powered GitHub repository analytics platform that ingests repository
activity, enables natural-language semantic search over commit history, and
scores pull requests for potential risk.

RepoPulse is implemented as a containerized microservice architecture using
Node.js/Express, MongoDB, Python/FastAPI, Hugging Face embeddings, FAISS,
LangChain, and scikit-learn.

## Architecture

```text
                         GitHub API
                             |
                             v
                  +----------------------+
                  | Node.js / Express    |
                  | GitHub ingestion     |
                  | Port 4000            |
                  +----------+-----------+
                             |
                             v
                  +----------------------+
                  | MongoDB              |
                  | Commits + PRs        |
                  +----------+-----------+
                             |
                    +--------+--------+
                    |                 |
                    v                 v
          +----------------+   +----------------+
          | Python/FastAPI |   | PR Risk Model  |
          | Port 8000      |   | Random Forest  |
          +-------+--------+   +-------+--------+
                  |                    |
                  v                    v
          Hugging Face + FAISS    Risk Scores
          Semantic Search         -> MongoDB
Services
Service	Port	Responsibility
node-service	4000	GitHub API communication, repository ingestion, MongoDB writes, REST API
python-service	8000	Semantic search, embeddings, FAISS indexing, PR risk scoring
mongo	27017	Stores raw commit and pull-request data
Technology Stack
Backend: Node.js, Express, Python, FastAPI
Database: MongoDB
Semantic Search: LangChain, Hugging Face Sentence Transformers, FAISS
Machine Learning: scikit-learn Random Forest
Data Processing: Pandas, NumPy
Visualization: Matplotlib
Containerization: Docker, Docker Compose
Cloud Deployment: Microsoft Azure VM
Source Control: Git, GitHub
Core Workflow
1. Ingest GitHub repository data

The Node.js service communicates with the GitHub REST API and stores
commits and pull requests in MongoDB.

curl -X POST http://localhost:4000/ingest/facebook/react

Example tested result:

{
  "repo": "facebook/react",
  "commitsIngested": 30,
  "pullRequestsIngested": 30
}
2. Build semantic search index

The Python service reads the stored commits, generates embeddings using
Hugging Face sentence-transformer models, and builds a FAISS vector index.

curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"repo":"facebook/react"}'

Example tested result:

{
  "repo": "facebook/react",
  "commitsIndexed": 30
}
3. Search repository history using natural language
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "repo":"facebook/react",
    "query":"What changes were made to the project documentation?",
    "k":3
  }'

The service returns ranked commits based on semantic similarity.

Example tested results included commits such as:

Improve project documentation
Initial project structure
Improve README documentation
4. Score pull requests for risk

The Python service trains a Random Forest classifier using structural PR
features and produces a risk score between 0 and 1.

curl -X POST http://localhost:8000/risk/facebook/react

Example tested result:

{
  "repo": "facebook/react",
  "scored": 30
}
5. Verify risk scores in MongoDB

The Node.js API exposes the stored PR records:

curl http://localhost:4000/repos/facebook/react/pulls

The tested deployment returned PRs with persisted riskScore values,
including examples such as 0.56, 0.60, 0.09, 0.11, and 0.03.

Tested Deployment

RepoPulse has been deployed and tested on a Microsoft Azure VM using
Docker Compose.

The deployed services expose:

Node.js / Express : 4000
Python / FastAPI  : 8000
MongoDB           : 27017

Health checks were verified successfully:

curl http://localhost:4000/health
curl http://localhost:8000/health

Both services return:

{
  "status": "ok"
}

The public Azure deployment was also tested externally through the VM's
public IP for:

GitHub repository ingestion
Semantic indexing
Natural-language semantic search
Pull-request risk scoring
Reading persisted PR risk scores
Running Locally

Create the environment files:

cp node-service/.env.example node-service/.env
cp python-service/.env.example python-service/.env

Add the required credentials to the environment files.

For the Node.js service, configure the GitHub personal access token:

GITHUB_TOKEN=your_github_personal_access_token
PORT=4000

Then start the complete stack:

docker compose up --build

Check the running containers:

docker compose ps

Expected services:

repopulse-mongo
repopulse-node
repopulse-python
API Endpoints
Node.js Service
Health Check
GET /health
Ingest Repository
POST /ingest/:owner/:repo

Example:

curl -X POST http://localhost:4000/ingest/facebook/react
Get Pull Requests
GET /repos/:owner/:repo/pulls

Example:

curl http://localhost:4000/repos/facebook/react/pulls
Python Service
Health Check
GET /health
Build Semantic Index
POST /index

Example:

curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"repo":"facebook/react"}'
Semantic Search
POST /search

Example:

curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "repo":"facebook/react",
    "query":"changes to the scheduler",
    "k":3
  }'
PR Risk Scoring
POST /risk/:owner/:repo

Example:

curl -X POST http://localhost:8000/risk/facebook/react
Verified MVP Metrics

The following values were observed during testing:

Metric	Verified Value
Repository tested	facebook/react
Commits ingested	30
Pull requests ingested	30
Commits indexed	30
Pull requests scored	30
Containers	3
Cloud deployment	Azure VM
Semantic search	Tested
PR risk scoring	Tested
Risk scores persisted to MongoDB	Tested

A second repository, aadhya-code/llmguard, was also tested:

Metric	Verified Value
Repository	aadhya-code/llmguard
Commits ingested	4
Pull requests ingested	0
Commits indexed	4
Semantic search	Tested
PR Risk Model

The current model uses a Random Forest classifier with the following
structural PR features:

additions
deletions
changedFiles
reviewComments

The current implementation bootstraps training labels using a heuristic:
a PR is labelled as risky when it is relatively large and has low review
density.

This allows the complete ingestion → feature extraction → model training
→ scoring → MongoDB persistence pipeline to be demonstrated.

Honest Limitations
Risk-model labels

The current PR risk classifier uses a bootstrapped heuristic label, not
ground-truth bug/outcome labels.

A PR is currently labelled as risky when it is relatively large and
under-reviewed.

Therefore, the current model demonstrates the complete ML pipeline but its
reported test accuracy should not be presented as real-world predictive
accuracy.

For production evaluation, the heuristic should be replaced with real
outcome labels, such as:

PRs later reverted
PRs linked to bug-fix issues
PRs followed by corrective/hotfix commits
PRs associated with production incidents
Authentication

The MVP API endpoints are currently unauthenticated. A production version
should add authentication and authorization, potentially using GitHub OAuth.

Frontend

RepoPulse is currently API-first and does not include a frontend dashboard.
A React/Next.js dashboard can be added as a future layer on top of the APIs.

Scale

The current implementation is an MVP and has primarily been tested using
recent repository activity rather than a large historical GitHub dataset.

Production scaling would require pagination, background ingestion jobs,
persistent vector-index management, monitoring, authentication, and
additional caching.

Deployment

The repository contains deployment documentation for cloud environments:

deploy/azure/ — Azure VM deployment used and tested for RepoPulse
deploy/aws/ — AWS deployment configuration and deployment path

The verified cloud deployment for this project is Microsoft Azure.

The application runs as three Docker Compose services:

MongoDB
   |
   +---- Node.js / Express
   |
   +---- Python / FastAPI
Security Notes

Environment files containing credentials are intentionally excluded from
Git using .gitignore.

Do not commit:

.env
*.pem
private keys
GitHub personal access tokens

Use environment variables or a proper secret-management service for
production deployments.

Future Improvements
React/Next.js analytics dashboard
GitHub OAuth authentication
Real PR outcome labels for risk-model training
Larger historical datasets
Precision, recall, F1-score, and ROC-AUC evaluation using real labels
GitHub Actions CI/CD
PostgreSQL for aggregated analytics
Production monitoring and logging
Background repository ingestion jobs
Persistent FAISS index storage
API authentication and rate limiting
Container orchestration beyond Docker Compose
Project Status

MVP completed and deployed on Azure.

The core RepoPulse pipeline has been implemented and tested end-to-end:

GitHub Repository
       ↓
GitHub API Ingestion
       ↓
MongoDB
       ↓
 ┌─────┴─────┐
 ↓           ↓
Semantic    PR Risk
Search      Scoring
 ↓           ↓
FAISS      Random Forest
 ↓           ↓
Search     Risk Scores
Results      ↓
          MongoDB
The current project is API-first. Frontend development, production
authentication, larger-scale evaluation, and real-world PR outcome labels
remain future improvements.
