from pathlib import Path
import ast

IMPORT_LINE = "from config.base_model import MANAGED"

archivos = list(Path("apps").rglob("models.py"))

for archivo in archivos:
    contenido = archivo.read_text(encoding="utf-8")
    lineas = contenido.splitlines()

    # Eliminar cualquier importación MANAGED colocada incorrectamente.
    lineas = [
        linea for linea in lineas
        if linea.strip() != IMPORT_LINE
    ]

    contenido_limpio = "\n".join(lineas) + "\n"

    try:
        arbol = ast.parse(contenido_limpio)
    except SyntaxError as error:
        print(f"ERROR previo en {archivo}: {error}")
        continue

    imports = [
        nodo for nodo in arbol.body
        if isinstance(nodo, (ast.Import, ast.ImportFrom))
    ]

    if not imports:
        print(f"ADVERTENCIA: no se encontraron imports en {archivo}")
        continue

    # end_lineno usa numeración desde 1.
    ultima_linea_import = max(nodo.end_lineno for nodo in imports)

    lineas = contenido_limpio.splitlines()
    lineas.insert(ultima_linea_import, IMPORT_LINE)

    contenido_corregido = "\n".join(lineas) + "\n"

    try:
        ast.parse(contenido_corregido)
    except SyntaxError as error:
        print(f"ERROR después de corregir {archivo}: {error}")
        continue

    archivo.write_text(contenido_corregido, encoding="utf-8")
    print(f"OK: {archivo}")

print("Corrección terminada.")
