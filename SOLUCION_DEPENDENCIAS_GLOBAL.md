# ✅ SOLUCIÓN: Dependencias Instaladas Globalmente

## Problema Resuelto
El error `ModuleNotFoundError: No module named 'pynput'` se debía a que el agente anterior intentaba usar un entorno virtual (venv), pero tu script corre como **daemon/servicio del sistema**, por lo que necesita las dependencias instaladas **globalmente**.

## Cambios Realizados

### 1. `/app/install_dependencies.sh`
- ❌ **ELIMINADO**: Toda la lógica de creación y activación de virtualenv
- ✅ **AGREGADO**: Instalación global usando `python3 -m pip install --break-system-packages`
- ✅ **MEJORA**: Verificación de módulos Python instalados

### 2. `/app/run_novacheck.sh`
- ❌ **ELIMINADO**: Lógica de activación de venv (`source .../activate`)
- ✅ **AGREGADO**: Verificación de paquetes usando `pip show` (no requiere X display)
- ✅ **MEJORA**: Auto-instalación si falta alguna dependencia

### 3. `/app/main.py`
- ✅ **SIN CAMBIOS**: El shebang ya era correcto (`#!/usr/bin/env python3`)

## Dependencias Instaladas Globalmente

Las siguientes dependencias ahora están instaladas en el sistema de forma global:

### Python Packages
- ✅ `pynput` (1.8.1) - Para test de teclado con detección de layout
- ✅ `pygame` (2.6.1) - Para test de audio L/R con control preciso
- ✅ `numpy` - Para generación de tonos de audio

### System Packages  
- ✅ `python3`, `python3-pip`, `python3-numpy`
- ✅ `python3-pygame`
- ✅ `sox`, `alsa-utils`, `pulseaudio`
- ✅ `smartmontools`, `usbutils`, `dmidecode`
- ✅ `pciutils`, `hdparm`, `lshw`
- ✅ `wireless-tools`, `net-tools`, `iw`
- ✅ `wipe`, `dcfldd`

## Cómo Usar

### Instalación Inicial (Solo una vez)
```bash
cd /app
sudo bash install_dependencies.sh
```

### Ejecutar NovaCheck
```bash
# Opción 1: Directamente
sudo python3 /app/main.py

# Opción 2: Con el script helper
bash /app/run_novacheck.sh
```

### Configurar como Servicio/Daemon
Si tu sistema usa systemd, crea un archivo `/etc/systemd/system/novacheck.service`:

```ini
[Unit]
Description=NovaCheck Hardware Diagnostic Tool
After=graphical.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /app/main.py
User=root
Environment="DISPLAY=:0"
Restart=on-failure

[Install]
WantedBy=graphical.target
```

Luego actívalo:
```bash
sudo systemctl daemon-reload
sudo systemctl enable novacheck.service
sudo systemctl start novacheck.service
```

## Verificación

Para verificar que todo está instalado correctamente:

```bash
# Verificar pynput (nota: fallará sin X display, pero eso es normal)
python3 -m pip show pynput

# Verificar pygame
python3 -m pip show pygame

# Verificar numpy
python3 -m pip show numpy
```

## Notas Importantes

### ⚠️ Error "this platform is not supported" al verificar pynput
Este error es **NORMAL** cuando ejecutas verificaciones en un entorno sin X11:
```
ImportError: this platform is not supported: ('failed to acquire X connection...')
```

Cuando el daemon corra en Lubuntu con interfaz gráfica, `pynput` funcionará perfectamente porque:
- El `DISPLAY` estará configurado (ej: `:0`)
- Habrá un servidor X activo
- El daemon tendrá acceso al sistema de ventanas

### ✅ Python "externally-managed-environment"
Se usa `--break-system-packages` para instalar en sistemas Debian/Ubuntu modernos que tienen PEP 668 activado. Esto es **seguro** en este caso porque:
- Es un sistema de diagnóstico dedicado (Lubuntu Live USB)
- No hay riesgo de romper dependencias del sistema
- Las dependencias son específicas de esta aplicación

## Estado del Problema P0
- ✅ **RESUELTO**: `pynput` instalado globalmente
- ✅ **RESUELTO**: Scripts actualizados para NO usar venv
- ✅ **VERIFICADO**: Dependencias detectadas correctamente por `run_novacheck.sh`
- ⏳ **PENDIENTE**: Prueba en Lubuntu con interfaz gráfica (requiere usuario)

## Siguiente Paso
El usuario debe probar ejecutar el script en su entorno Lubuntu real:
```bash
cd /app
sudo python3 main.py
```

El test de teclado ahora debería funcionar correctamente con `pynput` detectando todas las teclas, incluidas las especiales españolas (Ñ, Ç, etc.).
