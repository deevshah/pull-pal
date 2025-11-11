from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from core import utils


def load_contexts(ctx_path: Path) -> Dict[Tuple[str, int], Dict]:
    ctx_json = utils.load_json(ctx_path)
    mapping: Dict[Tuple[str, int], Dict] = {}
    for file_entry in ctx_json["files"]:
        for ctx in file_entry.get("contexts", []):
            mapping[(ctx["path"], ctx["line"])] = ctx
    return mapping


def hunk_string(lines: Iterable[Dict]) -> str:
    rows = []
    for line in lines:
        prefix = "+" if line["type"] == "add" else "-" if line["type"] == "del" else " "
        rows.append(f"{prefix}{line['text']}")
    return "\n".join(rows)


def build_examples(diff_path: Path, ctx_path: Path, comments_path: Path) -> List[Dict]:
    diff = utils.load_json(diff_path)
    ctx_lookup = load_contexts(ctx_path)
    comments = utils.load_json(comments_path)

    file_map = {file_entry["path"]: file_entry for file_entry in diff["files"]}
    examples: List[Dict] = []
    for comment in comments:
        path = comment.get("path")
        line = comment.get("line")
        if path not in file_map or line is None:
            continue
        file_entry = file_map[path]
        hunk = _find_hunk(file_entry["hunks"], line)
        if not hunk:
            continue
        lint_hits = [warn for warn in file_entry.get("lint", []) if warn["line"] == line]
        context = ctx_lookup.get((path, line))
        examples.append(
            {
                "path": path,
                "line": line,
                "comment": comment.get("body", ""),
                "diff_hunk": hunk_string(hunk["lines"]),
                "context": context,
                "lint": lint_hits,
            }
        )
    return examples


def _find_hunk(hunks: List[Dict], line: int) -> Optional[Dict]:
    for hunk in hunks:
        for entry in hunk["lines"]:
            if entry["target"] == line:
                return hunk
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Match enriched diffs to review comments for training examples.")
    parser.add_argument("--diff", type=Path, required=True, help="Path to diff_with_lint.json")
    parser.add_argument("--ctx", type=Path, required=True, help="Path to diff_with_ctx.json")
    parser.add_argument("--comments", type=Path, required=True, help="Path to pull_comments.json")
    parser.add_argument("--out", type=Path, default=None, help="Output JSONL file path.")
    args = parser.parse_args()

    examples = build_examples(args.diff, args.ctx, args.comments)
    out_path = args.out or (args.comments.parent / "examples.jsonl")
    utils.dump_jsonl(examples, out_path)
    print(f"Wrote {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    main()
