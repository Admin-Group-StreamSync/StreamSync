import calendar
import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from decouple import Config, RepositoryEnv
from matplotlib.ticker import MaxNLocator

# ── Configuración de Rutas y Variables ─────────────────────────────────────────
# Esto asegura que busque el archivo .env en la misma carpeta que este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, '.env')

# Si existe el archivo .env en la carpeta, lo cargamos específicamente
if os.path.exists(env_path):
    config = Config(RepositoryEnv(env_path))
else:
    # Si no existe, usamos la configuración por defecto (variables de entorno del sistema)
    from decouple import config

# ── Configuración del Repositorio ──────────────────────────────────────────────
REPO = "Admin-Group-StreamSync/StreamSync"
TOKEN = config("HISTOGRAM_TOKEN")
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
        # Filtramos para excluir Pull Requests (GitHub trata PRs como issues en su API)
        issues.extend(i for i in batch if "pull_request" not in i)
        page += 1
    return issues


# ── Parseo de fechas ───────────────────────────────────────────────────────────
def parse_dates(issues: list[dict]):
    dates = []
    for i in issues:
        created_at = datetime.strptime(i["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        closed_at = None
        if i["closed_at"]:
            closed_at = datetime.strptime(i["closed_at"], "%Y-%m-%dT%H:%M:%SZ")
        dates.append((created_at, closed_at))
    return dates


# ── Lógica de Semanas ──────────────────────────────────────────────────────────
def build_weeks(year, month):
    cal = calendar.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)
    weeks = []
    for week in month_days:
        week_days = [d for d in week if d != 0]
        if week_days:
            start_date = datetime(year, month, min(week_days))
            end_date = datetime(year, month, max(week_days), 23, 59, 59)
            label = f"{min(week_days)}-{max(week_days)} {calendar.month_name[month][:3]}"
            weeks.append((label, start_date, end_date))
    return weeks


def count_open_per_week(issue_dates, weeks):
    counts = []
    for _, start, end in weeks:
        open_count = 0
        for created, closed in issue_dates:
            # Una issue estaba abierta si se creó antes del fin de semana
            # y no se había cerrado antes del inicio de la semana.
            if created <= end and (closed is None or closed >= start):
                open_count += 1
        counts.append(open_count)
    return counts


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    print("Obteniendo issues de GitHub...")
    try:
        issues = fetch_all_issues(OWNER, REPO_NAME)
    except requests.exceptions.HTTPError as e:
        print(f"Error de conexión: {e}")
        return

    issue_dates = parse_dates(issues)
    print(f"  → {len(issues)} issues encontradas (sin PRs)")

    now = datetime.now()
    weeks = build_weeks(now.year, now.month)
    counts = count_open_per_week(issue_dates, weeks)
    labels = [w[0] for w in weeks]

    # ── Gráfica ────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 6))
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
    ax.set_title(f"Evolución de Issues Abiertas - {calendar.month_name[now.month]} {now.year}", fontsize=14)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
