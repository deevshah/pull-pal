from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


DEFAULT_DATA_DIR = Path("data")


class PullPalError(RuntimeError):
    """Base exception for domain specific failures."""


@dataclass
class RepoRef:
    owner: str
    repo: str
    pr: int

    @property
    def slug(self) -> str:
        safe_owner = self.owner.replace("/", "_").replace(" ", "-")
        safe_repo = self.repo.replace("/", "_").replace(" ", "-")
        return f"{safe_owner}_{safe_repo}"

    @property
    def pr_dir(self) -> Path:
        return DEFAULT_DATA_DIR / "raw" / self.slug / f"pr_{self.pr}"


def getenv_token() -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise PullPalError("GITHUB_TOKEN missing; export it before running scripts.")
    return token


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(payload: Any, path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)


def dump_jsonl(records: Iterable[Dict[str, Any]], path: Path) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as fh:
        for row in records:
            fh.write(json.dumps(row))
            fh.write("\n")


def run(cmd: List[str], *, cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and proc.returncode != 0:
        raise PullPalError(f"Command {' '.join(cmd)} failed: {proc.stderr.strip()}")
    return proc


def github_headers(token: Optional[str] = None) -> Dict[str, str]:
    token = token or getenv_token()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pull-pal/0.1",
    }


def github_get(url: str, *, params: Optional[Dict[str, Any]] = None, token: Optional[str] = None) -> Dict[str, Any]:
    resp = requests.get(url, headers=github_headers(token), params=params, timeout=30)
    if resp.status_code >= 400:
        raise PullPalError(f"GitHub request failed ({resp.status_code}): {resp.text}")
    return resp.json()


def github_get_binary(url: str, *, token: Optional[str] = None) -> bytes:
    resp = requests.get(url, headers=github_headers(token), timeout=30)
    if resp.status_code >= 400:
        raise PullPalError(f"GitHub request failed ({resp.status_code}): {resp.text}")
    return resp.content


def read_patch(path: Path) -> str:
    with path.open("r", encoding="utf-8") as fh:
        return fh.read()


def chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def filter_python_files(paths: Iterable[str]) -> List[str]:
    return [p for p in paths if p.endswith(".py")]
