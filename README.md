# RepoPulse (MVP)

An AI-powered developer productivity tool: ingest a GitHub repo's commits
and pull requests, ask natural-language questions about its history via a
LangChain + Hugging Face semantic search agent, and get a risk score for
each PR from a scikit-learn classifier — all running as three containers
via Docker Compose.

## Why this architecture

- **Node.js + Express (ingestion)** — GitHub activity is webhook/event-shaped
  and I/O bound (waiting on the GitHub API), which is what Node's
  event loop is good at. This service owns talking to GitHub.
- **MongoDB** — commits and PRs from the GitHub API are irregularly shaped
  JSON blobs. Storing them as documents avoids forcing a rigid schema on
  data that isn't naturally relational.
- **Python + FastAPI (AI/ML)** — all the AI/ML tooling (LangChain, Hugging
  Face, scikit-learn, pandas) lives in the Python ecosystem, so the ML
  logic is isolated in its own service rather than shoehorned into Node.
- **Docker Compose** — one command (`docker compose up`) brings up Mongo +
  both services with the right network wiring, instead of three sets of
  manual setup instructions.

## Services

| Service | Port | Responsibility |
|---|---|---|
| `node-service` | 4000 | Fetches commits/PRs from the GitHub API, stores them in MongoDB, exposes REST endpoints |
| `python-service` | 8000 | Semantic search (LangChain + Hugging Face) and PR risk scoring (scikit-learn) |
| `mongo` | 27017 | Document store for raw GitHub data |

## Running it

```bash
cp node-service/.env.example node-service/.env
cp python-service/.env.example python-service/.env
# edit node-service/.env and add a GitHub personal access token
# (unauthenticated GitHub API calls are heavily rate-limited)

docker compose up --build
```

## Example workflow

```bash
# 1. Ingest a repo's recent commits and PRs
curl -X POST http://localhost:4000/ingest/facebook/react

# 2. Build the semantic search index from the ingested commits
curl -X POST http://localhost:8000/index \
  -H "Content-Type: application/json" \
  -d '{"repo": "facebook/react"}'

# 3. Ask a natural-language question about the repo's history
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"repo": "facebook/react", "query": "changes to the scheduler"}'

# 4. Train the risk classifier and score every PR
curl -X POST http://localhost:8000/risk/facebook/react

# 5. Read back the scored PRs
curl http://localhost:4000/repos/facebook/react/pulls
```

## Deploying it

Runs locally via Docker Compose by default. For a real deployment (EC2,
plus a documented stretch path to ECS/Fargate), see
[`deploy/aws/README.md`](deploy/aws/README.md).

## Honest limitations (read before demoing this)

- **The risk model's labels are a bootstrapped heuristic, not real
  outcomes.** `python-service/app/risk_model.py` labels a PR "risky" if
  it's large and under-reviewed — a reasonable starting proxy, but not
  ground truth. Before quoting an accuracy number in an interview,
  either say clearly that it's trained on a heuristic label, or replace
  it with real data (e.g. PRs that were later reverted, or linked to a
  bug-tracker issue).
- **No auth.** The ingestion endpoint is unauthenticated for MVP
  simplicity. A real version would put GitHub OAuth in front of it.
- **No frontend yet.** Everything here is API-first; a dashboard is a
  natural next step, not included in this MVP.
- **AWS deployment is documented but not run from this environment.**
  `deploy/aws/` has a ready-to-follow EC2 path and an ECS/Fargate
  stretch-goal path. Actually launch and test the EC2 path yourself
  before claiming "deployed on AWS" anywhere — see that folder's README
  for the honest caveat on what's been verified vs. templated.

## Possible next steps

- React/Next.js dashboard for the search bar + risk score list
- PostgreSQL for aggregated analytics (keeping Mongo for raw data only)
- GitHub Actions CI to lint/test both services and build the images
- Replace the heuristic label with real PR-outcome data
- Move from the EC2 path to the ECS/Fargate path in `deploy/aws/`
