import re
import sys
import json

KEYWORDS = {
    'if', 'else', 'for', 'while', 'return', 'class',
    'def', 'import', 'from', 'as', 'with', 'try', 'except',
    'break', 'continue', 'pass', 'finally', 'raise', 'in',
    'and', 'or', 'not', 'is', 'lambda', 'yield'
}

IDENTIFIER = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
THRESHOLD = 10

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
        "file": path,
        "avg_length": round(avg, 2),
        "status_code": "OK!" if avg >= THRESHOLD else "⚠️ IMPROVE NAMING"
    }

def main(paths):
    results = []

    for path in paths:
        print(f"Analyzing {path}")
        results.append(analyze_file(path))

    # Create JSON
    report = {
        "analysis_type": "Identifier Length",
        "threshold": THRESHOLD,
        "summary": {
            "total_files": len(results),
            "failed_files": sum(1 for r in results if r["status_code"] != "OK!")
        },
        "results": results
    }

    with open("identifier_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print("JSON report generated: identifier_report.json")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python identifier_length.py <file1> <file2> ...")
        sys.exit(1)

    main(sys.argv[1:])
