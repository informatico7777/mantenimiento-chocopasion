"""
Script para cambiar managed = False a managed = MANAGED
en todos los modelos para permitir migraciones en Heroku
"""
import os
import re

def actualizar_modelos():
    """Actualiza todos los modelos para usar managed dinamico"""

    apps_dir = 'apps'
    archivos_modificados = []

    # Buscar todos los models.py
    for root, dirs, files in os.walk(apps_dir):
        # Saltar __pycache__ y migrations
        if '__pycache__' in root or 'migrations' in root:
            continue

        for file in files:
            if file == 'models.py':
                filepath = os.path.join(root, file)

                # Leer archivo
                with open(filepath, 'r', encoding='utf-8') as f:
                    contenido = f.read()

                # Verificar si tiene managed = False
                if 'managed = False' not in contenido:
                    continue

                contenido_original = contenido

                # Agregar import si no existe
                if 'from config.base_model import MANAGED' not in contenido:
                    # Buscar la ultima linea de imports
                    lines = contenido.split('\n')
                    import_index = 0

                    for i, line in enumerate(lines):
                        if line.strip().startswith('from ') or line.strip().startswith('import '):
                            import_index = i

                    # Insertar despues del ultimo import
                    lines.insert(import_index + 1, 'from config.base_model import MANAGED')
                    contenido = '\n'.join(lines)

                # Reemplazar managed = False por managed = MANAGED
                contenido = re.sub(
                    r'managed\s*=\s*False',
                    'managed = MANAGED',
                    contenido
                )

                # Solo escribir si hubo cambios
                if contenido != contenido_original:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(contenido)

                    archivos_modificados.append(filepath)
                    print(f"OK Actualizado: {filepath}")

    return archivos_modificados

if __name__ == '__main__':
    print("=" * 60)
    print("ACTUALIZANDO MODELOS PARA HEROKU")
    print("=" * 60)
    print()
    print("Cambiando managed = False -> managed = MANAGED")
    print("Esto permitira que Django cree las tablas en PostgreSQL")
    print()

    archivos = actualizar_modelos()

    print()
    print("=" * 60)
    print(f"OK {len(archivos)} archivos actualizados")
    print("=" * 60)
    print()

    if archivos:
        print("Archivos modificados:")
        for archivo in archivos:
            print(f"  - {archivo}")
        print()
        print("SIGUIENTE PASO:")
        print("  1. Revisa los cambios: git diff")
        print("  2. Haz commit: git add . && git commit -m 'Habilitar managed para Heroku'")
        print("  3. Push a Heroku: git push heroku main")
    else:
        print("No se encontraron archivos para actualizar")
