from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

from git import Repo

from core import utils
from core.ast_context import ContextExtractor


def ensure_repo(metadata: Dict, repo_dir: Path) -> Path:
    repo_dir = Path(repo_dir)
    clone_url = metadata["head"]["repo"]["clone_url"]
    commit = metadata["head"]["sha"]
    if repo_dir.exists():
        repo = Repo(repo_dir)
        repo.git.fetch("--all")
    else:
        repo = Repo.clone_from(clone_url, repo_dir)
    repo.git.checkout(commit, force=True)
    return repo_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich diff summary with AST context.")
    parser.add_argument("--summary", type=Path, required=True, help="Path to diff_summary.json")
    parser.add_argument("--metadata", type=Path, required=True, help="Path to metadata.json from fetch_pr")
    parser.add_argument("--repo-dir", type=Path, default=None, help="Existing clone to reuse.")
    parser.add_argument("--out", type=Path, default=None, help="Output file (defaults to diff_with_ctx.json next to summary).")
    args = parser.parse_args()

    summary = utils.load_json(args.summary)
    metadata = utils.load_json(args.metadata)
    repo_dir = args.repo_dir or (args.summary.parent / "repo")
    repo_root = ensure_repo(metadata, repo_dir)
    extractor = ContextExtractor(repo_root)

    enriched_files: List[Dict] = []
    for file_entry in summary["files"]:
        path = file_entry["path"]
        added_lines = file_entry.get("added_lines", [])
        if not path.endswith(".py") or not added_lines:
            enriched_files.append({**file_entry, "contexts": []})
            continue
        contexts = extractor.get_context(path, sorted(set(added_lines)))
        enriched_files.append({**file_entry, "contexts": [ctx.__dict__ for ctx in contexts]})

    out_path = args.out or (args.summary.parent / "diff_with_ctx.json")
    utils.dump_json({"files": enriched_files}, out_path)
    print(f"Wrote context-enriched diff to {out_path}")


if __name__ == "__main__":
    main()
