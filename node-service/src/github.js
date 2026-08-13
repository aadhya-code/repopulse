import axios from "axios";

const GITHUB_API = "https://api.github.com";

function client() {
  return axios.create({
    baseURL: GITHUB_API,
    headers: {
      Accept: "application/vnd.github+json",
      ...(process.env.GITHUB_TOKEN && {
        Authorization: `Bearer ${process.env.GITHUB_TOKEN}`
      })
    }
  });
}

// owner/repo e.g. "facebook/react"
export async function fetchCommits(ownerRepo, perPage = 30) {
  const api = client();
  const { data } = await api.get(`/repos/${ownerRepo}/commits`, {
    params: { per_page: perPage }
  });

  return data.map((c) => ({
    repo: ownerRepo,
    sha: c.sha,
    author: c.commit?.author?.name || "unknown",
    message: c.commit?.message || "",
    committedAt: c.commit?.author?.date ? new Date(c.commit.author.date) : null,
    raw: c
  }));
}

export async function fetchPullRequests(ownerRepo, perPage = 30) {
  const api = client();
  const { data } = await api.get(`/repos/${ownerRepo}/pulls`, {
    params: { state: "all", per_page: perPage }
  });

  // The list endpoint doesn't include diff stats, so we fetch each PR's
  // detail to get additions/deletions/changedFiles.
  const detailed = await Promise.all(
    data.map(async (pr) => {
      const { data: full } = await api.get(
        `/repos/${ownerRepo}/pulls/${pr.number}`
      );
      return {
        repo: ownerRepo,
        number: full.number,
        title: full.title,
        author: full.user?.login || "unknown",
        state: full.merged_at ? "merged" : full.state,
        additions: full.additions,
        deletions: full.deletions,
        changedFiles: full.changed_files,
        createdAt: full.created_at ? new Date(full.created_at) : null,
        mergedAt: full.merged_at ? new Date(full.merged_at) : null,
        reviewComments: full.review_comments,
        raw: full
      };
    })
  );

  return detailed;
}
