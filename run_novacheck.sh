#!/bin/bash
# Script para ejecutar NovaCheck
# Las dependencias deben estar instaladas GLOBALMENTE
# (no se usa virtualenv porque el script corre como daemon)

SCRIPT_PATH="/app/main.py"

echo "========================================="
echo "  NOVACHECK - Iniciando"
echo "========================================="
echo ""

# Verificar si Python 3 está disponible
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 no encontrado"
    echo "  Instala con: sudo apt install python3"
    exit 1
fi

echo "✓ Python 3 encontrado"

# Verificar pynput (CRÍTICO para test de teclado)
if python3 -c "import pynput" 2>/dev/null; then
    echo "✓ pynput instalado correctamente"
else
    echo "✗ pynput no encontrado"
    echo "  Instalando pynput..."
    pip3 install pynput
    if python3 -c "import pynput" 2>/dev/null; then
        echo "✓ pynput instalado"
    else
        echo "✗ ERROR: No se pudo instalar pynput"
        exit 1
    fi
fi

# Verificar pygame
if python3 -c "import pygame" 2>/dev/null; then
    echo "✓ pygame instalado correctamente"
else
    echo "✗ pygame no encontrado"
    echo "  Instalando pygame..."
    pip3 install pygame
fi

# Verificar numpy
if python3 -c "import numpy" 2>/dev/null; then
    echo "✓ numpy instalado correctamente"
else
    echo "✗ numpy no encontrado"
    echo "  Instalando numpy..."
    pip3 install numpy
fi

echo ""
echo "Ejecutando NovaCheck..."
echo ""
python3 "$SCRIPT_PATH"
