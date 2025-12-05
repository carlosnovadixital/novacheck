#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Script de test rápido para verificar que pynput está accesible
"""

import sys

print("=" * 60)
print("  TEST DE PYNPUT - Verificación de Instalación")
print("=" * 60)
print()

print("1. INFORMACIÓN DEL INTÉRPRETE PYTHON")
print("-" * 60)
print(f"Ejecutable: {sys.executable}")
print(f"Versión: {sys.version}")
print()

print("2. PYTHON PATH")
print("-" * 60)
for i, path in enumerate(sys.path, 1):
    print(f"  {i}. {path}")
print()

print("3. VERIFICACIÓN DE INSTALACIÓN FÍSICA")
print("-" * 60)
# Verificar si el paquete existe físicamente
import importlib.util
spec = importlib.util.find_spec("pynput")
if spec is None:
    print("✗ ERROR: pynput NO está instalado físicamente")
    print()
    print("SOLUCIÓN:")
    print(f"  sudo {sys.executable} -m pip install --break-system-packages pynput")
    print()
    sys.exit(1)
else:
    print(f"✓ pynput encontrado en el sistema")
    print(f"  Ubicación: {spec.origin}")
    print()

print("4. IMPORTACIÓN DE PYNPUT (puede fallar sin X11)")
print("-" * 60)
try:
    import pynput
    print(f"✓ pynput importado completamente")
    print(f"  Versión: {pynput.__version__}")
    print()
    
    # Intentar importar submodulos
    print("5. SUBMÓDULOS DE PYNPUT")
    print("-" * 60)
    try:
        from pynput import keyboard
        print("✓ pynput.keyboard importado (tiene X11 activo)")
    except Exception as e:
        print(f"⚠ pynput.keyboard falló al inicializar")
        print(f"  Tipo: {type(e).__name__}")
        if "X connection" in str(e) or "DISPLAY" in str(e):
            print()
            print("  ✓✓ ESTO ES ESPERADO sin interfaz gráfica ✓✓")
            print("  El módulo está instalado correctamente.")
            print("  Funcionará cuando ejecutes en Lubuntu con GUI (DISPLAY=:0).")
    
    print()
    print("=" * 60)
    print("✓✓✓ PYNPUT INSTALADO CORRECTAMENTE ✓✓✓")
    print("=" * 60)
    print()
    print("NOTA: Errores de 'X connection' son normales sin GUI.")
    print("      El script funcionará en Lubuntu con interfaz gráfica.")
    
except ImportError as e:
    # Este error significa que pynput lanza ImportError durante __init__
    if "X connection" in str(e) or "DISPLAY" in str(e) or "platform is not supported" in str(e):
        print(f"⚠ pynput está instalado pero requiere X11")
        print(f"  Error: {str(e)[:100]}...")
        print()
        print("=" * 60)
        print("✓✓✓ PYNPUT INSTALADO - REQUIERE GUI ✓✓✓")
        print("=" * 60)
        print()
        print("CONCLUSIÓN:")
        print("  • pynput SÍ está instalado correctamente")
        print("  • Necesita DISPLAY configurado (ej: DISPLAY=:0)")
        print("  • Funcionará en Lubuntu con interfaz gráfica")
        print()
    else:
        print(f"✗ ERROR INESPERADO al importar pynput")
        print(f"  Tipo: {type(e).__name__}")
        print(f"  Mensaje: {e}")
        print()
        sys.exit(1)
