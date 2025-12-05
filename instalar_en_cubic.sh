#!/bin/bash
# Script de instalación para ejecutar DENTRO de Cubic (entorno chroot)
# Este script prepara la imagen ISO para que NovaCheck arranque automáticamente

set -e  # Salir si hay errores

echo "========================================="
echo "  INSTALACIÓN NOVACHECK PARA CUBIC"
echo "========================================="
echo ""

# Verificar que estamos en root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Este script debe ejecutarse como root"
    exit 1
fi

echo "1. ACTUALIZANDO REPOSITORIOS..."
apt update

echo ""
echo "2. INSTALANDO PYTHON Y DEPENDENCIAS BASE..."
apt install -y python3 python3-pip python3-dev build-essential

echo ""
echo "3. INSTALANDO DEPENDENCIAS PYTHON GLOBALMENTE..."
# Usar --break-system-packages porque estamos en un Live USB
python3 -m pip install --break-system-packages pynput pygame numpy

echo ""
echo "4. INSTALANDO HERRAMIENTAS DE AUDIO..."
apt install -y sox alsa-utils pulseaudio pulseaudio-utils

echo ""
echo "5. INSTALANDO HERRAMIENTAS DE HARDWARE..."
apt install -y smartmontools usbutils dmidecode pciutils hdparm lshw

echo ""
echo "6. INSTALANDO HERRAMIENTAS DE RED..."
apt install -y wireless-tools net-tools iw

echo ""
echo "7. INSTALANDO UTILIDADES DE BORRADO..."
apt install -y wipe dcfldd

echo ""
echo "8. COPIANDO SCRIPT NOVACHECK..."
# Asumiendo que el script está en /app/main.py
if [ ! -f "/home/novacheck/main.py" ]; then
    mkdir -p /home/novacheck
    cp /app/main.py /home/novacheck/main.py
    chmod +x /home/novacheck/main.py
fi

echo ""
echo "9. CONFIGURANDO SERVICIO SYSTEMD..."
cat > /etc/systemd/system/novacheck.service << 'EOF'
[Unit]
Description=NovaCheck Hardware Diagnostic Tool
After=multi-user.target
DefaultDependencies=no

[Service]
Type=idle
ExecStart=/usr/bin/openvt -c 1 -s -w -- /usr/bin/python3 /home/novacheck/main.py
StandardInput=tty
StandardOutput=tty
Restart=no
User=root
Environment="TERM=linux"

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "10. HABILITANDO SERVICIO..."
systemctl enable novacheck.service

echo ""
echo "11. CONFIGURANDO AUTOLOGIN EN TTY1..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF

echo ""
echo "12. DESHABILITANDO ENTORNO GRÁFICO..."
systemctl set-default multi-user.target

echo ""
echo "13. VERIFICANDO INSTALACIÓN..."
echo ""
echo "Python:"
python3 --version

echo ""
echo "Dependencias Python:"
python3 -m pip show pynput 2>&1 | head -3 || echo "⚠ pynput check (normal error en chroot)"
python3 -m pip show pygame 2>&1 | head -3 || echo "⚠ pygame check"
python3 -m pip show numpy 2>&1 | head -3 || echo "⚠ numpy check"

echo ""
echo "Herramientas de sistema:"
for cmd in sox aplay smartctl lsusb dmidecode; do
    if command -v $cmd &> /dev/null; then
        echo "✓ $cmd"
    else
        echo "✗ $cmd NO INSTALADO"
    fi
done

echo ""
echo "========================================="
echo "  INSTALACIÓN COMPLETADA"
echo "========================================="
echo ""
echo "El script NovaCheck se ejecutará automáticamente"
echo "en TTY1 cuando arranque el Live USB."
echo ""
echo "CONFIGURACIÓN:"
echo "  • Script: /home/novacheck/main.py"
echo "  • Servicio: novacheck.service (habilitado)"
echo "  • Target: multi-user.target (sin GUI)"
echo "  • Autologin: root en TTY1"
echo ""
echo "Ahora puedes cerrar Cubic y generar la ISO."
echo ""
