#gh issue list --state all --limit 1000 --json createdAt > .\scripts\issues.json
import json
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt


def main():
    # 1. Obtener la ruta exacta de la carpeta donde está este script (scripts/)
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # 2. Construir las rutas absolutas para los archivos
    json_path = os.path.join(SCRIPT_DIR, 'issues.json')
    img_path = os.path.join(SCRIPT_DIR, 'issue_runchart.png')

    try:
        # Intento 1: UTF-8 (El estándar que usará GitHub Actions)
        with open(json_path, 'r', encoding='utf-8') as f:
            texto_crudo = f.read()
    except UnicodeDecodeError:
        # Intento 2: UTF-16 (El formato que usa PowerShell en Windows localmente)
        with open(json_path, 'r', encoding='utf-16') as f:
            texto_crudo = f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en la ruta: {json_path}")
        return

    # Comprobamos si el archivo está vacío
    if not texto_crudo.strip():
        print("ERROR: El archivo está completamente vacío.")
        return

    try:
        # Convertimos el texto a JSON
        issues = json.loads(texto_crudo)
    except json.decoder.JSONDecodeError as e:
        print("Error: El texto no es un JSON válido.")
        return

    # 4. Extraer fechas
    dates = []
    for issue in issues:
        dt_str = issue['createdAt'].replace('Z', '+00:00')
        dates.append(datetime.fromisoformat(dt_str))

    # 5. Calcular semanas
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

    # 6. Preparar datos para el gráfico
    x_labels = list(weekly_counts.keys())
    y_values = list(weekly_counts.values())

    # 7. Generar el gráfico
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

    # 8. Guardar la imagen usando la ruta segura
    plt.savefig(img_path)
    print(f"Gráfico generado exitosamente en: {img_path}")


if __name__ == "__main__":
    main()