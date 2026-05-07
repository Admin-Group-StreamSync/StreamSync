import ast
import sys
import json
from pathlib import Path
from typing import Dict, Optional, List, Any

#new metric
CRITICAL_THRESHOLD = 5
WARNING_THRESHOLD = 3


class NestingVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.depths: List[int] = []
        self.current_depth: int = 0

    def visit_If(self, node: ast.If) -> None:
        self.current_depth += 1
        self.depths.append(self.current_depth)

        for item in node.body:
            self.visit(item)

        if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
            self.current_depth -= 1
            self.visit(node.orelse[0])
            self.current_depth += 1
        else:
            for item in node.orelse:
                self.visit(item)

        self.current_depth -= 1


def get_status_code(max_depth: int) -> str:
    if max_depth > CRITICAL_THRESHOLD:
        return "❌ CRITICAL"
    if max_depth >= WARNING_THRESHOLD:
        return "🚨 WARNING"
    return "✅ OK"


def get_metrics(filepath: Path) -> Optional[Dict[str, Any]]:
    try:
        content = filepath.read_text(encoding="utf-8").strip()
        if not content:
            return None
        tree = ast.parse(content)
    except (SyntaxError, OSError) as e:
        print(f"Error processing {filepath}: {e}")
        return None

    visitor = NestingVisitor()
    visitor.visit(tree)

    if not visitor.depths:
        return {"avg": 0.0, "max": 0, "status_code": "✅ OK"}

    max_d = max(visitor.depths)
    avg_d = round(sum(visitor.depths) / len(visitor.depths), 1)

    return {
        "avg": avg_d,
        "max": max_d,
        "status_code": get_status_code(max_d)
    }


def collect_python_files(paths: List[str]) -> List[Path]:
    collected = []
    for raw in paths:
        p = Path(raw).resolve()
        if p.is_dir():
            collected.extend(p.rglob("*.py"))
        elif p.is_file() and p.suffix == ".py":
            collected.append(p)
    return collected


def main() -> None:
    if not sys.argv[1:]:
        print("No paths provided.")
        sys.exit(0)

    files_to_analyze = collect_python_files(sys.argv[1:])

    if not files_to_analyze:
        print("No Python files found.")
        sys.exit(0)

    all_results: List[Dict[str, Any]] = []
    failed_count = 0

    for filepath in files_to_analyze:
        metrics = get_metrics(filepath)
        if metrics:
            all_results.append({
                "file": str(filepath),
                "avg_depth": metrics["avg"],
                "max_depth": metrics["max"],
                "status_code": metrics["status_code"]
            })
            if metrics["max"] > CRITICAL_THRESHOLD:
                failed_count += 1

    json_data = {
        "analysis_type": "Depth of Conditional Nesting",
        "threshold": CRITICAL_THRESHOLD,
        "summary": {
            "total_files": len(all_results),
            "failed_files": failed_count
        },
        "results": all_results
    }

    output_file = Path(".github/scripts/reports/nesting_metrics.json")
    # output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(json_data, indent=4, ensure_ascii=False), encoding="utf-8")

    print(f"Analysis report saved to {output_file}")

    if failed_count > 0:
        print(f"FAIL: {failed_count} files exceed the nesting threshold.")
        sys.exit(1)
    else:
        print("SUCCESS: All files are within the nesting threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()