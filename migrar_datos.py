"""
Script para migrar datos de MySQL a PostgreSQL (Heroku)
Ejecutar después de hacer las migraciones en Heroku

Uso:
1. Asegúrate de tener acceso a ambas bases de datos
2. Configura las credenciales en este script
3. Ejecuta: python migrar_datos.py
"""

import os
import django
import MySQLdb
import psycopg2

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from django.db import connections

def exportar_datos_mysql():
    """Exporta datos de MySQL a archivos JSON"""
    print("📦 Exportando datos de MySQL...")

    # Lista de apps a exportar (excluir tablas de sistema)
    apps_to_export = [
        'accounts',
        'core',
        'mantenimiento',
        'inventario',
        'produccion',
        'documentos',
        'reportes',
    ]

    for app in apps_to_export:
        try:
            print(f"  Exportando {app}...")
            call_command(
                'dumpdata',
                app,
                '--natural-foreign',
                '--natural-primary',
                '--indent', '2',
                '--output', f'{app}_data.json'
            )
            print(f"  ✓ {app} exportado correctamente")
        except Exception as e:
            print(f"  ⚠️ Error exportando {app}: {e}")

    print("\n✅ Exportación completada")
    print("Archivos generados: *_data.json")

def importar_datos_postgresql():
    """Importa datos JSON a PostgreSQL"""
    print("\n📥 Importando datos a PostgreSQL...")

    apps_to_import = [
        'accounts',
        'core',
        'mantenimiento',
        'inventario',
        'produccion',
        'documentos',
        'reportes',
    ]

    for app in apps_to_import:
        filename = f'{app}_data.json'
        if os.path.exists(filename):
            try:
                print(f"  Importando {app}...")
                call_command('loaddata', filename)
                print(f"  ✓ {app} importado correctamente")
            except Exception as e:
                print(f"  ⚠️ Error importando {app}: {e}")
        else:
            print(f"  ⚠️ Archivo {filename} no encontrado")

    print("\n✅ Importación completada")

def verificar_migracion():
    """Verifica que los datos se migraron correctamente"""
    from apps.accounts.models import Usuario
    from apps.core.models import Maquina, Area
    from apps.mantenimiento.models import OrdenTrabajo
    from apps.inventario.models import Repuesto

    print("\n🔍 Verificando migración...")
    print(f"  Usuarios: {Usuario.objects.count()}")
    print(f"  Áreas: {Area.objects.count()}")
    print(f"  Máquinas: {Maquina.objects.count()}")
    print(f"  Órdenes de Trabajo: {OrdenTrabajo.objects.count()}")
    print(f"  Repuestos: {Repuesto.objects.count()}")
    print("\n✅ Verificación completada")

if __name__ == '__main__':
    import sys

    print("=" * 60)
    print("MIGRACIÓN DE DATOS: MySQL → PostgreSQL")
    print("=" * 60)
    print()
    print("IMPORTANTE:")
    print("1. Asegúrate de haber ejecutado las migraciones en PostgreSQL")
    print("2. Este script debe ejecutarse con acceso a MySQL local")
    print("3. Los archivos JSON se generarán en el directorio actual")
    print()

    opcion = input("¿Qué deseas hacer?\n1. Exportar desde MySQL\n2. Importar a PostgreSQL\n3. Verificar migración\n4. Todo (Exportar + Importar)\nOpción: ")

    if opcion == '1':
        exportar_datos_mysql()
    elif opcion == '2':
        importar_datos_postgresql()
    elif opcion == '3':
        verificar_migracion()
    elif opcion == '4':
        exportar_datos_mysql()
        importar_datos_postgresql()
        verificar_migracion()
    else:
        print("Opción inválida")
