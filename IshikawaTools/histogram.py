import calendar
from decouple import config
import requests
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ── Configuración ──────────────────────────────────────────────────────────────
REPO   = "TralaleritosTralalas/SoftwareProject"
TOKEN  = config("HISTOGRAM_TOKEN")
OWNER, REPO_NAME = REPO.split("/")

headers = {
    "X-GitHub-Api-Version": "2022-11-28",
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
}

# ── Fetch con paginación ───────────────────────────────────────────────────────
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

# ── Parseo de fechas ───────────────────────────────────────────────────────────
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

# ── Semanas del mes con rango real (lun–dom) ───────────────────────────────────
def build_weeks(year: int, month: int) -> list[tuple[str, datetime, datetime]]:
    cal   = calendar.monthcalendar(year, month)
    weeks = []
    for i, week in enumerate(cal):
        days = [d for d in week if d != 0]
        if not days:
            continue
        start = datetime(year, month, days[0])
        end   = datetime(year, month, days[-1], 23, 59, 59)
        weeks.append((f"Sem {i + 1}\n({days[0]}-{days[-1]})", start, end))
    return weeks

# ── Conteo de issues abiertas en cada semana ───────────────────────────────────
def count_open_per_week(
    issue_dates: list[tuple[datetime, datetime | None]],
    weeks: list[tuple[str, datetime, datetime]],
) -> list[int]:
    counts = []
    for _label, start, end in weeks:
        open_count = sum(
            1
            for created, closed in issue_dates
            if created <= end and (closed is None or closed >= start)
        )
        counts.append(open_count)
    return counts

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Obteniendo issues de GitHub…")
    issues      = fetch_all_issues(OWNER, REPO_NAME)
    issue_dates = parse_dates(issues)
    print(f"  → {len(issues)} issues encontradas (sin PRs)")

    now    = datetime.now()
    weeks  = build_weeks(now.year, now.month)
    counts = count_open_per_week(issue_dates, weeks)
    labels = [w[0] for w in weeks]

    # ── Gráfica ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
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
    ax.set_xlabel("Semanas del mes", fontsize=12)
    ax.set_ylabel("Número de issues abiertas", fontsize=12)
    ax.set_title(
        f"Issues abiertas por semana — {now.strftime('%B %Y')}",
        fontsize=14,
        fontweight="bold",
    )
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.savefig("issues_histogram.png", dpi=150)
    plt.show()
    print("Gráfica guardada como issues_histogram.png")

if __name__ == "__main__":
    main()