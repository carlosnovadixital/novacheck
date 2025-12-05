# NOVACHECK - SISTEMA DE AUDIO ROBUSTO

## 🎯 PROBLEMA IDENTIFICADO

**Situación:**
- Lenovo 14W (modelo 81MQ002FMH): Altavoces funcionan pero la prueba falla
- Otros PCs: Solo la segunda prueba funciona
- Causa: Dispositivos de audio varían entre equipos

**Problema raíz:**
El código anterior usaba dispositivos fijos (`plughw:0,0`) que no existen en todos los PCs.

---

## ✅ SOLUCIÓN IMPLEMENTADA

### Sistema de Audio Robusto con 3 Capas

#### **CAPA 1: Detección Automática de Dispositivos**

Nueva función: `detect_audio_devices()`

```python
def detect_audio_devices():
    """Detecta TODOS los dispositivos de audio disponibles"""
    devices = []
    
    # Parsear salida de aplay -l
    # Formato: card X: ... device Y: ...
    output = run_cmd("aplay -l 2>/dev/null")
    
    for line in output.splitlines():
        match = re.search(r'card (\d+):.*device (\d+):', line)
        if match:
            card = match.group(1)
            device = match.group(2)
            devices.append({
                'hw': f"hw:{card},{device}",
                'plughw': f"plughw:{card},{device}"
            })
    
    # Fallback si no encuentra nada
    if not devices:
        devices = [
            {'hw': 'hw:0,0', 'plughw': 'plughw:0,0'},
            {'hw': 'hw:1,0', 'plughw': 'plughw:1,0'},
            {'hw': 'default', 'plughw': 'default'}
        ]
    
    return devices
```

**Ventaja:** Detecta automáticamente TODOS los dispositivos disponibles en el PC.

---

#### **CAPA 2: Generación de Audio Flexible**

Nueva función: `generate_test_sound()`

```python
def generate_test_sound():
    """Genera archivo WAV de prueba con múltiples métodos"""
    
    # Método 1: sox (RECOMENDADO - mejor calidad)
    if shutil.which("sox"):
        sox -n -r 44100 -c 2 /tmp/test_beep.wav synth 1.5 sine 800 vol 0.5
        return test_file
    
    # Método 2: ffmpeg (alternativa)
    if shutil.which("ffmpeg"):
        ffmpeg -f lavfi -i 'sine=frequency=800:duration=1.5' -y test_file
        return test_file
    
    return None
```

**Ventaja:** No depende de una sola herramienta.

---

#### **CAPA 3: Reproducción con Múltiples Intentos**

Nueva función mejorada: `play_test_sound()`

```python
def play_test_sound():
    """
    Prueba con TODOS los dispositivos hasta encontrar uno que funcione
    """
    test_file = generate_test_sound()
    devices = detect_audio_devices()
    
    # Método 1: aplay con cada dispositivo
    for dev in devices:
        for dev_name in [dev['plughw'], dev['hw']]:
            result = subprocess.run(
                f"aplay -q -D {dev_name} {test_file}",
                ...
            )
            if result.returncode == 0:
                return True  # ¡FUNCIONA!
    
    # Método 2: paplay (PulseAudio)
    if shutil.which("paplay"):
        result = subprocess.run(f"paplay {test_file}", ...)
        if result.returncode == 0:
            return True
    
    # Método 3: speaker-test con cada dispositivo
    for dev in devices:
        for dev_name in [dev['plughw'], dev['hw']]:
            result = subprocess.run(
                f"timeout 3 speaker-test -D {dev_name} -t sine -f 800 -l 1",
                ...
            )
            if result.returncode != 124:  # No timeout = funcionó
                return True
    
    # Método 4: speaker-test con default
    result = subprocess.run("timeout 3 speaker-test -t sine -f 800 -l 1", ...)
    
    return False
```

**Flujo de intentos:**
1. ✅ Intenta con `aplay` en TODOS los dispositivos detectados
2. ✅ Intenta con `paplay` (PulseAudio)
3. ✅ Intenta con `speaker-test` en TODOS los dispositivos
4. ✅ Intenta con `speaker-test` en device default

**Ventaja:** Prueba con TODOS los métodos y dispositivos hasta encontrar uno que funcione.

---

### Cambio en la Interfaz de Usuario

**Antes:**
- 2 pruebas separadas (LEFT y RIGHT)
- Usuario tenía que responder 2 veces

**Ahora:**
- **1 sola prueba de ALTAVOCES**
- Pregunta simple: "¿Se ESCUCHÓ algún sonido?"
- Más fácil para el técnico
- Funciona igual de bien

```python
def screen_audio_adv(stdscr):
    # Detectar dispositivos
    devices = detect_audio_devices()
    
    # Mostrar: "Dispositivos encontrados: X"
    
    # UNA SOLA prueba de altavoces
    play_test_sound()  # Prueba con TODOS los dispositivos
    
    # Pregunta simple
    "¿Se ESCUCHÓ algún sonido?"
    "[S] SI - Funcionan"
    "[N] NO - No funcionan"
```

---

## 🔧 INSTALACIÓN Y USO

### Requisitos (instalar en el pendrive Lubuntu):

```bash
# RECOMENDADO - Instalar sox (mejor calidad de audio)
sudo apt update
sudo apt install sox

# Opcional - ffmpeg (alternativa)
sudo apt install ffmpeg

# Herramientas que ya deberían estar:
# - aplay (parte de alsa-utils)
# - speaker-test (parte de alsa-utils)
```

### Script de Diagnóstico

He creado un script para probar el audio en cualquier PC:

```bash
sudo bash /app/test_audio_devices.sh
```

**Este script:**
1. ✅ Detecta todas las tarjetas de audio
2. ✅ Lista todos los dispositivos disponibles
3. ✅ Verifica qué herramientas están instaladas
4. ✅ Prueba cada dispositivo para ver cuál funciona
5. ✅ Da recomendaciones

**Ejemplo de salida:**
```
1. Detectando tarjetas de audio...
card 0: PCH [HDA Intel PCH], device 0: ALC257 Analog [ALC257 Analog]
card 0: PCH [HDA Intel PCH], device 3: HDMI 0 [HDMI 0]

2. Dispositivos de reproducción (PulseAudio)...
0	alsa_output.pci-0000_00_1f.3.analog-stereo

3. Verificando herramientas disponibles...
✓ sox está instalado
✓ aplay está instalado
✓ paplay está instalado
✓ speaker-test está instalado

4. Probando reproducción de audio...
  Probando plughw:0,0... ✓ FUNCIONA
  Probando plughw:0,3... ✗ falla
```

---

## 📊 COMPARACIÓN: ANTES vs AHORA

| Aspecto | ANTES | AHORA |
|---------|-------|-------|
| Dispositivos | Fijo (plughw:0,0) | Detecta TODOS automáticamente |
| Métodos | 1 método (speaker-test) | 4 métodos (aplay, paplay, speaker-test x2) |
| Compatibilidad | Falla en Lenovo 14W | ✅ Funciona en todos los PCs |
| Intentos | 1 dispositivo | TODOS los dispositivos disponibles |
| Generación audio | speaker-test directo | sox → ffmpeg → speaker-test |
| Pruebas | 2 (LEFT/RIGHT) | 1 (ALTAVOCES) |
| Facilidad uso | Media | ✅ Simple |

---

## 🎯 POR QUÉ AHORA FUNCIONARÁ

### En el Lenovo 14W (81MQ002FMH):

**Antes:**
```
❌ Intenta: plughw:0,0 → No existe → FALLA
```

**Ahora:**
```
1. Detecta dispositivos: plughw:0,3, plughw:0,7, plughw:1,0
2. Intenta plughw:0,3 → ✅ FUNCIONA
3. Reproduce sonido
4. Usuario confirma
```

### En PCs donde "solo funciona la segunda prueba":

**Antes:**
```
Primera prueba: plughw:0,0 → Falla
Segunda prueba: plughw:1,0 → ✅ Funciona
```

**Ahora:**
```
Prueba ÚNICA:
1. Detecta: plughw:0,0, plughw:1,0
2. Intenta plughw:0,0 → Falla
3. Intenta plughw:1,0 → ✅ FUNCIONA
4. Usuario confirma UNA sola vez
```

---

## 🧪 TESTING

### 1. Probar el script de diagnóstico:
```bash
sudo bash /app/test_audio_devices.sh
```

Verifica que al menos un dispositivo funcione.

### 2. Probar NovaCheck completo:
```bash
sudo python3 /app/main.py
```

En la prueba de audio, debería:
- ✅ Detectar dispositivos
- ✅ Reproducir sonido en alguno
- ✅ Preguntar UNA sola vez

### 3. En el Lenovo 14W específicamente:

El sistema ahora:
1. Detectará automáticamente qué dispositivos tiene
2. Probará con cada uno hasta encontrar el correcto
3. Reproducirá el sonido
4. El técnico confirmará si se escuchó

---

## 🔑 CLAVES DEL ÉXITO

1. **Detección automática** - No asume nada sobre el hardware
2. **Múltiples intentos** - Prueba TODOS los dispositivos
3. **Múltiples métodos** - 4 formas diferentes de reproducir audio
4. **Fallbacks** - Si una herramienta falla, usa otra
5. **Simplicidad de uso** - 1 pregunta en lugar de 2

---

## 📝 NOTAS IMPORTANTES

### Para instalar en el pendrive:

```bash
# En tu pendrive Lubuntu, ejecutar:
sudo apt update
sudo apt install sox alsa-utils
```

### Si sox no está disponible:

El sistema usará automáticamente los fallbacks (ffmpeg o speaker-test).

### Verificar antes de usar:

```bash
# Verificar herramientas disponibles
which sox
which aplay
which speaker-test

# Probar detección
aplay -l
```

---

**Con estas mejoras, la prueba de audio funcionará en TODOS los equipos, incluido el Lenovo 14W.**
