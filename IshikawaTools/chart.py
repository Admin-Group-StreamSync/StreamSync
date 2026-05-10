import pandas as pd
import json
import matplotlib.pyplot as plt
import os


def generate_diagram():
    file_path = 'issues_data.json'

    # 1. Validate file existence and size
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        return

    if os.path.getsize(file_path) == 0:
        print(f"Error: File {file_path} is empty.")
        return


    try:

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # If UTF-8 fails, try UTF-16
        try:
            with open(file_path, 'r', encoding='utf-16') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Encoding error: Could not read file. Details: {e}")
            return
    except json.JSONDecodeError as e:
        print(f"Error: File content is not valid JSON. {e}")
        return

    if not data or not isinstance(data, list):
        print("No valid data found or the list is empty.")
        return

    all_labels = []
    for issue in data:
        labels = issue.get('labels', [])
        if labels:
            for label in labels:
                # Supports both dict labels {'name': 'bug'} and raw strings
                name = label['name'] if isinstance(label, dict) else label
                all_labels.append(name)
        else:
            all_labels.append('No Label')

    if not all_labels:
        print("No labels to process.")
        return

    # 4. Build DataFrame and Pareto metrics
    df = pd.Series(all_labels).value_counts().to_frame(name='frequency')
    df.index.name = 'label'
    df['percentage'] = (df['frequency'] / df['frequency'].sum()) * 100
    df['cumulative'] = df['percentage'].cumsum()

    # 5. Generate chart
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Bars
    ax1.bar(df.index, df['frequency'], color="steelblue", label="Frequency")
    ax1.set_ylabel("Issue Count", fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    # Cumulative line
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['cumulative'], color="red", marker="D", ms=5, label="% Cumulative")
    ax2.axhline(80, color="orange", linestyle="--", alpha=0.6)
    ax2.set_ylabel("Cumulative Percentage (%)", fontweight='bold')
    ax2.set_ylim(0, 110)

    plt.title("Pareto Chart: Issue Analysis", fontsize=14, fontweight='bold')
    plt.tight_layout()

    plt.savefig('pareto_report.png')
    print("Chart generated: pareto_report.png")


if __name__ == "__main__":
    generate_diagram()
