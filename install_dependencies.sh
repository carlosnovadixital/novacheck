#!/bin/bash
# Script de instalación de dependencias para NovaCheck
# Ejecutar con: sudo bash install_dependencies.sh

echo "========================================="
echo "  INSTALACIÓN DE DEPENDENCIAS NOVACHECK"
echo "========================================="
echo ""

# Verificar que se ejecuta como root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Este script debe ejecutarse como root (usa sudo)"
    exit 1
fi

echo "Actualizando repositorios..."
apt update

echo ""
echo "========================================="
echo "1. PYTHON Y HERRAMIENTAS BÁSICAS"
echo "========================================="

apt install -y python3 python3-pip python3-venv python3-numpy

echo "Instalando pygame (para audio L/R)..."
apt install -y python3-pygame

echo ""
echo "========================================="
echo "2. CONFIGURANDO VIRTUALENV"
echo "========================================="

VENV_PATH="/home/novacheck/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "Creando virtualenv en $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
fi

echo "Activando virtualenv..."
source "$VENV_PATH/bin/activate"

echo "Instalando pynput (para test de teclado)..."
pip3 install --upgrade pip
pip3 install pynput

echo "Instalando pygame y numpy en virtualenv..."
pip3 install pygame numpy

echo "✓ Virtualenv configurado correctamente"
deactivate

echo ""
echo "========================================="
echo "3. AUDIO (CRÍTICO)"
echo "========================================="

# Sox - Para generar archivos de audio con canales L/R específicos
echo "Instalando sox..."
apt install -y sox

# ALSA utils - aplay, amixer, arecord
echo "Instalando alsa-utils..."
apt install -y alsa-utils

# PulseAudio (normalmente ya está en Lubuntu)
echo "Verificando PulseAudio..."
apt install -y pulseaudio pulseaudio-utils

echo ""
echo "========================================="
echo "4. HERRAMIENTAS DE HARDWARE"
echo "========================================="

# smartmontools - Para smartctl (test de discos SMART)
echo "Instalando smartmontools..."
apt install -y smartmontools

# usbutils - Para lsusb (test USB)
echo "Instalando usbutils..."
apt install -y usbutils

# dmidecode - Info de hardware (modelo, serial, etc.)
echo "Instalando dmidecode..."
apt install -y dmidecode

# pciutils - lspci
echo "Instalando pciutils..."
apt install -y pciutils

# hdparm - Info de discos
echo "Instalando hdparm..."
apt install -y hdparm

# lshw - Listado completo de hardware
echo "Instalando lshw..."
apt install -y lshw

echo ""
echo "========================================="
echo "4. HERRAMIENTAS DE RED"
echo "========================================="

# Para test de WiFi
apt install -y wireless-tools net-tools iw

echo ""
echo "========================================="
echo "5. UTILIDADES DEL SISTEMA"
echo "========================================="

# Para borrado seguro de discos
apt install -y wipe dcfldd

echo ""
echo "========================================="
echo "VERIFICACIÓN DE INSTALACIÓN"
echo "========================================="
echo ""

# Función para verificar comando
check_command() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1 instalado correctamente"
        return 0
    else
        echo "✗ $1 NO encontrado"
        return 1
    fi
}

# Verificar comandos críticos
echo "AUDIO:"
check_command sox
check_command aplay
check_command arecord
check_command paplay

echo ""
echo "HARDWARE:"
check_command smartctl
check_command lsusb
check_command dmidecode
check_command lshw

echo ""
echo "SISTEMA:"
check_command python3

echo ""
echo "========================================="
echo "CONFIGURACIÓN DE AUDIO"
echo "========================================="
echo ""

# Asegurar que ALSA está configurado correctamente
echo "Configurando mixer de audio..."
amixer sset Master unmute 2>/dev/null
amixer sset Master 80% 2>/dev/null
amixer sset PCM unmute 2>/dev/null
amixer sset PCM 80% 2>/dev/null
amixer sset Speaker unmute 2>/dev/null
amixer sset Speaker 80% 2>/dev/null

echo ""
echo "Dispositivos de audio detectados:"
aplay -l 2>/dev/null || echo "No se detectaron dispositivos de reproducción"

echo ""
echo "========================================="
echo "INSTALACIÓN COMPLETADA"
echo "========================================="
echo ""
echo "Resumen:"
echo "  ✓ Python 3 y herramientas básicas"
echo "  ✓ Sox y ALSA (audio)"
echo "  ✓ Smartmontools (discos)"
echo "  ✓ Herramientas de hardware"
echo "  ✓ Utilidades de sistema"
echo ""
echo "Para ejecutar NovaCheck:"
echo "  sudo python3 /app/main.py"
echo ""
echo "Para probar audio:"
echo "  bash /app/test_audio_devices.sh"
echo ""
