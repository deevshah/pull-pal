from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

import requests

from core import utils


API_ROOT = "https://api.github.com"


def fetch_pr(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}"
    return utils.github_get(url)


def fetch_patch(owner: str, repo: str, pr_number: int) -> bytes:
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}"
    headers = utils.github_headers()
    headers["Accept"] = "application/vnd.github.v3.patch"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code >= 400:
        raise utils.PullPalError(f"Failed to download patch: {resp.text}")
    return resp.content


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch GitHub PR metadata and diff patch.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--out", type=Path, default=None, help="Optional override for output directory.")
    args = parser.parse_args()

    ref = utils.RepoRef(owner=args.owner, repo=args.repo, pr=args.pr)
    out_dir = Path(args.out) if args.out else ref.pr_dir
    utils.ensure_dir(out_dir)

    metadata = fetch_pr(args.owner, args.repo, args.pr)
    patch_bytes = fetch_patch(args.owner, args.repo, args.pr)

    utils.dump_json(metadata, out_dir / "metadata.json")
    (out_dir / "diff.patch").write_bytes(patch_bytes)
    print(f"Saved PR #{args.pr} metadata and diff to {out_dir}")


if __name__ == "__main__":
    main()
