from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

from unidiff import PatchSet

from core import utils


def summarize_diff(patch_text: str) -> Dict[str, List[Dict[str, List[int]]]]:
    patch = PatchSet(patch_text)
    files_summary = []
    files_full = []

    for patched_file in patch:
        added_lines = [
            line.target_line_no
            for hunk in patched_file
            for line in hunk
            if line.is_added and line.target_line_no is not None
        ]
        removed_lines = [
            line.source_line_no
            for hunk in patched_file
            for line in hunk
            if line.is_removed and line.source_line_no is not None
        ]
        files_summary.append(
            {
                "path": patched_file.path,
                "added_lines": added_lines,
                "removed_lines": removed_lines,
            }
        )
        files_full.append(
            {
                "path": patched_file.path,
                "hunks": [
                    {
                        "target_start": hunk.target_start,
                        "target_length": hunk.target_length,
                        "source_start": hunk.source_start,
                        "source_length": hunk.source_length,
                        "lines": [
                            {
                                "type": "add" if line.is_added else "del" if line.is_removed else "ctx",
                                "source": line.source_line_no,
                                "target": line.target_line_no,
                                "text": line.value.rstrip("\n"),
                            }
                            for line in hunk
                        ],
                    }
                    for hunk in patched_file
                ],
            }
        )
    return {"files": files_summary}, {"files": files_full}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse a PR diff patch into JSON summaries.")
    parser.add_argument("patch", type=Path, help="Path to diff.patch file.")
    parser.add_argument("--out-dir", type=Path, default=None, help="Directory for parsed artifacts.")
    args = parser.parse_args()

    patch_path = args.patch
    out_dir = args.out_dir or patch_path.parent
    patch_text = utils.read_patch(patch_path)

    summary, full = summarize_diff(patch_text)
    utils.dump_json(summary, Path(out_dir) / "diff_summary.json")
    utils.dump_json(full, Path(out_dir) / "diff_full.json")
    print(f"Wrote summaries to {out_dir}")


if __name__ == "__main__":
    main()
