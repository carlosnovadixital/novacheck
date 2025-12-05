#!/bin/bash
# Script para ejecutar NovaCheck con virtualenv

VENV_PATH="/home/novacheck/venv"
SCRIPT_PATH="/app/main.py"

echo "========================================="
echo "  NOVACHECK - Iniciando"
echo "========================================="
echo ""

# Verificar si existe virtualenv
if [ -d "$VENV_PATH" ]; then
    echo "✓ Virtualenv encontrado en $VENV_PATH"
    
    # Activar virtualenv
    source "$VENV_PATH/bin/activate"
    
    # Verificar pynput
    if python3 -c "import pynput" 2>/dev/null; then
        echo "✓ pynput instalado correctamente"
    else
        echo "✗ pynput no encontrado en virtualenv"
        echo "  Instalando pynput..."
        pip3 install pynput
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
    python3 "$SCRIPT_PATH"
    
else
    echo "⚠ Virtualenv no encontrado en $VENV_PATH"
    echo "  Creando virtualenv..."
    
    # Crear virtualenv
    python3 -m venv "$VENV_PATH"
    
    # Activar
    source "$VENV_PATH/bin/activate"
    
    # Instalar dependencias
    echo "  Instalando dependencias..."
    pip3 install --upgrade pip
    pip3 install pynput pygame numpy
    
    echo ""
    echo "✓ Virtualenv creado y configurado"
    echo "  Ejecutando NovaCheck..."
    python3 "$SCRIPT_PATH"
fi
