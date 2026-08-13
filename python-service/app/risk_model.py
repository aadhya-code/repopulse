"""
PR risk classifier.

Predicts whether a pull request is "risky" (large, sparsely reviewed
changes that are statistically more likely to need follow-up fixes)
based on structural features pulled from GitHub.

IMPORTANT / honest caveat for the README and for interviews:
We don't have ground-truth labels (e.g. "this PR caused a bug") out of
the box, so this module bootstraps labels with a documented heuristic
(see `heuristic_label`) purely to make the pipeline end-to-end runnable
and demonstrable. Before presenting real accuracy numbers, replace
`heuristic_label` with actual outcomes you collect -- e.g. PRs that were
later reverted, or PRs linked to a hotfix/bug-label issue. Say this
explicitly if asked in an interview; it's a legitimate, common approach
to bootstrapping a supervised model before real labels exist, but only
if you're upfront about it.
"""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import matplotlib

matplotlib.use("Agg")  # headless, since this runs in a container
import matplotlib.pyplot as plt

from app.db import pulls_collection

FEATURE_COLUMNS = ["additions", "deletions", "changedFiles", "reviewComments"]


@dataclass
class TrainedModel:
    model: RandomForestClassifier
    accuracy: float
    report: str
    feature_importance_path: str


def _load_dataframe(repo: str) -> pd.DataFrame:
    docs = list(pulls_collection.find({"repo": repo}))
    if not docs:
        return pd.DataFrame(columns=FEATURE_COLUMNS)

    df = pd.DataFrame(docs)
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0
    df[FEATURE_COLUMNS] = df[FEATURE_COLUMNS].fillna(0)
    return df


def heuristic_label(row: pd.Series) -> int:
    """
    Bootstrap label: 1 (risky) if the PR is large and under-reviewed.
    Replace this with real outcome data once you have it (see module docstring).
    """
    size = row["additions"] + row["deletions"]
    review_density = row["reviewComments"] / max(row["changedFiles"], 1)
    return int(size > 300 and review_density < 1)


def train(repo: str) -> Optional[TrainedModel]:
    df = _load_dataframe(repo)
    if len(df) < 10:
        return None  # not enough data to train meaningfully

    df["label"] = df.apply(heuristic_label, axis=1)

    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y = df["label"].to_numpy()

    if len(np.unique(y)) < 2:
        return None  # need both classes present

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    accuracy = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, zero_division=0)

    # Feature importance chart -- demonstrates matplotlib usage and gives
    # something concrete to show in the README / a demo.
    fig, ax = plt.subplots()
    ax.barh(FEATURE_COLUMNS, clf.feature_importances_)
    ax.set_xlabel("Importance")
    ax.set_title(f"PR risk model feature importance ({repo})")
    fig.tight_layout()
    chart_path = f"/tmp/{repo.replace('/', '_')}_feature_importance.png"
    fig.savefig(chart_path)
    plt.close(fig)

    return TrainedModel(
        model=clf, accuracy=accuracy, report=report, feature_importance_path=chart_path
    )


def score_all(repo: str) -> List[dict]:
    """Train on the repo's PRs and return a risk score (0-1) for each one."""
    trained = train(repo)
    if trained is None:
        return []

    df = _load_dataframe(repo)
    X = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    probs = trained.model.predict_proba(X)[:, 1] if len(df) else []

    return [
        {"number": int(row["number"]), "riskScore": float(prob)}
        for row, prob in zip(df.to_dict("records"), probs)
    ]
