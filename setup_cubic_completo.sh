#!/bin/bash
# Script TODO-EN-UNO para configurar NovaCheck en Cubic
# Ejecutar dentro del entorno chroot de Cubic

set -e  # Salir si hay error

echo "========================================"
echo "  SETUP NOVACHECK PARA CUBIC"
echo "  (Script Todo-en-Uno)"
echo "========================================"
echo ""

# Verificar root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Ejecutar como root"
    exit 1
fi

# 1. ACTUALIZAR E INSTALAR DEPENDENCIAS
echo "1. Instalando dependencias del sistema..."
apt update
DEBIAN_FRONTEND=noninteractive apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    sox \
    alsa-utils \
    pulseaudio \
    pulseaudio-utils \
    smartmontools \
    usbutils \
    dmidecode \
    pciutils \
    hdparm \
    lshw \
    wireless-tools \
    net-tools \
    iw \
    wipe \
    dcfldd

# 2. INSTALAR PAQUETES PYTHON
echo ""
echo "2. Instalando paquetes Python globalmente..."
python3 -m pip install --break-system-packages --upgrade pip
python3 -m pip install --break-system-packages pynput pygame numpy

# 3. CONFIGURAR SCRIPT
echo ""
echo "3. Configurando script NovaCheck..."

# Verificar si main.py existe en /tmp o /app
if [ -f "/tmp/main.py" ]; then
    SCRIPT_SOURCE="/tmp/main.py"
elif [ -f "/app/main.py" ]; then
    SCRIPT_SOURCE="/app/main.py"
else
    echo "ERROR: No se encuentra main.py en /tmp ni /app"
    echo "Por favor, copia main.py a /tmp antes de ejecutar este script"
    exit 1
fi

mkdir -p /home/novacheck
cp "$SCRIPT_SOURCE" /home/novacheck/main.py
chmod +x /home/novacheck/main.py

# Verificar y corregir shebang
if ! grep -q "#!/usr/bin/python3" /home/novacheck/main.py; then
    echo "Corrigiendo shebang..."
    sed -i '1s|^#!.*python.*|#!/usr/bin/python3|' /home/novacheck/main.py
fi

# 4. CONFIGURAR AUTO-ARRANQUE CON .bash_profile
echo ""
echo "4. Configurando auto-arranque en TTY1..."

cat > /root/.bash_profile << 'EOFPROFILE'
# Auto-ejecutar NovaCheck en TTY1
if [ "$(tty)" = "/dev/tty1" ]; then
    # Limpiar pantalla
    clear
    
    # Configurar audio
    amixer sset Master 80% unmute 2>/dev/null || true
    amixer sset PCM 80% unmute 2>/dev/null || true
    amixer sset Speaker 80% unmute 2>/dev/null || true
    
    # Ejecutar NovaCheck
    /usr/bin/python3 /home/novacheck/main.py
    
    # Al terminar, preguntar si apagar
    echo ""
    echo "NovaCheck ha terminado."
    echo "Presiona ENTER para apagar, o Ctrl+C para cancelar..."
    read
    poweroff
fi
EOFPROFILE

# 5. CONFIGURAR AUTOLOGIN EN TTY1
echo ""
echo "5. Configurando autologin root en TTY1..."

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOFGETTY'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
Type=idle
EOFGETTY

# 6. DESHABILITAR ENTORNO GRÁFICO
echo ""
echo "6. Deshabilitando entorno gráfico..."

systemctl set-default multi-user.target

# Deshabilitar todos los display managers comunes
for dm in lightdm gdm gdm3 sddm; do
    systemctl disable $dm 2>/dev/null || true
done

# 7. OPTIMIZAR ARRANQUE
echo ""
echo "7. Optimizando arranque..."

# Reducir timeout de GRUB si existe
if [ -f /etc/default/grub ]; then
    sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' /etc/default/grub
fi

# Deshabilitar servicios innecesarios
for svc in bluetooth ModemManager avahi-daemon cups; do
    systemctl disable $svc 2>/dev/null || true
done

# 8. CONFIGURAR AUDIO POR DEFECTO
echo ""
echo "8. Configurando audio..."

cat > /etc/rc.local << 'EOFRC'
#!/bin/bash
# Configurar audio al arrancar
amixer sset Master 80% unmute 2>/dev/null
amixer sset PCM 80% unmute 2>/dev/null
amixer sset Speaker 80% unmute 2>/dev/null
exit 0
EOFRC
chmod +x /etc/rc.local

# Crear servicio para rc.local si no existe
if [ ! -f /etc/systemd/system/rc-local.service ]; then
    cat > /etc/systemd/system/rc-local.service << 'EOFRCSERVICE'
[Unit]
Description=/etc/rc.local
ConditionPathExists=/etc/rc.local

[Service]
Type=forking
ExecStart=/etc/rc.local start
TimeoutSec=0
StandardOutput=tty
RemainAfterExit=yes
SysVStartPriority=99

[Install]
WantedBy=multi-user.target
EOFRCSERVICE
    systemctl enable rc-local
fi

# 9. VERIFICACIÓN
echo ""
echo "9. Verificando instalación..."
echo ""

echo "Python:"
python3 --version

echo ""
echo "Paquetes Python:"
for pkg in pynput pygame numpy; do
    if python3 -m pip show $pkg &>/dev/null; then
        echo "  ✓ $pkg instalado"
    else
        echo "  ✗ $pkg NO instalado"
    fi
done

echo ""
echo "Herramientas de sistema:"
for cmd in sox aplay smartctl lsusb dmidecode; do
    if command -v $cmd &> /dev/null; then
        echo "  ✓ $cmd"
    else
        echo "  ✗ $cmd"
    fi
done

echo ""
echo "Configuración:"
echo "  Script: $([ -f /home/novacheck/main.py ] && echo '✓' || echo '✗') /home/novacheck/main.py"
echo "  Target: $(systemctl get-default)"
echo "  Autologin TTY1: $([ -f /etc/systemd/system/getty@tty1.service.d/override.conf ] && echo '✓' || echo '✗')"
echo "  .bash_profile: $([ -f /root/.bash_profile ] && echo '✓' || echo '✗')"

# 10. LIMPIAR
echo ""
echo "10. Limpiando archivos temporales..."
apt clean
apt autoremove -y

echo ""
echo "========================================"
echo "  INSTALACIÓN COMPLETADA"
echo "========================================"
echo ""
echo "Configuración aplicada:"
echo "  • Dependencias instaladas"
echo "  • Script en /home/novacheck/main.py"
echo "  • Auto-arranque en TTY1 configurado"
echo "  • Entorno gráfico deshabilitado"
echo ""
echo "Al arrancar desde el USB:"
echo "  1. Login automático como root"
echo "  2. Ejecución automática de NovaCheck"
echo "  3. Sin interfaz gráfica de Lubuntu"
echo ""
echo "Ahora puedes:"
echo "  - Escribir 'exit' para salir del chroot"
echo "  - Continuar en Cubic para generar la ISO"
echo ""
