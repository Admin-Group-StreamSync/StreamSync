import pandas as pd
import json
import matplotlib.pyplot as plt
import os


def generate_diagram():
    file_path = 'issues_data.json'

    # 1. Verificación de existencia y tamaño
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe.")
        return

    if os.path.getsize(file_path) == 0:
        print(f"Error: El archivo {file_path} está vacío.")
        return

    # 2. Carga de datos con manejo de codificación (UTF-8 con soporte para BOM)
    try:
        # Usamos 'utf-8-sig' para que ignore el marcador 0xff si existe
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except UnicodeDecodeError:
        # Si falla el utf-8, intentamos con utf-16 (común en Windows/PowerShell)
        try:
            with open(file_path, 'r', encoding='utf-16') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error de codificación: No se pudo leer el archivo. Detalles: {e}")
            return
    except json.JSONDecodeError as e:
        print(f"Error: El archivo no tiene un formato JSON válido. {e}")
        return

    if not data or not isinstance(data, list):
        print("No se encontraron datos válidos o la lista está vacía.")
        return

    # 3. Procesamiento de etiquetas (Labels)
    all_labels = []
    for issue in data:
        labels = issue.get('labels', [])
        if labels:
            for label in labels:
                # Soporta tanto diccionarios {'name': 'bug'} como strings directos
                name = label['name'] if isinstance(label, dict) else label
                all_labels.append(name)
        else:
            all_labels.append('Sin Etiqueta')

    if not all_labels:
        print("No hay etiquetas para procesar.")
        return

    # 4. Creación del DataFrame y Pareto
    df = pd.Series(all_labels).value_counts().to_frame(name='frecuencia')
    df.index.name = 'etiqueta'
    df['porcentaje'] = (df['frecuencia'] / df['frecuencia'].sum()) * 100
    df['acumulado'] = df['porcentaje'].cumsum()

    # 5. Generación del Gráfico
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Barras
    ax1.bar(df.index, df['frecuencia'], color="steelblue", label="Frecuencia")
    ax1.set_ylabel("Cantidad de Issues", fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    # Línea acumulada
    ax2 = ax1.twinx()
    ax2.plot(df.index, df['acumulado'], color="red", marker="D", ms=5, label="% Acumulado")
    ax2.axhline(80, color="orange", linestyle="--", alpha=0.6)
    ax2.set_ylabel("Porcentaje Acumulado (%)", fontweight='bold')
    ax2.set_ylim(0, 110)

    plt.title("Diagrama de Pareto: Análisis de Issues", fontsize=14, fontweight='bold')
    plt.tight_layout()

    # Guardar resultado
    plt.savefig('pareto_report.png')
    print("Gráfico generado: pareto_report.png")


if __name__ == "__main__":
    generate_diagram()