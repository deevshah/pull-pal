from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import requests

from core import utils


API_ROOT = "https://api.github.com"


def fetch_comments(owner: str, repo: str, pr_number: int) -> List[Dict]:
    page = 1
    comments: List[Dict] = []
    headers = utils.github_headers()
    while True:
        params = {"per_page": 100, "page": page}
        url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code >= 400:
            raise utils.PullPalError(f"GitHub comment fetch failed: {resp.text}")
        batch = resp.json()
        if not batch:
            break
        comments.extend(batch)
        if "next" not in _parse_link_header(resp.headers.get("Link")):
            break
        page += 1
    valid = [c for c in comments if c.get("path") and c.get("line")]
    return valid


def _parse_link_header(link_header: Optional[str]) -> Dict[str, str]:
    links: Dict[str, str] = {}
    if not link_header:
        return links
    for part in link_header.split(","):
        section = part.strip().split(";")
        if len(section) != 2:
            continue
        url = section[0].strip()[1:-1]
        rel = section[1].split("=")[1].strip().strip('"')
        links[rel] = url
    return links


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch review comments from a GitHub PR.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    comments = fetch_comments(args.owner, args.repo, args.pr)
    ref = utils.RepoRef(args.owner, args.repo, args.pr)
    out_path = args.out or (ref.pr_dir / "pull_comments.json")
    utils.dump_json(comments, out_path)
    print(f"Saved {len(comments)} comments to {out_path}")


if __name__ == "__main__":
    main()
