from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class LineContext:
    path: str
    line: int
    symbol: Optional[str]
    symbol_type: Optional[str]
    signature: Optional[str]


class ContextExtractor:
    """Calculates simple lexical context (enclosing class/function) for lines."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root)

    def _read_source(self, rel_path: str) -> str:
        file_path = self.repo_root / rel_path
        return file_path.read_text(encoding="utf-8")

    def _build_index(self, source: str) -> Dict[int, List[ast.AST]]:
        tree = ast.parse(source)
        index: Dict[int, List[ast.AST]] = {}

        def visit(node: ast.AST, stack: List[ast.AST]) -> None:
            if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                for line in range(node.lineno, getattr(node, "end_lineno", node.lineno) + 1):
                    index.setdefault(line, []).append(node)
            for child in ast.iter_child_nodes(node):
                visit(child, stack + [node])

        visit(tree, [])
        return index

    @staticmethod
    def _symbol_metadata(node: ast.AST) -> (Optional[str], Optional[str], Optional[str]):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            return node.name, "function", f"{node.name}({', '.join(args)})"
        if isinstance(node, ast.ClassDef):
            bases = [getattr(base, "id", "?") for base in node.bases]
            return node.name, "class", f"class {node.name}({', '.join(bases)})"
        return None, None, None

    def get_context(self, rel_path: str, lines: Iterable[int]) -> List[LineContext]:
        source = self._read_source(rel_path)
        index = self._build_index(source)
        results: List[LineContext] = []
        for line in lines:
            nodes = index.get(line, [])
            symbol = symbol_type = signature = None
            for node in reversed(nodes):
                symbol, symbol_type, signature = self._symbol_metadata(node)
                if symbol:
                    break
            results.append(
                LineContext(
                    path=rel_path,
                    line=line,
                    symbol=symbol,
                    symbol_type=symbol_type,
                    signature=signature,
                )
            )
        return results
