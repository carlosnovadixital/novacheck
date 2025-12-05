# ✅ SOLUCIÓN FINAL: Python Environment Mismatch

## 🎯 Problema Real Identificado por Troubleshoot Agent

El daemon estaba usando Python del venv (`/root/.venv/bin/python3`) mientras que `pynput` estaba instalado solo globalmente. El sys.path del venv no incluye los paquetes globales.

## 🔧 Solución Implementada

### 1. Cambio de Shebang (CRÍTICO)
```bash
# ANTES (incorrecto para daemon)
#!/usr/bin/env python3  # ← Usa el primer python3 en PATH (puede ser venv)

# DESPUÉS (correcto)
#!/usr/bin/python3       # ← Usa SIEMPRE el Python del sistema
```

### 2. Instalación Dual
`pynput` ahora está instalado en AMBOS lugares:
- ✅ Sistema: `/usr/local/lib/python3.11/dist-packages/pynput`
- ✅ Venv: `/root/.venv/lib/python3.11/site-packages/pynput`

### 3. Scripts Actualizados
- ✅ `/app/main.py`: Shebang cambiado a `#!/usr/bin/python3`
- ✅ `/app/install_dependencies.sh`: Instala globalmente con `--break-system-packages`
- ✅ `/app/run_novacheck.sh`: Verifica dependencias correctamente

## 📊 Diagnóstico Actual

```
Shebang de main.py: #!/usr/bin/python3 ✓
Python del sistema: /usr/bin/python3 (v3.11.2) ✓
pynput en sistema: /usr/local/lib/python3.11/dist-packages/ ✓
pynput en venv: /root/.venv/lib/python3.11/site-packages/ ✓
```

## 🧪 Cómo Verificar en Lubuntu

### Desde la Consola (Ctrl+F3)

```bash
# 1. Verificar que el script use el Python correcto
head -1 /app/main.py
# Debe mostrar: #!/usr/bin/python3

# 2. Verificar pynput en ese Python
/usr/bin/python3 -m pip show pynput

# 3. Ejecutar el script directamente
sudo /usr/bin/python3 /app/main.py
```

### Verificar que el DISPLAY esté configurado

Cuando ejecutes en Lubuntu con interfaz gráfica:
```bash
echo $DISPLAY
# Debe mostrar algo como: :0 o :0.0
```

Si no hay DISPLAY configurado, agrégalo antes de ejecutar:
```bash
export DISPLAY=:0
sudo /usr/bin/python3 /app/main.py
```

## 🚀 Configuración como Servicio Systemd

Si el script corre como servicio, crea `/etc/systemd/system/novacheck.service`:

```ini
[Unit]
Description=NovaCheck Hardware Diagnostic Tool
After=graphical.target

[Service]
Type=simple
# IMPORTANTE: Usa /usr/bin/python3 explícitamente
ExecStart=/usr/bin/python3 /app/main.py
User=root
# CRÍTICO: Configurar DISPLAY para que pynput funcione
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/[TU_USUARIO]/.Xauthority"
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
```

Reemplaza `[TU_USUARIO]` con tu usuario de Lubuntu.

Luego:
```bash
sudo systemctl daemon-reload
sudo systemctl enable novacheck.service
sudo systemctl start novacheck.service

# Ver logs si hay problemas
sudo journalctl -u novacheck.service -f
```

## 🔍 Troubleshooting

### Si sigue diciendo "pynput not found"

1. **Verificar qué Python usa el script:**
   ```bash
   # Ver la primera línea del script
   head -1 /app/main.py
   ```

2. **Instalar pynput en ESE Python específico:**
   ```bash
   # Si usa /usr/bin/python3
   sudo /usr/bin/python3 -m pip install --break-system-packages pynput
   
   # Si por alguna razón usa otro Python
   sudo /ruta/al/python3 -m pip install --break-system-packages pynput
   ```

3. **Verificar variables de entorno:**
   ```bash
   # En Lubuntu gráfico
   echo $DISPLAY  # Debe mostrar :0
   echo $PATH     # No debe tener venvs al inicio
   ```

### Si hay error de X11 Display

Esto es **NORMAL** en consola sin interfaz gráfica (Ctrl+F3). El error desaparecerá cuando:
- Ejecutes desde la interfaz gráfica de Lubuntu
- O configures DISPLAY=:0 antes de ejecutar

### Archivo de Test Rápido

Guarda esto como `/app/test_pynput.py`:
```python
#!/usr/bin/python3
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Path: {sys.path}")

try:
    import pynput
    print(f"✓ pynput encontrado: {pynput.__file__}")
    print(f"✓ pynput version: {pynput.__version__}")
except ImportError as e:
    print(f"✗ pynput NO encontrado: {e}")
```

Ejecuta:
```bash
sudo python3 /app/test_pynput.py
```

Debe mostrar que pynput está encontrado (el error de X11 vendrá después al intentar usarlo, pero eso es normal sin display).

## 📝 Resumen de Cambios

| Archivo | Cambio | Motivo |
|---------|--------|--------|
| `/app/main.py` | Shebang: `#!/usr/bin/python3` | Usar Python del sistema, no venv |
| `/usr/local/lib/.../pynput` | Instalado globalmente | Para Python del sistema |
| `/root/.venv/.../pynput` | Instalado en venv | Backup por si acaso |

## ⚠️ IMPORTANTE: Error de X11 es Normal

```
ImportError: this platform is not supported: ('failed to acquire X connection...')
```

Este error es **ESPERADO** cuando pruebas en consola sin GUI. 

✅ **Se resolverá automáticamente** cuando ejecutes en Lubuntu con interfaz gráfica donde `DISPLAY=:0` está configurado.

## 🎯 Próximo Paso

Por favor ejecuta en tu Lubuntu Live USB desde la interfaz gráfica:

```bash
cd /app
sudo /usr/bin/python3 main.py
```

O si está configurado como daemon, reinicia el servicio para que use el nuevo shebang.

El test de teclado con `pynput` debería funcionar ahora correctamente.
