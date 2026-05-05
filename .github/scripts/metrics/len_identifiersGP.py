import re
import sys
import json
from pathlib import Path

# Python reserved words
PY_KEYWORDS = {
    'if', 'else', 'for', 'while', 'return', 'class',
    'def', 'import', 'from', 'as', 'with', 'try', 'except',
    'break', 'continue', 'pass', 'finally', 'raise', 'in',
    'and', 'or', 'not', 'is', 'lambda', 'yield'
}

# JavaScript / TypeScript reserved words
JS_KEYWORDS = {
    'if', 'else', 'for', 'while', 'do', 'return', 'class', 'function',
    'import', 'export', 'from', 'as', 'with', 'try', 'catch', 'finally',
    'throw', 'break', 'continue', 'new', 'delete', 'typeof', 'instanceof',
    'in', 'of', 'let', 'const', 'var', 'this', 'super', 'null', 'undefined',
    'true', 'false', 'void', 'switch', 'case', 'default', 'debugger',
    'interface', 'type', 'enum', 'namespace', 'declare', 'abstract',
    'implements', 'extends', 'readonly', 'public', 'private', 'protected',
    'static', 'async', 'await', 'yield', 'get', 'set', 'keyof', 'typeof',
    'never', 'unknown', 'any', 'string', 'number', 'boolean', 'object',
    'symbol', 'bigint',
}

KEYWORDS = PY_KEYWORDS | JS_KEYWORDS

JS_EXTENSIONS = {'.js', '.ts', '.mjs', '.tsx', '.jsx', '.cjs'}
ACCEPTED_EXTENSIONS = {'.py'} | JS_EXTENSIONS

IDENTIFIER = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
THRESHOLD = 6

# 🔽 NUEVO: directorios ignorados
IGNORED_DIRS = {'venv', '.venv', 'env', '__pycache__', '.git', 'node_modules', 'dist', 'build'}

def extract_identifiers(code):
    return re.findall(IDENTIFIER, code)

def filter_identifiers(ids):
    return [i for i in ids if i not in KEYWORDS]

def average_length(ids):
    if not ids:
        return 0
    return sum(len(i) for i in ids) / len(ids)

def analyze_file(path):
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    identifiers = filter_identifiers(extract_identifiers(code))
    avg = average_length(identifiers)

    return {
        "file": str(path),
        "avg_length": round(avg, 2),
        "status_code": "OK!" if avg >= THRESHOLD else "⚠️ IMPROVE NAMING"
    }

# 🔽 SOLO CAMBIO AQUÍ
def collect_files(paths):
    files = []

    for path in paths:
        p = Path(path)

        if p.is_file() and p.suffix in ACCEPTED_EXTENSIONS:
            files.append(p)

        elif p.is_dir():
            for f in p.rglob("*"):
                if f.suffix in ACCEPTED_EXTENSIONS:
                    # ignorar directorios no deseados
                    if any(part in IGNORED_DIRS for part in f.parts):
                        continue
                    files.append(f)

    return files


def main(paths):
    results = []

    files = collect_files(paths)

    for file in files:
        print(f"Analyzing {file}")
        results.append(analyze_file(file))

    report = {
        "analysis_type": "Identifier Length",
        "threshold": THRESHOLD,
        "summary": {
            "total_files": len(results),
            "failed_files": sum(1 for r in results if r["status_code"] != "OK!")
        },
        "results": results
    }

    directory_path = ".github/scripts/reports"

    Path(directory_path).mkdir(parents=True, exist_ok=True)

    # ✅ guardar en fichero
    with open(f"{directory_path}/fog_index_report.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(report, indent=2, ensure_ascii=False))

    print("JSON report generated: identifier_report.json")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identifier_length.py <file_or_directory> ...")
        sys.exit(1)

    main(sys.argv[1:])