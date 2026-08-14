import mongoose from "mongoose";

// Raw commit data. Kept close to the GitHub API's own shape (with `raw`)
// so we never lose information the ML service might later need —
// this is exactly why we're using a document store instead of a fixed
// relational schema for this half of the system.
const commitSchema = new mongoose.Schema(
  {
    repo: { type: String, required: true, index: true },
    sha: { type: String, required: true, unique: true },
    author: String,
    message: String,
    filesChanged: Number,
    additions: Number,
    deletions: Number,
    committedAt: Date,
    raw: mongoose.Schema.Types.Mixed
  },
  { timestamps: true }
);

const pullRequestSchema = new mongoose.Schema(
  {
    repo: { type: String, required: true, index: true },
    number: { type: Number, required: true },
    title: String,
    author: String,
    state: String, // open | closed | merged
    additions: Number,
    deletions: Number,
    changedFiles: Number,
    createdAt: Date,
    mergedAt: Date,
    reviewComments: Number,
    riskScore: Number, // filled in later by the Python service
    raw: mongoose.Schema.Types.Mixed
  },
  { timestamps: true }
);

pullRequestSchema.index({ repo: 1, number: 1 }, { unique: true });

export const Commit = mongoose.model("Commit", commitSchema);
export const PullRequest = mongoose.model("PullRequest", pullRequestSchema);
