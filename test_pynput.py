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

print("3. IMPORTACIÓN DE PYNPUT")
print("-" * 60)
try:
    import pynput
    print(f"✓ pynput encontrado correctamente")
    print(f"  Ubicación: {pynput.__file__}")
    print(f"  Versión: {pynput.__version__}")
    print()
    
    # Intentar importar submodulos
    print("4. SUBMÓDULOS DE PYNPUT")
    print("-" * 60)
    try:
        from pynput import keyboard
        print("✓ pynput.keyboard importado")
    except Exception as e:
        print(f"⚠ pynput.keyboard: {type(e).__name__}")
        print(f"  Mensaje: {str(e)[:100]}")
        if "X connection" in str(e) or "DISPLAY" in str(e):
            print()
            print("  NOTA: Este error es NORMAL sin interfaz gráfica.")
            print("  El módulo está instalado correctamente.")
            print("  Funcionará cuando ejecutes en Lubuntu con GUI.")
    
    print()
    try:
        from pynput import mouse
        print("✓ pynput.mouse importado")
    except Exception as e:
        print(f"⚠ pynput.mouse: {type(e).__name__}")
    
    print()
    print("=" * 60)
    print("✓✓✓ PYNPUT INSTALADO CORRECTAMENTE ✓✓✓")
    print("=" * 60)
    
except ImportError as e:
    print(f"✗ ERROR: pynput NO encontrado")
    print(f"  Tipo: {type(e).__name__}")
    print(f"  Mensaje: {e}")
    print()
    print("SOLUCIÓN:")
    print(f"  sudo {sys.executable} -m pip install --break-system-packages pynput")
    print()
    sys.exit(1)
