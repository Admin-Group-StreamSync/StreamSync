#gh issue list --state all --limit 1000 --json createdAt > .\scripts\issues.json
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def main():
    # 1. Get the exact path of the folder where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 2. Build absolute file paths
    json_path = os.path.join(script_dir, 'issues.json')
    img_path = os.path.join(script_dir, 'issue_runchart.png')

    try:
        # Attempt 1: UTF-8 (the standard used by GitHub Actions)
        with open(json_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except UnicodeDecodeError:
        # Attempt 2: UTF-16 (format commonly used by local Windows PowerShell)
        with open(json_path, 'r', encoding='utf-16') as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"Error: File not found at path: {json_path}")
        return

    # Check if the file is empty
    if not raw_text.strip():
        print("ERROR: The file is completely empty.")
        return

    try:
        # Convert text to JSON
        issues = json.loads(raw_text)
    except json.decoder.JSONDecodeError as e:
        print("Error: The file content is not valid JSON.")
        return

    # 4. Extract dates
    dates = []
    for issue in issues:
        dt_str = issue['createdAt'].replace('Z', '+00:00')
        dates.append(datetime.fromisoformat(dt_str))

    # 5. Compute week buckets
    min_date = min(dates)
    max_date = max(dates)
    start_week = min_date - timedelta(days=min_date.weekday())
    start_week = start_week.replace(hour=0, minute=0, second=0, microsecond=0)

    weekly_counts = {}
    current_week = start_week
    while current_week <= max_date + timedelta(days=7):
        week_label = current_week.strftime('%Y-W%W')
        weekly_counts[week_label] = 0
        current_week += timedelta(days=7)

    for dt in dates:
        week_label = dt.strftime('%Y-W%W')
        if week_label in weekly_counts:
            weekly_counts[week_label] += 1

    # 6. Prepare chart data
    x_labels = list(weekly_counts.keys())
    y_values = list(weekly_counts.values())

    # 7. Generate the chart
    plt.figure(figsize=(12, 6))
    plt.plot(x_labels, y_values, marker='o', linestyle='-', color='#8957e5', linewidth=2)

    plt.title('Issues Created Per Week', fontsize=16, fontweight='bold')
    plt.xlabel('Week (Year-Week Number)', fontsize=12)
    plt.ylabel('Number of New Issues', fontsize=12)

    plt.xticks(rotation=45, ha='right')

    max_issues = max(y_values) if y_values else 0
    plt.yticks(range(0, max_issues + 2))

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()

    # 8. Save image using safe absolute path
    plt.savefig(img_path)
    print(f"Chart generated successfully at: {img_path}")


if __name__ == "__main__":
    main()
