import os
import sys
import ast
import json
from pathlib import Path


class AnalizadorComplejidad(ast.NodeVisitor):
    def __init__(self):
        self.complejidad = 1

    def visit_If(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complejidad += len(node.values) - 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_match_case(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complejidad += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complejidad += 1
        self.generic_visit(node)


def calcular(codigo_fuente: str) -> int:
    try:
        arbol = ast.parse(codigo_fuente)
    except SyntaxError:
        return 0

    visitor = AnalizadorComplejidad()
    visitor.visit(arbol)
    return visitor.complejidad


DIRECTORIOS_IGNORADOS = {'venv', 'env', '.venv', 'migrations', '__pycache__', '.git', 'tests'}
ARCHIVOS_IGNORADOS = {'manage.py', 'settings.py', 'wsgi.py', 'asgi.py'}


def es_archivo_valido(ruta):
    nombre = os.path.basename(ruta)

    if not nombre.endswith('.py'):
        return False

    if nombre in ARCHIVOS_IGNORADOS:
        return False

    for parte in ruta.split(os.sep):
        if parte in DIRECTORIOS_IGNORADOS:
            return False

    return True


def obtener_archivos_python(directorio):
    archivos = []

    for root, dirs, files in os.walk(directorio):
        for file in files:
            ruta = os.path.join(root, file)
            if es_archivo_valido(ruta):
                archivos.append(ruta)

    return archivos


def analizar_directorio(directorio, limite_complejidad=15):
    archivos = obtener_archivos_python(directorio)

    resultados = []
    total = 0
    fallidos = 0

    for ruta in archivos:
        try:
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()

            complejidad = calcular(contenido)
            total += 1

            if complejidad > limite_complejidad:
                status = "DANGER"
                fallidos += 1
            elif complejidad >= limite_complejidad - 5:
                status = "WARN"
            else:
                status = "OK"

            resultados.append({
                "file": ruta,
                "complexity": complejidad,
                "status_code": status
            })

        except Exception:
            continue

    salida = {
        "analysis_type": "Cyclomatic Complexity (Directory Scan)",
        "threshold": limite_complejidad,
        "summary": {
            "total_files": total,
            "failed_files": fallidos
        },
        "results": resultados
    }

    print(json.dumps(salida, indent=4))

    directory_path = ".github/scripts/reports"

    Path(directory_path).mkdir(parents=True, exist_ok=True)

    # ✅ guardar en fichero
    with open(f"{directory_path}/cyclomatic_complexity_report.json", "w", encoding="utf-8") as file:
        file.write(json.dumps(salida, indent=2, ensure_ascii=False))


    sys.exit(0)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "analysis_type": "Cyclomatic Complexity",
            "summary": {"total_files": 0, "failed_files": 0},
            "results": []
        }, indent=4))
        sys.exit(0)

    analizar_directorio(sys.argv[1])