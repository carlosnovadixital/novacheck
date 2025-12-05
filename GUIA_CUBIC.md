# 🚀 GUÍA COMPLETA: Preparar NovaCheck en Cubic

## 📋 Contexto

Estás creando una **imagen ISO personalizada de Lubuntu Live USB** usando **Cubic**, donde el script NovaCheck se ejecutará automáticamente al arrancar, **sin mostrar el escritorio de Lubuntu**.

## 🎯 Objetivo

Cuando arranque desde el USB:
1. ❌ NO aparece el escritorio de Lubuntu
2. ✅ Se ejecuta automáticamente el script NovaCheck en TTY1
3. ✅ El técnico ve directamente la interfaz de diagnóstico
4. ✅ Todo funciona sin intervención manual

## 📦 Preparación de Archivos

Antes de abrir Cubic, ten listos estos archivos en una carpeta:

```
/tu/carpeta/
├── main.py                      # Tu script NovaCheck
├── install_dependencies.sh      # Script de instalación
└── configurar_autoarranque.sh   # Script de configuración
```

## 🔧 Pasos en Cubic

### 1. Abrir Cubic y Cargar ISO Base

```bash
# Abrir Cubic
cubic
```

1. Selecciona tu ISO de Lubuntu original
2. Espera a que monte el sistema de archivos
3. Cuando aparezca la terminal chroot, estás dentro del entorno

### 2. Copiar Archivos al Entorno Chroot

Desde **OTRA terminal** (NO la de Cubic):

```bash
# Encontrar el punto de montaje de Cubic
# Usualmente está en ~/cubic/custom-root/ o similar

# Copiar archivos
sudo cp main.py ~/cubic/custom-root/home/novacheck/
sudo cp install_dependencies.sh ~/cubic/custom-root/tmp/
sudo cp configurar_autoarranque.sh ~/cubic/custom-root/tmp/
```

O usa la interfaz de Cubic si tiene opción de copiar archivos.

### 3. Dentro del Terminal Chroot de Cubic

Ejecuta estos comandos **en la terminal de Cubic**:

#### A. Instalar Dependencias

```bash
cd /tmp
chmod +x install_dependencies.sh
bash install_dependencies.sh
```

Esto instalará:
- Python 3 y pip
- pynput, pygame, numpy (con --break-system-packages)
- sox, alsa-utils, pulseaudio
- smartmontools, usbutils, dmidecode, etc.

#### B. Configurar Auto-Arranque

**Opción 1: Usando systemd (RECOMENDADO)**

```bash
# Crear directorio si no existe
mkdir -p /home/novacheck

# Copiar script
cp /tmp/main.py /home/novacheck/main.py
chmod +x /home/novacheck/main.py

# Crear servicio systemd
cat > /etc/systemd/system/novacheck.service << 'EOF'
[Unit]
Description=NovaCheck Hardware Diagnostic Tool
After=multi-user.target
DefaultDependencies=no

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/novacheck/main.py
StandardInput=tty-force
StandardOutput=inherit
StandardError=inherit
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
Restart=no
User=root
Environment="TERM=linux"

[Install]
WantedBy=multi-user.target
EOF

# Habilitar servicio
systemctl enable novacheck.service

# Configurar autologin root en TTY1
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF

# Deshabilitar entorno gráfico
systemctl set-default multi-user.target

# Deshabilitar display manager
systemctl disable lightdm || true
systemctl disable gdm || true
```

**Opción 2: Usando .bash_profile (MÁS SIMPLE)**

```bash
# Agregar al .bash_profile de root
cat >> /root/.bash_profile << 'EOF'

# Auto-ejecutar NovaCheck en TTY1
if [ "$(tty)" = "/dev/tty1" ]; then
    /usr/bin/python3 /home/novacheck/main.py
    # Al terminar, apagar
    poweroff
fi
EOF

# Configurar autologin root en TTY1
mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF

# Deshabilitar GUI
systemctl set-default multi-user.target
systemctl disable lightdm || true
systemctl disable gdm || true
```

#### C. Verificar Instalación

```bash
# Verificar Python
python3 --version

# Verificar pynput (puede fallar con error X11, es normal en chroot)
python3 -m pip show pynput

# Verificar que el script existe
ls -la /home/novacheck/main.py

# Verificar que el servicio está habilitado (si usas systemd)
systemctl is-enabled novacheck.service
```

### 4. Configuraciones Adicionales (Opcional)

#### Acelerar Arranque

```bash
# Reducir timeout de GRUB
sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=2/' /etc/default/grub

# Deshabilitar servicios innecesarios
systemctl disable bluetooth
systemctl disable ModemManager
systemctl disable avahi-daemon
```

#### Configurar Audio

```bash
# Pre-configurar volumen
cat > /etc/rc.local << 'EOF'
#!/bin/bash
amixer sset Master 80% unmute
amixer sset PCM 80% unmute
amixer sset Speaker 80% unmute
exit 0
EOF
chmod +x /etc/rc.local
```

### 5. Limpiar y Salir de Cubic

```bash
# Limpiar archivos temporales
rm /tmp/*.sh
apt clean
apt autoremove -y

# Salir del chroot
exit
```

En la interfaz de Cubic:
1. Click en "Next" o "Siguiente"
2. Genera la ISO personalizada
3. Espera a que termine el proceso

## 🧪 Probar la ISO

### 1. Grabar en USB

```bash
# Con dd
sudo dd if=tu-iso-personalizada.iso of=/dev/sdX bs=4M status=progress && sync

# O con Etcher, Ventoy, etc.
```

### 2. Arrancar desde USB

1. Conecta el USB a un PC de prueba
2. Arranca desde USB
3. **Debería aparecer directamente el script NovaCheck** sin mostrar Lubuntu

### 3. Si No Funciona

Presiona `Ctrl+Alt+F2` para ir a TTY2 y ejecuta:

```bash
# Ver logs del servicio
sudo journalctl -u novacheck.service -n 50

# Ver si el servicio está corriendo
sudo systemctl status novacheck.service

# Ejecutar manualmente para ver errores
sudo /usr/bin/python3 /home/novacheck/main.py
```

## 🔍 Troubleshooting Común

### Problema: "pynput not found"

**En Cubic**, ejecuta:
```bash
python3 -m pip install --break-system-packages pynput --force-reinstall
```

### Problema: "X connection error"

**NORMAL en chroot**. En el USB real con hardware, funcionará.

### Problema: Aparece el escritorio de Lubuntu

Verifica que deshabilitaste la GUI:
```bash
systemctl get-default
# Debe decir: multi-user.target

# Si dice graphical.target:
systemctl set-default multi-user.target
```

### Problema: No aparece nada, pantalla negra

El script puede estar esperando en alguna parte. Presiona `Ctrl+Alt+F1` para ir a TTY1.

### Problema: Error "setupterm: could not find terminal"

Asegúrate de que el servicio tiene:
```ini
Environment="TERM=linux"
```

## 📝 Script Completo Todo-en-Uno

Si quieres un solo script que haga todo, crea `/tmp/setup_novacheck.sh` en Cubic:

```bash
#!/bin/bash
set -e

echo "Instalando dependencias..."
apt update
apt install -y python3 python3-pip sox alsa-utils smartmontools \
               usbutils dmidecode pciutils hdparm lshw wireless-tools \
               net-tools iw wipe dcfldd pulseaudio

echo "Instalando paquetes Python..."
python3 -m pip install --break-system-packages pynput pygame numpy

echo "Configurando script..."
mkdir -p /home/novacheck
# Asume que main.py ya fue copiado a /tmp/
cp /tmp/main.py /home/novacheck/main.py
chmod +x /home/novacheck/main.py

echo "Configurando auto-arranque..."
cat >> /root/.bash_profile << 'EOF'
if [ "$(tty)" = "/dev/tty1" ]; then
    /usr/bin/python3 /home/novacheck/main.py
    poweroff
fi
EOF

mkdir -p /etc/systemd/system/getty@tty1.service.d
cat > /etc/systemd/system/getty@tty1.service.d/override.conf << 'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin root --noclear %I $TERM
EOF

systemctl set-default multi-user.target
systemctl disable lightdm || true

echo "✓ Configuración completada"
```

Ejecuta en Cubic:
```bash
cd /tmp
bash setup_novacheck.sh
```

## ✅ Checklist Final

Antes de generar la ISO, verifica:

- [ ] Dependencias Python instaladas (`python3 -m pip show pynput`)
- [ ] Script copiado a `/home/novacheck/main.py`
- [ ] Script tiene permisos de ejecución (`chmod +x`)
- [ ] Shebang correcto en main.py (`#!/usr/bin/python3`)
- [ ] Target configurado a multi-user (`systemctl get-default`)
- [ ] Display manager deshabilitado
- [ ] Autologin configurado en TTY1
- [ ] Auto-ejecución configurada (.bash_profile o servicio)

## 🎯 Resultado Esperado

Al arrancar desde el USB:
1. Grub → 2 segundos
2. Arranque de Linux → ~10-15 segundos
3. **NovaCheck aparece automáticamente en pantalla completa**
4. El técnico ve directamente la interfaz TUI del diagnóstico

Sin tocar nada, sin ver Lubuntu, directo al script.

---

¿Tienes Cubic abierto ahora? ¿En qué paso estás?
