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
# Nota: Las verificaciones de import fallarán sin X display
# pero los módulos estarán instalados correctamente
echo "Verificando dependencias críticas instaladas..."

# Verificar que los paquetes estén físicamente instalados
if python3 -m pip show pynput &>/dev/null; then
    echo "✓ pynput instalado"
else
    echo "✗ pynput no encontrado"
    echo "  Instalando pynput..."
    python3 -m pip install --break-system-packages pynput
    if python3 -m pip show pynput &>/dev/null; then
        echo "✓ pynput instalado"
    else
        echo "✗ ERROR: No se pudo instalar pynput"
        exit 1
    fi
fi

# Verificar pygame
if python3 -m pip show pygame &>/dev/null; then
    echo "✓ pygame instalado"
else
    echo "✗ pygame no encontrado"
    echo "  Instalando pygame..."
    python3 -m pip install --break-system-packages pygame
fi

# Verificar numpy
if python3 -m pip show numpy &>/dev/null; then
    echo "✓ numpy instalado"
else
    echo "✗ numpy no encontrado"
    echo "  Instalando numpy..."
    python3 -m pip install --break-system-packages numpy
fi

echo ""
echo "Ejecutando NovaCheck..."
echo ""
python3 "$SCRIPT_PATH"
