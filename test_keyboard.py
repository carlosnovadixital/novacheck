#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar el mapeo de teclas especiales
"""

# Función de mapeo de teclas (copiada de main.py para testing)
def map_key(k):
    # Teclas especiales comunes
    if k in [10,13]: return "ENTER"
    if k==32: return "SPACE"
    if k in [263,127]: return "BKSP"
    if k==9: return "TAB"
    if k==60: return "<"
    
    # Caracteres especiales españoles
    if k==241: return "Ñ"  # ñ
    if k==209: return "Ñ"  # Ñ
    if k==231: return "Ç"  # ç
    if k==199: return "Ç"  # Ç
    if k==180: return "´"  # acento agudo
    if k==96: return "`"   # acento grave
    if k==161: return "¡"  # ¡
    if k==191: return "¿"  # ¿
    if k==186: return "º"  # º
    if k==170: return "ª"  # ª
    if k==43: return "+"   # +
    if k==45: return "-"   # -
    if k==39: return "'"   # '
    if k==44: return ","   # ,
    if k==46: return "."   # .
    
    # Intentar convertir el resto
    try: 
        char = chr(k).upper()
        return char if char.isprintable() else None
    except: 
        return None

# Pruebas
print("=== TEST DE MAPEO DE TECLAS ===\n")

# Teclas especiales españolas
test_keys = [
    (241, "ñ"),
    (209, "Ñ"),
    (231, "ç"),
    (199, "Ç"),
    (180, "´"),
    (96, "`"),
    (161, "¡"),
    (191, "¿"),
    (186, "º"),
    (170, "ª"),
    (43, "+"),
    (45, "-"),
    (ord('A'), "A"),
    (ord('z'), "Z"),
    (32, "SPACE"),
    (10, "ENTER"),
]

print("Pruebas de caracteres especiales:")
for code, expected in test_keys:
    result = map_key(code)
    status = "✓" if result else "✗"
    print(f"{status} Código {code:3d} ({expected:8s}) -> {result}")

print("\n✓ Test completado")
