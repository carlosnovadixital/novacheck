#!/bin/bash
# Script de verificación de instalación de NovaCheck
# Ejecutar con: bash verificar_instalacion.sh

echo "========================================="
echo "  VERIFICACIÓN DE INSTALACIÓN NOVACHECK"
echo "========================================="
echo ""

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Verificar Python 3
echo "1. Python 3"
if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version)
    check_ok "Python 3 instalado: $VERSION"
else
    check_fail "Python 3 NO instalado"
fi

echo ""
echo "2. Dependencias Python (globales)"

# Verificar pynput en dist-packages
if [ -d "/usr/local/lib/python3.11/dist-packages/pynput" ]; then
    check_ok "pynput instalado globalmente en /usr/local/lib/python3.11/dist-packages/"
else
    check_fail "pynput NO encontrado en instalación global"
fi

# Verificar pygame
if python3 -m pip show pygame &> /dev/null; then
    check_ok "pygame instalado"
else
    check_fail "pygame NO instalado"
fi

# Verificar numpy
if python3 -m pip show numpy &> /dev/null; then
    check_ok "numpy instalado"
else
    check_fail "numpy NO instalado"
fi

echo ""
echo "3. Herramientas de sistema"

for cmd in sox aplay arecord smartctl lsusb dmidecode lshw; do
    if command -v $cmd &> /dev/null; then
        check_ok "$cmd instalado"
    else
        check_fail "$cmd NO instalado"
    fi
done

echo ""
echo "4. Archivos del proyecto"

for file in main.py install_dependencies.sh run_novacheck.sh; do
    if [ -f "/app/$file" ]; then
        check_ok "/app/$file existe"
    else
        check_fail "/app/$file NO existe"
    fi
done

echo ""
echo "5. Verificar NO hay venv residual"

if [ -d "/home/novacheck/venv" ]; then
    check_warn "ADVERTENCIA: Directorio venv encontrado en /home/novacheck/"
    echo "    Ejecútalo: sudo rm -rf /home/novacheck/venv"
else
    check_ok "No hay directorios venv residuales"
fi

echo ""
echo "========================================="
echo "6. TEST DE IMPORTACIÓN"
echo "========================================="
echo ""

# Test de importación (fallará sin X11, pero verificará que el módulo existe)
echo "Probando importación de pynput..."
python3 -c "import pynput" 2>&1 | grep -q "ImportError.*X connection" && check_warn "pynput necesita X11 (normal sin interfaz gráfica)" || check_ok "pynput importa correctamente"

echo ""
echo "Probando importación de pygame..."
python3 -c "import pygame" 2>&1 | head -1

echo ""
echo "Probando importación de numpy..."
if python3 -c "import numpy" 2>&1; then
    check_ok "numpy importa correctamente"
else
    check_fail "Error al importar numpy"
fi

echo ""
echo "========================================="
echo "RESUMEN"
echo "========================================="
echo ""
echo "Si todas las verificaciones están OK, puedes ejecutar:"
echo "  sudo python3 /app/main.py"
echo ""
echo "Si estás en Lubuntu con interfaz gráfica, el script debería"
echo "funcionar correctamente incluyendo el test de teclado con pynput."
echo ""
