import re
import sys
import json
import os

KEYWORDS = {
    'if', 'else', 'for', 'while', 'return', 'class',
    'def', 'import', 'from', 'as', 'with', 'try', 'except',
    'break', 'continue', 'pass', 'finally', 'raise', 'in',
    'and', 'or', 'not', 'is', 'lambda', 'yield'
}

IDENTIFIER = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
THRESHOLD = 5


def extract_identifiers(code):
    return re.findall(IDENTIFIER, code)


def filter_identifiers(ids):
    return [i for i in ids if i not in KEYWORDS]


def average_length(ids):
    if not ids:
        return 0
    return sum(len(i) for i in ids) / len(ids)


def analyze_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            code = f.read()

        identifiers = filter_identifiers(extract_identifiers(code))
        avg = average_length(identifiers)

        return {
            "file": path,
            "avg_length": round(avg, 2),
            "status_code": "OK!" if avg >= THRESHOLD else "⚠️ IMPROVE NAMING"
        }
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None


def main(inputs):
    results = []
    all_files = []

    # Lógica para expandir carpetas o aceptar archivos individuales
    for item in inputs:
        if os.path.isdir(item):
            for root, _, files in os.walk(item):
                for file in files:
                    if file.endswith(".py"):
                        all_files.append(os.path.join(root, file))
        elif os.path.isfile(item):
            all_files.append(item)

    if not all_files:
        print("No valid files found to analyze.")
        return

    for path in all_files:
        print(f"Analyzing {path}")
        res = analyze_file(path)
        if res:
            results.append(res)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_dir = os.path.join(script_dir, "reports")

    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    report_path = os.path.join(report_dir, "identifier_report.json")

    report = {
        "analysis_type": "Identifier Length",
        "threshold": THRESHOLD,
        "summary": {
            "total_files": len(results),
            "failed_files": sum(1 for r in results if r["status_code"] != "OK!")
        },
        "results": results
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)

    print(f"\n✅ JSON report generated in: {report_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 len_identifier_metric.py <file_or_folder1> ...")
        sys.exit(1)

    main(sys.argv[1:])