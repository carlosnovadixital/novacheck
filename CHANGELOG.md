# NOVACHECK PRO - Changelog de Mejoras

## Versión Mejorada - Diciembre 2024

### 🎯 Problemas Resueltos

#### 1. ✅ Audio - Texto en Diagonal CORREGIDO
**Problema:** El texto en la prueba de audio se mostraba en diagonal y daba errores.

**Solución:**
- Reescrita completamente la función `screen_audio_adv()`
- Se añaden llamadas `stdscr.clear()` antes de cada mensaje nuevo
- Se añaden llamadas `stdscr.refresh()` después de cada actualización
- Se añaden pausas `time.sleep()` para mejor visualización
- Pantallas separadas para altavoces y micrófono con mejor formato

**Cambios en el código:**
```python
# Antes: Mensajes se sobreescribían sin limpiar
center(stdscr, 6, "🔊 Sonando...")
center(stdscr, 8, "¿Se oyó algo?")

# Ahora: Pantalla limpia para cada mensaje
stdscr.clear()
draw_header(stdscr, "AUDIO CHECK")
center(stdscr, 6, "==================")
center(stdscr, 7, "  🔊 ALTAVOCES  ")
center(stdscr, 8, "==================")
stdscr.refresh()
```

---

#### 2. ✅ Teclado - Caracteres Especiales CORREGIDO
**Problema:** No se podían marcar teclas españolas como ñ, ç, ´, etc.

**Solución:**
- Mejorada la función `map_key()` con mapeo explícito de caracteres españoles
- Añadidos códigos ASCII específicos para cada tecla especial

**Caracteres especiales soportados:**
- ✓ ñ / Ñ (código 241 / 209)
- ✓ ç / Ç (código 231 / 199)
- ✓ ´ (acento agudo - código 180)
- ✓ ` (acento grave - código 96)
- ✓ ¡ (código 161)
- ✓ ¿ (código 191)
- ✓ º (código 186)
- ✓ ª (código 170)
- ✓ Símbolos: +, -, ', ,, .

**Cambios en el código:**
```python
def map_key(k):
    # Antes: Solo chr(k).upper()
    
    # Ahora: Mapeo explícito de caracteres especiales
    if k==241: return "Ñ"  # ñ
    if k==231: return "Ç"  # ç
    if k==180: return "´"  # acento agudo
    # ... y más
```

---

#### 3. ✅ Fuente Pequeña CORREGIDO
**Problema:** El texto era muy pequeño y difícil de leer.

**Soluciones aplicadas:**

##### a) Encabezados más grandes (3 líneas en lugar de 1):
```python
def draw_header(stdscr, sub=""):
    # Línea superior decorativa
    stdscr.addstr(0, 0, "=" * (w-1))
    # Título principal
    stdscr.addstr(1, 0, f"  {APP_TITLE}  |  {sub}  ")
    # Línea inferior decorativa
    stdscr.addstr(2, 0, "=" * (w-1))
```

##### b) Mayor espaciado vertical en todas las pantallas:
- Cambio de `r+=1` a `r+=2` entre elementos
- Líneas en blanco adicionales para separación
- Uso de separadores decorativos (═══, ╔╗╚╝)

##### c) Mejoras visuales en cada pantalla:

**screen_hw_info:**
- Separadores decorativos grandes
- Espaciado doble entre elementos
- Formato con viñetas (•)

**screen_keyboard_vis:**
- Teclas mostradas como `[ TECLA ]` en lugar de simple texto
- Espaciado triple entre filas (i*3 en lugar de i*2)
- Instrucciones grandes y claras
- Contador de teclas presionadas

**screen_visual:**
- Pantallas de colores con texto grande centrado
- Bordes decorativos
- Instrucciones más claras

**screen_audio_adv:**
- Títulos con marcos decorativos
- Mensajes grandes y centrados
- Pausas entre transiciones

**screen_auto:**
- Formato de lista con viñetas
- Separadores de sección
- Resultados destacados

**screen_usb_interactive:**
- Marco decorativo grande
- Contador de tiempo regresivo
- Mensajes de estado claros

##### d) Nuevo color para destacar:
```python
curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLUE)
```
Usado para títulos y elementos importantes.

---

### 📁 Archivos Modificados

1. **`/app/main.py`** - Archivo principal con todas las correcciones
2. **`/app/test_keyboard.py`** - Script de prueba para verificar mapeo de teclas
3. **`/app/CHANGELOG.md`** - Este archivo de documentación

---

### 🧪 Pruebas Realizadas

1. ✅ Compilación de sintaxis Python: **OK**
2. ✅ Test de mapeo de teclas especiales: **OK** (16/16 caracteres)
3. ✅ Verificación de funciones: **OK**

---

### 📝 Notas de Uso

#### Para ejecutar el programa:
```bash
sudo python3 /app/main.py
```

#### Para probar el mapeo de teclado:
```bash
python3 /app/test_keyboard.py
```

#### Requisitos:
- Python 3.x
- Permisos de root (sudo)
- Librería curses (incluida en Python estándar)

---

### 🔧 Detalles Técnicos

**Mejoras de UI:**
- Header: 1 línea → 3 líneas con decoración
- Espaciado vertical: Simple → Doble/Triple
- Tamaño de teclas: Simple → [ FORMATO ]
- Colores: 5 pares → 6 pares (añadido amarillo)

**Mejoras de funcionalidad:**
- Detección de caracteres: Básica → Completa con español
- Limpieza de pantalla: Inconsistente → Sistemática
- Feedback visual: Mínimo → Completo con estados

---

### ✨ Resultado Final

Todos los problemas reportados han sido solucionados:
- ✅ Audio sin texto diagonal
- ✅ Detección completa de teclas especiales españolas (ñ, ç, ´, etc.)
- ✅ Interfaz más grande y legible

La herramienta está lista para usar en el pendrive Lubuntu.
