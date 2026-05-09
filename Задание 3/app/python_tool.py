from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path


BLOCKED_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "shutil",
    "pathlib",
}
BLOCKED_CALLS = {"eval", "exec", "compile", "open", "__import__", "input"}
MAX_CODE_CHARS = 7000


class SafetyVisitor(ast.NodeVisitor):
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in BLOCKED_IMPORTS:
                raise ValueError(f"Import '{root}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".")[0]
        if root in BLOCKED_IMPORTS:
            raise ValueError(f"Import '{root}' is not allowed.")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            raise ValueError(f"Call '{node.func.id}' is not allowed.")
        if isinstance(node.func, ast.Attribute) and node.func.attr in {"system", "popen", "remove", "unlink", "rmdir"}:
            raise ValueError(f"Call '*.{node.func.attr}' is not allowed.")
        self.generic_visit(node)


def validate_code(code: str) -> None:
    if len(code) > MAX_CODE_CHARS:
        raise ValueError("Code is too long.")
    tree = ast.parse(code)
    SafetyVisitor().visit(tree)


def run_python_code(code: str, dataset_path: Path, output_dir: Path) -> str:
    validate_code(code)
    output_dir.mkdir(parents=True, exist_ok=True)

    wrapper = f"""
import json
import math
import statistics
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATASET_PATH = {str(dataset_path)!r}
OUTPUT_DIR = {str(output_dir)!r}
if DATASET_PATH.lower().endswith((".xlsx", ".xls")):
    data = pd.read_excel(DATASET_PATH)
else:
    data = pd.read_csv(DATASET_PATH)
df = data

{code}
"""

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".py", delete=False) as file:
        file.write(wrapper)
        script_path = file.name

    try:
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
            "MPLCONFIGDIR": str(output_dir / ".matplotlib"),
        }
        completed = subprocess.run(
            [sys.executable, script_path],
            cwd=output_dir,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    finally:
        Path(script_path).unlink(missing_ok=True)

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    if completed.returncode != 0:
        return f"Tool failed with exit code {completed.returncode}.\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    if stderr:
        return f"STDOUT:\n{stdout}\nSTDERR:\n{stderr}"
    return stdout or "Tool executed successfully without printed output."
