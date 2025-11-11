from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List

import requests

from core import utils


API_ROOT = "https://api.github.com"


def load_examples(path: Path) -> List[Dict]:
    items: List[Dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                items.append(json.loads(line))
    return items


def call_model(endpoint: str, payload: Dict) -> str:
    resp = requests.post(f"{endpoint}/review", json=payload, timeout=30)
    if resp.status_code >= 400:
        raise utils.PullPalError(f"Inference request failed: {resp.text}")
    return resp.json()["comment"]


def post_comment(owner: str, repo: str, pr: int, body: str, example: Dict, commit_id: str) -> None:
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr}/comments"
    headers = utils.github_headers()
    data = {
        "body": body,
        "path": example["path"],
        "line": example["line"],
        "side": "RIGHT",
        "commit_id": commit_id,
    }
    resp = requests.post(url, headers=headers, json=data, timeout=30)
    if resp.status_code >= 400:
        raise utils.PullPalError(f"Failed to post comment: {resp.text}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Send Pull Pal suggestions to GitHub PR comments.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--endpoint", required=True, help="Base URL for the FastAPI service.")
    parser.add_argument("--limit", type=int, default=5, help="Max comments to post.")
    args = parser.parse_args()

    examples = load_examples(args.examples)[: args.limit]
    metadata = utils.load_json(args.metadata)
    commit_id = metadata["head"]["sha"]

    for example in examples:
        comment = call_model(args.endpoint, example)
        post_comment(args.owner, args.repo, args.pr, comment, example, commit_id)
        print(f"Posted review for {example['path']}:{example['line']}")


if __name__ == "__main__":
    main()
