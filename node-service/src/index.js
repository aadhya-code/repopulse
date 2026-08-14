import "dotenv/config";
import express from "express";
import cors from "cors";
import mongoose from "mongoose";
import { Commit, PullRequest } from "./models.js";
import { fetchCommits, fetchPullRequests } from "./github.js";

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 4000;
const MONGO_URI = process.env.MONGO_URI || "mongodb://localhost:27017/repopulse";

mongoose
  .connect(MONGO_URI)
  .then(() => console.log("[node-service] connected to MongoDB"))
  .catch((err) => {
    console.error("[node-service] MongoDB connection failed:", err.message);
    process.exit(1);
  });

app.get("/health", (_req, res) => res.json({ status: "ok" }));

/**
 * POST /ingest/:owner/:repo
 * Pulls recent commits + PRs for a repo from the GitHub API and
 * upserts them into MongoDB. This is the "ingestion" half of the system.
 */
app.post("/ingest/:owner/:repo", async (req, res) => {
  const ownerRepo = `${req.params.owner}/${req.params.repo}`;

  try {
    const [commits, pulls] = await Promise.all([
      fetchCommits(ownerRepo),
      fetchPullRequests(ownerRepo)
    ]);

    const commitOps = commits.map((c) => ({
      updateOne: {
        filter: { sha: c.sha },
        update: { $set: c },
        upsert: true
      }
    }));

    const prOps = pulls.map((p) => ({
      updateOne: {
        filter: { repo: p.repo, number: p.number },
        update: { $set: p },
        upsert: true
      }
    }));

    if (commitOps.length) await Commit.bulkWrite(commitOps);
    if (prOps.length) await PullRequest.bulkWrite(prOps);

    res.json({
      repo: ownerRepo,
      commitsIngested: commits.length,
      pullRequestsIngested: pulls.length
    });
  } catch (err) {
    console.error("[ingest] failed:", err.message);
    res.status(502).json({ error: "Failed to ingest from GitHub", detail: err.message });
  }
});

// GET /repos/:owner/:repo/commits
app.get("/repos/:owner/:repo/commits", async (req, res) => {
  const repo = `${req.params.owner}/${req.params.repo}`;
  const commits = await Commit.find({ repo }).sort({ committedAt: -1 }).limit(100);
  res.json(commits);
});

// GET /repos/:owner/:repo/pulls
app.get("/repos/:owner/:repo/pulls", async (req, res) => {
  const repo = `${req.params.owner}/${req.params.repo}`;
  const pulls = await PullRequest.find({ repo }).sort({ createdAt: -1 }).limit(100);
  res.json(pulls);
});

/**
 * PATCH /repos/:owner/:repo/pulls/:number/risk
 * Called by the Python service to write back a computed risk score.
 */
app.patch("/repos/:owner/:repo/pulls/:number/risk", async (req, res) => {
  const repo = `${req.params.owner}/${req.params.repo}`;
  const { riskScore } = req.body;

  const updated = await PullRequest.findOneAndUpdate(
    { repo, number: Number(req.params.number) },
    { $set: { riskScore } },
    { new: true }
  );

  if (!updated) return res.status(404).json({ error: "PR not found" });
  res.json(updated);
});

app.listen(PORT, () => console.log(`[node-service] listening on port ${PORT}`));
