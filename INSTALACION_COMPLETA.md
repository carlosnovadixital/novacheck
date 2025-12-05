# NOVACHECK - GUÍA DE INSTALACIÓN COMPLETA

## 📦 DEPENDENCIAS NECESARIAS

### ✅ **1. AUDIO (CRÍTICO para que funcione)**

| Paquete | Para qué sirve | Comando incluido |
|---------|----------------|------------------|
| **sox** | Generar archivos de audio con canales L/R específicos | `sox` |
| **alsa-utils** | Reproducir audio, controlar volumen, grabar micrófono | `aplay`, `arecord`, `amixer` |
| **pulseaudio** | Sistema de audio (normalmente ya está en Lubuntu) | `paplay` |

**Sin sox y alsa-utils el audio NO funcionará.**

---

### ✅ **2. HERRAMIENTAS DE HARDWARE**

| Paquete | Para qué sirve | Test que usa |
|---------|----------------|--------------|
| **smartmontools** | Test SMART de discos duros | Auto-tests (discos) |
| **usbutils** | Detectar dispositivos USB | Test USB |
| **dmidecode** | Leer info BIOS (modelo, serial) | Hardware Info |
| **lshw** | Listar hardware completo | Hardware Info |
| **hdparm** | Info de discos duros | Auto-tests |
| **pciutils** | Listar dispositivos PCI | Hardware Info |

---

### ✅ **3. HERRAMIENTAS DE RED**

| Paquete | Para qué sirve |
|---------|----------------|
| **wireless-tools** | Test WiFi |
| **net-tools** | Comandos de red |
| **iw** | Herramientas WiFi modernas |

---

### ✅ **4. UTILIDADES DEL SISTEMA**

| Paquete | Para qué sirve |
|---------|----------------|
| **wipe** | Borrado seguro de discos |
| **dcfldd** | Borrado de discos mejorado |

---

### ✅ **5. PYTHON**

| Paquete | Para qué sirve |
|---------|----------------|
| **python3** | Ejecutar el script |

**Nota:** La librería `curses` viene incluida en Python 3 estándar, no necesita instalarse.

---

## 🚀 INSTALACIÓN AUTOMÁTICA

He creado un script que instala TODO automáticamente:

### **Opción 1: Instalación automática (RECOMENDADO)**

```bash
# Copiar el script al pendrive y ejecutar:
sudo bash /app/install_dependencies.sh
```

Este script:
- ✅ Actualiza repositorios
- ✅ Instala todas las dependencias
- ✅ Configura el audio (volumen, unmute)
- ✅ Verifica que todo esté instalado
- ✅ Muestra dispositivos de audio detectados

---

### **Opción 2: Instalación manual**

Si prefieres instalarlo paso a paso:

```bash
# 1. Actualizar sistema
sudo apt update

# 2. AUDIO (CRÍTICO)
sudo apt install -y sox alsa-utils pulseaudio pulseaudio-utils

# 3. HERRAMIENTAS DE HARDWARE
sudo apt install -y smartmontools usbutils dmidecode pciutils hdparm lshw

# 4. HERRAMIENTAS DE RED
sudo apt install -y wireless-tools net-tools iw

# 5. UTILIDADES
sudo apt install -y wipe dcfldd

# 6. PYTHON (normalmente ya está)
sudo apt install -y python3
```

---

## ✅ VERIFICACIÓN POST-INSTALACIÓN

### **Verificar que todo está instalado:**

```bash
# Audio (CRÍTICO)
which sox          # Debe mostrar: /usr/bin/sox
which aplay        # Debe mostrar: /usr/bin/aplay
which arecord      # Debe mostrar: /usr/bin/arecord

# Hardware
which smartctl     # Debe mostrar: /usr/bin/smartctl
which lsusb        # Debe mostrar: /usr/bin/lsusb
which dmidecode    # Debe mostrar: /usr/sbin/dmidecode

# Python
python3 --version  # Debe mostrar: Python 3.x.x
```

---

### **Probar audio:**

```bash
# Ver dispositivos de audio disponibles
aplay -l

# Probar diagnóstico de audio
bash /app/test_audio_devices.sh

# Generar y reproducir audio de prueba
sox -n /tmp/test.wav synth 1 sine 800
aplay /tmp/test.wav
```

**Deberías escuchar un tono de 1 segundo.**

---

## 🔧 CONFIGURACIÓN ADICIONAL

### **Configurar volumen inicial:**

```bash
# Subir volumen y quitar mute
sudo amixer sset Master unmute
sudo amixer sset Master 80%
sudo amixer sset PCM unmute
sudo amixer sset PCM 80%
sudo amixer sset Speaker unmute
sudo amixer sset Speaker 80%
```

Esto está incluido en el script de instalación automática.

---

### **Permisos:**

NovaCheck necesita ejecutarse como root para:
- Acceder a información de hardware (dmidecode)
- Leer/escribir en discos
- Acceder a dispositivos de audio
- Ejecutar tests de sistema

```bash
sudo python3 /app/main.py
```

---

## 📝 NOTAS IMPORTANTES

### **1. Sobre sox:**

Sox es **CRÍTICO** para que funcionen las pruebas separadas de altavoz IZQUIERDO/DERECHO.

Sin sox:
- ❌ No se puede generar audio por canal específico
- ❌ Solo reproducirá en ambos canales a la vez

Con sox:
- ✅ Audio IZQUIERDO solo por canal L (remix 1 0)
- ✅ Audio DERECHO solo por canal R (remix 0 1)

### **2. Sobre alsa-utils:**

Incluye los comandos esenciales:
- `aplay` - Reproducir audio
- `arecord` - Grabar micrófono
- `amixer` - Control de volumen
- `alsactl` - Configuración ALSA

### **3. Sobre smartmontools:**

Necesario para test SMART de discos. Sin él:
- Los tests de disco mostrarán "SKIP"
- No es crítico pero recomendado

### **4. Sobre Python:**

Lubuntu normalmente ya tiene Python 3 instalado. La librería `curses` es parte de la biblioteca estándar de Python, NO necesita:
- ❌ `pip install curses`
- ❌ `apt install python3-curses`

Ya está incluida en Python 3.

---

## 🎯 PREPARAR EL PENDRIVE LUBUNTU

### **Pasos recomendados:**

1. **Instalar Lubuntu en el pendrive** (con persistencia)
2. **Copiar el script:**
   ```bash
   # Copiar main.py y archivos relacionados
   sudo cp main.py /app/
   sudo cp *.sh /app/
   ```

3. **Ejecutar instalación:**
   ```bash
   sudo bash /app/install_dependencies.sh
   ```

4. **Crear acceso directo en escritorio:**
   ```bash
   cat > ~/Desktop/NovaCheck.desktop <<EOF
   [Desktop Entry]
   Type=Application
   Name=NovaCheck
   Exec=sudo python3 /app/main.py
   Terminal=true
   Icon=utilities-system-monitor
   EOF
   
   chmod +x ~/Desktop/NovaCheck.desktop
   ```

5. **Configurar sudo sin contraseña** (opcional, para el pendrive):
   ```bash
   sudo visudo
   # Añadir al final:
   # novacheck ALL=(ALL) NOPASSWD: /usr/bin/python3 /app/main.py
   ```

---

## 🐛 SOLUCIÓN DE PROBLEMAS

### **Audio no funciona:**

```bash
# 1. Verificar instalación
which sox
which aplay

# 2. Ver dispositivos
aplay -l

# 3. Probar manualmente
sox -n /tmp/test.wav synth 1 sine 800
aplay /tmp/test.wav

# 4. Si no suena, probar otros dispositivos
aplay -D plughw:0,0 /tmp/test.wav
aplay -D plughw:0,3 /tmp/test.wav
aplay -D plughw:1,0 /tmp/test.wav
```

### **Tests de disco fallan:**

```bash
# Verificar smartctl
which smartctl
sudo smartctl -H /dev/sda
```

### **Test USB no detecta:**

```bash
# Verificar lsusb
which lsusb
lsusb
```

---

## 📋 CHECKLIST DE INSTALACIÓN

Usa esto para verificar que todo está listo:

```
□ Lubuntu instalado en pendrive
□ Script copiado a /app/main.py
□ Ejecutado: sudo bash /app/install_dependencies.sh
□ Verificado: which sox (muestra /usr/bin/sox)
□ Verificado: which aplay (muestra /usr/bin/aplay)
□ Verificado: aplay -l (muestra dispositivos)
□ Probado: sox + aplay funcionan
□ Verificado: which smartctl (muestra /usr/bin/smartctl)
□ Verificado: python3 --version (muestra Python 3.x)
□ Ejecutado: sudo python3 /app/main.py (funciona)
□ Probado: Audio L/R funcionan
□ Probado: Micrófono funciona
□ Probado: Test de teclado funciona
```

---

## ✅ RESUMEN RÁPIDO

**Para instalar TODO en un comando:**

```bash
sudo bash /app/install_dependencies.sh
```

**Para ejecutar NovaCheck:**

```bash
sudo python3 /app/main.py
```

**Dependencias CRÍTICAS (sin estas NO funciona):**
- ✅ sox
- ✅ alsa-utils
- ✅ python3

**Dependencias RECOMENDADAS (para tests completos):**
- ✅ smartmontools
- ✅ usbutils
- ✅ dmidecode

---

**Con esto tu pendrive Lubuntu estará completamente listo para usar NovaCheck en producción.**
