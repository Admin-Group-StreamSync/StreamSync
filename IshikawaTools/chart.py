import pandas as pd
import json
import matplotlib.pyplot as plt

def generate_diagram():
    with open('issues_data.json', 'r') as f:
        data = json.load(f)

    all_labels = []
    for issue in data:
        if issue['labels']:
            for label in issue['labels']:
                all_labels.append(label['name'])
        else:
            all_labels.append('Unlabeled')

    df = pd.Series(all_labels).value_counts().to_frame(name='frecuencia')
    df.index.name = 'etiqueta'

    df['porcentaje'] = (df['frecuencia'] / df['frecuencia'].sum()) * 100
    df['acumulado'] = df['porcentaje'].cumsum()

    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.bar(df.index, df['frecuencia'], color="steelblue", label="Frecuencia")
    ax1.set_ylabel("Cantidad de Issues", fontweight='bold')
    ax1.set_xlabel("Etiquetas", fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    ax2 = ax1.twinx()
    ax2.plot(df.index, df['acumulado'], color="red", marker="D", ms=5, label="% Acumulado")
    ax2.axhline(80, color="orange", linestyle="--", alpha=0.5) # Línea del 80%
    ax2.set_ylabel("Porcentaje Acumulado (%)", fontweight='bold')
    ax2.set_ylim(0, 110)

    plt.title("Diagrama de Pareto: Análisis de Etiquetas en Issues", fontsize=14)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('pareto_report.png')
    print("Gráfico generado exitosamente.")

if __name__ == "__main__":
    generate_diagram()
