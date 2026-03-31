from __future__ import annotations

import ast
import json
import uuid
from pathlib import Path
from typing import Any, Dict


class CodeExporter:
    def __init__(self, output_dir: str | Path = "outputs") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, code: Any, job_id: str | None = None) -> Dict[str, Any]:
        job_id = job_id or str(uuid.uuid4())[:8]

        file_path = self.output_dir / f"{job_id}{code.file_extension}"
        file_path.write_text(code.cleaned_code, encoding="utf-8")

        code_tree = self._build_code_tree(code)
        tree_path = self.output_dir / f"{job_id}_tree.json"
        tree_path.write_text(json.dumps(code_tree, indent=2), encoding="utf-8")

        return {
            "job_id": job_id,
            "file_path": str(file_path),
            "tree_path": str(tree_path),
            "code_tree": code_tree,
            "metadata": {
                "language": getattr(code.language, "value", str(code.language)),
                "confidence": round(float(code.confidence), 3),
                "line_count": len(code.cleaned_code.splitlines()),
                "file_size_bytes": len(code.cleaned_code.encode("utf-8")),
            },
        }

    def _build_code_tree(self, code: Any) -> Dict[str, Any]:
        if code.file_extension == ".py":
            return self._python_tree(code.cleaned_code)

        return {
            "type": "unsupported",
            "language": getattr(code.language, "value", str(code.language)),
        }

    def _python_tree(self, source: str) -> Dict[str, Any]:
        try:
            tree = ast.parse(source)
            return self._ast_to_dict(tree)
        except SyntaxError as exc:
            return {"type": "parse_error", "message": str(exc)}

    def _ast_to_dict(self, node: ast.AST) -> Dict[str, Any]:
        result: Dict[str, Any] = {"type": type(node).__name__}

        if isinstance(node, ast.FunctionDef):
            result["name"] = node.name
            result["args"] = [arg.arg for arg in node.args.args]
            result["lineno"] = node.lineno
            result["body"] = [self._ast_to_dict(n) for n in node.body]
        elif isinstance(node, ast.ClassDef):
            result["name"] = node.name
            result["lineno"] = node.lineno
            result["body"] = [self._ast_to_dict(n) for n in node.body]
        elif isinstance(node, ast.Module):
            result["body"] = [self._ast_to_dict(n) for n in node.body]

        return result
