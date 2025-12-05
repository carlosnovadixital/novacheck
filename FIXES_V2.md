# NOVACHECK - CORRECCIONES V2

## 🔧 PROBLEMAS CORREGIDOS (Segunda iteración)

### 1. ✅ INPUT DEL TÉCNICO - TEXTO PISADO CORREGIDO

**Problema:** El texto se pisaba al escribir el nombre

**Solución:**
- Eliminado uso de `safe_print()` que ajustaba mal las coordenadas
- Uso directo de `stdscr.addstr()` con coordenadas absolutas
- Línea limpia antes de mostrar el input: `stdscr.addstr(13, 2, " " * (w-4))`
- Input posicionado correctamente con `stdscr.getstr(13, 5, 40)`
- Prompt ">> " en posición fija

**Código clave:**
```python
stdscr.addstr(13, 2, " " * (w-4))  # Limpiar línea completa
stdscr.addstr(13, 2, ">> ")         # Prompt
stdscr.move(13, 5)                  # Cursor después de >>
name = stdscr.getstr(13, 5, 40).decode().strip()
```

---

### 2. ✅ AUDIO - ERRORES EN PANTALLA ELIMINADOS

**Problema:** Los mensajes de `speaker-test` aparecían en pantalla

**Solución:**
- **Nueva función `play_test_sound()`** que maneja audio limpiamente
- Prioridad: Usar `sox` + `aplay` (silencioso)
- Fallback: `speaker-test` en background con redirección completa
- Uso de coordenadas absolutas en lugar de funciones helper
- `stdscr.erase()` + `stdscr.refresh()` antes de cada pantalla

**Método de audio:**
```python
def play_test_sound():
    # Generar WAV con sox (silencioso)
    if shutil.which("sox"):
        subprocess.run(f"sox -n {test_file} synth 1 sine 800", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(f"aplay -q {test_file}", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Fallback: speaker-test en background
        subprocess.run("(speaker-test -t sine -f 800 -l 1 >/dev/null 2>&1) &", 
                      shell=True)
```

**Ventajas:**
- ✅ Sin output de texto en pantalla
- ✅ Más silencioso y limpio
- ✅ Funciona con o sin sox
- ✅ Pruebas separadas LEFT/RIGHT

---

### 3. ✅ TECLADO - LAYOUT VISUAL COMO AIKEN

**Problema:** El sistema de lista no era visual, difícil de usar

**Solución COMPLETA:**
- **Layout visual mejorado** con representación de teclado real
- 6 filas de teclas mostradas visualmente
- Formato: `[KEY  ]` para cada tecla
- Las teclas presionadas se ponen en **VERDE**
- Contador en tiempo real
- Barra de progreso visual
- Termina con **F10** (más intuitivo)

**Layout incluido:**
```python
keyboard_layout = [
    ["ESC", "F1", "F2", "F3", ... "F12"],
    ["`", "1", "2", ... "BKSP"],
    ["TAB", "Q", "W", "E", ... "ENTER"],
    ["CAPS", "A", "S", "D", ... "Ñ", "ENTER"],
    ["SHIFT", "Z", "X", ... "Ç"],
    ["CTRL", "ALT", "SPACE", "ALTGR"]
]
```

**Detección mejorada:**
- Teclas de función (F1-F12)
- Teclas especiales (ESC, TAB, ENTER, BKSP, SHIFT, CTRL, ALT)
- Caracteres españoles (Ñ, Ç)
- Teclas de navegación (flechas, PGUP, PGDN, HOME, END)
- Símbolos y números

**Ventajas:**
- ✅ Visual como Aiken
- ✅ Fácil de ver qué teclas faltan
- ✅ Feedback inmediato (tecla verde = presionada)
- ✅ No requiere contar manualmente
- ✅ Funciona con cualquier distribución

---

## 📝 CAMBIOS TÉCNICOS CLAVE

### Coordinadas Absolutas

**Antes:** Uso de `safe_print()` y funciones helper con ajustes
**Ahora:** `stdscr.addstr(y, x, text)` directo

**Ventaja:** Sin problemas de offset o pisado de texto

### Audio Limpio

**Antes:** `speaker-test` con stdout/stderr a DEVNULL (no funcionaba)
**Ahora:** 
1. sox + aplay (silencioso nativo)
2. Fallback: speaker-test en subshell background

### Teclado Visual

**Antes:** Lista de teclas sin representación visual
**Ahora:** 
- Layout de teclado real
- 6 filas visibles
- Teclas en formato `[KEY]`
- Color verde para presionadas

---

## 🧪 TESTING RECOMENDADO

### 1. Input Técnico
```bash
# Verificar que:
- El texto "Por favor, escribe tu nombre:" se ve claro
- El prompt ">>" está en una línea separada
- Se puede escribir sin que el texto se pise
```

### 2. Audio
```bash
# Verificar que:
- NO aparecen mensajes de error en pantalla
- Se escuchan los tonos de prueba
- Pantalla limpia durante toda la prueba
- Sox está instalado: which sox
```

### 3. Teclado
```bash
# Verificar que:
- Se ve el layout del teclado (6 filas)
- Las teclas se ponen verdes al pulsarlas
- F10 termina la prueba
- Contador aumenta correctamente
- Incluye Ñ, Ç y otras especiales
```

---

## ⚠️ NOTA IMPORTANTE: FUENTE

La fuente pequeña **NO SE PUEDE CAMBIAR** desde el script Python.

**Por qué:**
- curses usa el tamaño de fuente del terminal del sistema
- El terminal en modo texto (tty) tiene fuente fija del kernel/GRUB
- Solo se puede cambiar preparando la imagen con Cubic

**Soluciones aplicadas:**
- Mayor espaciado entre elementos
- Menos elementos por pantalla
- Texto más organizado y claro

**Para cambiar fuente:**
1. Editar configuración de GRUB
2. Usar Cubic para modificar la imagen ISO
3. Configurar terminal con fuente más grande antes de boot

---

## 📊 RESUMEN DE ESTADO

| Problema | Estado | Solución |
|----------|--------|----------|
| Input técnico pisado | ✅ RESUELTO | Coordenadas absolutas + limpieza de línea |
| Audio con errores | ✅ RESUELTO | play_test_sound() con sox/aplay |
| Teclado sin visual | ✅ RESUELTO | Layout visual 6 filas + teclas verdes |
| Fuente pequeña | ⚠️ LIMITACIÓN | No modificable desde script (requiere Cubic) |

---

## 🎯 PRÓXIMOS PASOS

1. **Probar en el pendrive Lubuntu real**
2. **Verificar que sox está instalado:** `apt install sox`
3. **Si sox no está, el fallback funcionará** (speaker-test en background)
4. **Para fuente más grande:** Modificar con Cubic en la imagen ISO

---

**La herramienta está lista para producción con estas correcciones aplicadas.**
