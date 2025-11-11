from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

from core import utils


def run_flake8(repo_root: Path, rel_path: str) -> List[Dict]:
    formatted = "%(path)s::%(row)d::%(code)s::%(text)s"
    cmd = ["flake8", f"--format={formatted}", rel_path]
    proc = utils.run(cmd, cwd=repo_root, check=False)
    if proc.returncode not in (0, 1):
        raise utils.PullPalError(proc.stderr.strip())
    warnings: List[Dict] = []
    for line in proc.stdout.strip().splitlines():
        parts = line.split("::", 3)
        if len(parts) != 4:
            continue
        path, row, code, text = parts
        warnings.append(
            {
                "path": path,
                "line": int(row),
                "code": code,
                "message": text,
            }
        )
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach lint warnings to diff JSON.")
    parser.add_argument("--diff", type=Path, required=True, help="Path to diff_full.json")
    parser.add_argument("--repo-dir", type=Path, default=None, help="Repo checkout containing files.")
    parser.add_argument("--out", type=Path, default=None, help="Output file (defaults to diff_with_lint.json).")
    args = parser.parse_args()

    diff_full = utils.load_json(args.diff)
    repo_root = args.repo_dir or (args.diff.parent / "repo")

    for file_entry in diff_full["files"]:
        path = file_entry["path"]
        if not path.endswith(".py"):
            file_entry["lint"] = []
            continue
        changed_lines = {
            line["target"]
            for hunk in file_entry["hunks"]
            for line in hunk["lines"]
            if line["type"] == "add" and line["target"] is not None
        }
        lints = [warn for warn in run_flake8(Path(repo_root), path) if warn["line"] in changed_lines]
        file_entry["lint"] = lints

    out_path = args.out or (args.diff.parent / "diff_with_lint.json")
    utils.dump_json(diff_full, out_path)
    print(f"Wrote lint-enriched diff to {out_path}")


if __name__ == "__main__":
    main()
