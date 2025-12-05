#!/bin/bash
# Configuración de auto-arranque para NovaCheck en Live USB
# Ejecutar dentro de Cubic

echo "========================================="
echo "  CONFIGURAR AUTOARRANQUE NOVACHECK"
echo "========================================="
echo ""

# Crear usuario novacheck si no existe
if ! id -u novacheck &>/dev/null; then
    echo "Creando usuario novacheck..."
    useradd -m -s /bin/bash novacheck
    echo "novacheck:novacheck" | chpasswd
fi

# Copiar script
echo "Copiando script a /home/novacheck..."
cp /app/main.py /home/novacheck/main.py
chmod +x /home/novacheck/main.py
chown novacheck:novacheck /home/novacheck/main.py

# Configurar .bashrc para auto-ejecución
echo "Configurando auto-ejecución en .bashrc..."
cat > /home/novacheck/.bashrc << 'EOF'
# Auto-ejecutar NovaCheck al hacer login
if [ -z "$NOVACHECK_RAN" ]; then
    export NOVACHECK_RAN=1
    
    # Esperar a que el sistema termine de arrancar
    sleep 3
    
    # Ejecutar NovaCheck
    sudo /usr/bin/python3 /home/novacheck/main.py
    
    # Al terminar, apagar o reiniciar
    # sudo poweroff
fi
EOF

chown novacheck:novacheck /home/novacheck/.bashrc

# Configurar sudoers para que novacheck pueda ejecutar sin password
echo "Configurando sudoers..."
echo "novacheck ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/novacheck
chmod 440 /etc/sudoers.d/novacheck

# Configurar autologin para novacheck en TTY1
echo "Configurando autologin en TTY1..."
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin novacheck --noclear %I $TERM
Type=idle
EOF

# Deshabilitar GUI
echo "Deshabilitando entorno gráfico..."
systemctl set-default multi-user.target

# Deshabilitar servicios innecesarios para arranque más rápido
systemctl disable lightdm 2>/dev/null || true
systemctl disable gdm 2>/dev/null || true
systemctl disable sddm 2>/dev/null || true

echo ""
echo "========================================="
echo "  CONFIGURACIÓN COMPLETADA"
echo "========================================="
echo ""
echo "Al arrancar el Live USB:"
echo "  1. Se hará login automático como 'novacheck'"
echo "  2. Se ejecutará automáticamente main.py"
echo "  3. El técnico verá directamente el script"
echo ""
