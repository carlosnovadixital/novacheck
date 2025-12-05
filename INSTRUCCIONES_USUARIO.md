# 📋 INSTRUCCIONES PARA EJECUTAR NOVACHECK EN LUBUNTU

## ✅ Estado Actual: TODO INSTALADO CORRECTAMENTE

El problema P0 está **RESUELTO**. `pynput` está instalado y el script está configurado correctamente.

## 🎯 Lo Que Pasaba

Tu observación era correcta: cuando ejecutabas `pip3 install pynput` desde la consola (Ctrl+F3), decía "already installed". El problema era que el daemon usaba un Python diferente (del venv) que no tenía acceso a esa instalación.

### ✅ Solución Aplicada

1. **Shebang corregido**: `/app/main.py` ahora usa `#!/usr/bin/python3` (Python del sistema)
2. **pynput instalado en ambos lugares**: Sistema Y venv (por seguridad)
3. **Scripts actualizados**: Para instalar correctamente las dependencias

## 🚀 Cómo Ejecutar NovaCheck

### Opción 1: Ejecución Directa (RECOMENDADO)

Desde Lubuntu Live USB con interfaz gráfica:

```bash
cd /app
sudo /usr/bin/python3 main.py
```

### Opción 2: Verificar Primero

Si quieres estar 100% seguro antes de ejecutar:

```bash
# 1. Verificar que pynput esté instalado
sudo /usr/bin/python3 /app/test_pynput.py

# 2. Si el test dice "INSTALADO CORRECTAMENTE", ejecuta el script
sudo /usr/bin/python3 /app/main.py
```

### Opción 3: Configurar como Servicio de Inicio

Si quieres que NovaCheck inicie automáticamente al arrancar Lubuntu:

#### A. Crear el archivo de servicio

```bash
sudo nano /etc/systemd/system/novacheck.service
```

Pega este contenido (ajusta TU_USUARIO):

```ini
[Unit]
Description=NovaCheck Hardware Diagnostic Tool
After=graphical.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /app/main.py
User=root
Environment="DISPLAY=:0"
Environment="XAUTHORITY=/home/TU_USUARIO/.Xauthority"
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical.target
```

Reemplaza `TU_USUARIO` con tu usuario de Lubuntu (ej: `lubuntu`, `user`, etc.).

#### B. Activar el servicio

```bash
sudo systemctl daemon-reload
sudo systemctl enable novacheck.service
sudo systemctl start novacheck.service
```

#### C. Ver el estado

```bash
# Ver si está corriendo
sudo systemctl status novacheck.service

# Ver logs en tiempo real
sudo journalctl -u novacheck.service -f

# Ver últimos errores
sudo journalctl -u novacheck.service -n 50
```

## 🔍 Troubleshooting

### ❌ Si dice "pynput not found"

1. **Verifica qué Python usa el script:**
   ```bash
   head -1 /app/main.py
   ```
   Debe decir: `#!/usr/bin/python3`

2. **Ejecuta el test de diagnóstico:**
   ```bash
   sudo /usr/bin/python3 /app/test_pynput.py
   ```
   
3. **Si el test falla, reinstala:**
   ```bash
   sudo /usr/bin/python3 -m pip install --break-system-packages pynput
   ```

### ❌ Si el test dice "X connection" (desde consola Ctrl+F3)

**ESTO ES NORMAL**. La consola TTY (Ctrl+F3) no tiene servidor X11.

✅ **Solución**: Ejecuta desde la interfaz gráfica de Lubuntu, NO desde Ctrl+F3.

O configura DISPLAY:
```bash
export DISPLAY=:0
sudo /usr/bin/python3 /app/main.py
```

### ❌ Si el servicio no inicia

```bash
# Ver errores
sudo journalctl -u novacheck.service -n 50

# Problemas comunes:
# 1. XAUTHORITY incorrecto → verifica el usuario en el .service
# 2. Permisos → asegúrate de que el servicio corre como root
# 3. DISPLAY no configurado → verifica Environment="DISPLAY=:0"
```

## 📊 Verificación Rápida

Ejecuta este comando para un diagnóstico completo:

```bash
cd /app
sudo bash diagnostico_python.sh
```

Busca estas líneas en la salida:

```
Shebang: #!/usr/bin/python3             ← Debe ser este
Python del sistema: /usr/bin/python3    ← Debe existir
pynput en sistema: (debe listar archivos) ← Debe tener pynput/
```

## 🎯 Test Final del Teclado

Una vez que el script arranque:

1. **Llegará a la pantalla de "TEST DE TECLADO"**
2. **Verás un layout de teclado en pantalla**
3. **Presiona todas las teclas** incluidas:
   - Teclas normales (letras, números)
   - Teclas españolas: `Ñ`, `Ç`, `´`, `¡`, `¿`
   - Teclas especiales: `F1`-`F12`, `TAB`, `ENTER`, `SPACE`
   - Teclas modificadoras: `CTRL`, `ALT`, `SHIFT`
4. **Presiona ESC 3 veces** para terminar el test
5. **El test mostrará cuántas teclas detectó**

Si detecta menos de 35 teclas, el test fallará. Si detecta 35+, pasará automáticamente.

## 📝 Notas Importantes

### ⚠️ NO ejecutes desde Ctrl+F3
La consola TTY no tiene X11. **SIEMPRE ejecuta desde la interfaz gráfica** de Lubuntu.

### ✅ El script está listo
- Shebang correcto: ✓
- pynput instalado: ✓
- Scripts configurados: ✓
- Todo verificado: ✓

### 🎮 Modo de Prueba
Si quieres solo probar el test de teclado sin ejecutar todo el diagnóstico:

```python
# Crea un archivo de test simple
sudo nano /tmp/test_keyboard.py
```

Contenido:
```python
#!/usr/bin/python3
import curses

def test(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.addstr(0, 0, "TEST: Presiona cualquier tecla (Q para salir)")
    stdscr.refresh()
    
    from pynput import keyboard
    
    keys = set()
    
    def on_press(key):
        try:
            keys.add(str(key))
            stdscr.addstr(2, 0, f"Teclas presionadas: {len(keys)}")
            stdscr.refresh()
        except:
            pass
    
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    while True:
        k = stdscr.getch()
        if k == ord('q'):
            break
    
    listener.stop()

if __name__ == "__main__":
    curses.wrapper(test)
```

Ejecuta:
```bash
sudo python3 /tmp/test_keyboard.py
```

## 💡 Siguiente Paso

Por favor ejecuta desde Lubuntu con interfaz gráfica:

```bash
sudo /usr/bin/python3 /app/main.py
```

Y confirma si el test de teclado funciona correctamente. 

Si tienes algún error, envía el mensaje de error completo y lo solucionaremos.
