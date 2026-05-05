import ast
import sys
import json
from pathlib import Path
from typing import Dict, List, Set


class CallGraphVisitor(ast.NodeVisitor):
    def __init__(self):
        self.current_function = None
        self.calls: Dict[str, Set[str]] = {}   # fan-out
        self.called_by: Dict[str, Set[str]] = {}  # fan-in

    def visit_FunctionDef(self, node: ast.FunctionDef):
        func_name = node.name

        self.current_function = func_name
        self.calls.setdefault(func_name, set())
        self.called_by.setdefault(func_name, set())

        self.generic_visit(node)

        self.current_function = None

    def visit_Call(self, node: ast.Call):
        if self.current_function is None:
            return

        if isinstance(node.func, ast.Name):
            called = node.func.id

            # fan-out
            self.calls[self.current_function].add(called)

            # fan-in
            self.called_by.setdefault(called, set()).add(self.current_function)

        self.generic_visit(node)


def analyze_file(filepath: Path):
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
    except:
        return []

    visitor = CallGraphVisitor()
    visitor.visit(tree)

    results = []

    for func in visitor.calls:
        fan_out = len(visitor.calls.get(func, []))
        fan_in = len(visitor.called_by.get(func, []))

        results.append({
            "function": func,
            "fan_in": fan_in,
            "fan_out": fan_out
        })

    return results


def collect_python_files(paths: List[str]) -> List[Path]:
    files = []
    base = Path.cwd()

    IGNORED_DIRS = {"venv", ".venv", "env", "__pycache__", ".git"}

    for p in paths:
        path = Path(p)

        if str(path) in {".", "./"}:
            path = base

        if path.is_file() and path.suffix == ".py":
            # ignorar si está dentro de venv
            if not any(part in IGNORED_DIRS for part in path.parts):
                files.append(path)

        elif path.is_dir():
            for file in path.rglob("*.py"):
                # ignorar carpetas no deseadas
                if not any(part in IGNORED_DIRS for part in file.parts):
                    files.append(file)

    return files


def classify(fan_in, fan_out):
    if fan_in > 10:
        return "HIGH FAN-IN ⚠️"
    if fan_out > 10:
        return "HIGH FAN-OUT ⚠️"
    return "OK"


def main():
    if not sys.argv[1:]:
        print("Usage: python fan_in_out.py <path>")
        sys.exit(1)

    files = collect_python_files(sys.argv[1:])
    all_results = []

    for file in files:
        functions = analyze_file(file)

        for f in functions:
            all_results.append({
                "file": str(file),
                "function": f["function"],
                "fan_in": f["fan_in"],
                "fan_out": f["fan_out"],
                "status_code": classify(f["fan_in"], f["fan_out"])
            })

    report = {
        "analysis_type": "Fan-In / Fan-Out",
        "summary": {
            "total_functions": len(all_results),
            "high_risk": sum(1 for r in all_results if "⚠️" in r["status_code"])
        },
        "results": all_results
    }

    directory_path = ".github/scripts/reports"

    Path(directory_path).mkdir(parents=True, exist_ok=True)

    # ✅ guardar en fichero
    with open(f"{directory_path}/fog_index_report.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(report, indent=2, ensure_ascii=False))

    print("Report generated: fan_in_out_report.json")


if __name__ == "__main__":
    main()