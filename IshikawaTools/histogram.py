import calendar
from decouple import config
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

import os
# Configuration
REPO   = "Admin-Group-StreamSync/StreamSync"
TOKEN  = config("HISTOGRAM_TOKEN")
OWNER, REPO_NAME = REPO.split("/")

headers = {
    "X-GitHub-Api-Version": "2022-11-28",
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

#  Paginated fetch
def fetch_all_issues(owner: str, repo: str) -> list[dict]:
    issues, page = [], 1
    while True:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            params={"state": "all", "per_page": 100, "page": page},
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        issues.extend(i for i in batch if "pull_request" not in i)
        page += 1
    return issues

#  Date parsing
def parse_dates(issues: list[dict]) -> list[tuple[datetime, datetime | None]]:
    result = []
    for issue in issues:
        created = datetime.strptime(issue["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        closed  = (
            datetime.strptime(issue["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
            if issue.get("closed_at")
            else None
        )
        result.append((created, closed))
    return result

#  Month weeks with real range (Mon–Sun)
def build_weeks(year: int, month: int) -> list[tuple[str, datetime, datetime]]:
    cal   = calendar.monthcalendar(year, month)
    weeks = []
    for i, week in enumerate(cal):
        days = [d for d in week if d != 0]
        if not days:
            continue
        start = datetime(year, month, days[0])
        end   = datetime(year, month, days[-1], 23, 59, 59)
        weeks.append((f"Wk {i + 1}\n({days[0]}-{days[-1]})", start, end))
    return weeks

#  Open issues count per week
def count_open_per_week(
    issue_dates: list[tuple[datetime, datetime | None]],
    weeks: list[tuple[str, datetime, datetime]],
) -> list[int]:
    counts = []
    for _label, start, end in weeks:
        open_count = sum(
            1
            for created, closed in issue_dates

            if start <= created <= end and (closed is None)
        )
        counts.append(open_count)
    return counts


def main():

    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(script_dir, 'issues_per_week.png')
    print("Fetching GitHub issues...")
    issues      = fetch_all_issues(OWNER, REPO_NAME)
    issue_dates = parse_dates(issues)
    print(f"  -> {len(issues)} issues found (excluding PRs)")

    weeks = []
    weeks.extend(build_weeks(2026, 3))
    weeks.extend(build_weeks(2026, 4))
    sprint_end_date = datetime(2026, 4, 24)

    weeks = [
        (label, start, end)
        for (label, start, end) in weeks
        if start <= sprint_end_date
    ]

    counts = count_open_per_week(issue_dates, weeks)

    labels = [
        f"{datetime(start.year, start.month, 1).strftime('%b')} {label}"
        for label, start, end in weeks
    ]

    # Chart
    fig, ax = plt.subplots(figsize=(14, 6))
    bars = ax.bar(labels, counts, color="#4C72B0", edgecolor="white", linewidth=0.8)

    for bar, count in zip(bars, counts):
        if count > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                str(count),
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Weeks of the month", fontsize=12)
    ax.set_ylabel("Number of open issues", fontsize=12)
    ax.set_title(
        "Open issues per week currently active",
        fontsize=14,
        fontweight="bold",
    )
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig(img_path)
    print(f"Chart generated successfully at: {img_path}")

if __name__ == "__main__":
    main()
