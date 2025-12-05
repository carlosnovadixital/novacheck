# NOVACHECK - SISTEMA DE NAVEGACIÓN

## 🎮 NAVEGACIÓN ENTRE PRUEBAS

He implementado un sistema completo de navegación que permite:
- ✅ Avanzar a la siguiente prueba
- ✅ Volver atrás a la prueba anterior
- ✅ Repetir la prueba actual
- ✅ Salir en cualquier momento

---

## 🔑 TECLAS DE NAVEGACIÓN

| Tecla | Acción | Descripción |
|-------|--------|-------------|
| **[SPACE]** o **[ENTER]** | Siguiente | Avanza a la próxima prueba |
| **[B]** | Atrás (Back) | Vuelve a la prueba anterior |
| **[R]** | Repetir (Repeat) | Repite la prueba actual |
| **[Q]** | Salir (Quit) | Sale del programa |

**Ayuda visible:** En la parte inferior de la pantalla siempre se muestra:
```
[SPACE/ENTER]=Siguiente | [B]=Atrás | [R]=Repetir | [Q]=Salir
```

---

## 📋 SECUENCIA DE PRUEBAS

El sistema ejecuta las pruebas en este orden:

```
1. WiFi (automático)
2. Técnico (input del nombre)
3. Hardware (información, auto 3s)
4. Auto-Tests (batería, touchpad, USB, SMART)
5. Audio (LEFT, RIGHT, Micrófono)
6. Visual (colores)
7. Teclado (pynput)
8. Wipe (opcional, con confirmación)
9. Informe Final
```

---

## 🎯 CÓMO FUNCIONA

### **Después de cada prueba:**

```
┌────────────────────────────────────┐
│  PRUEBA COMPLETADA                 │
│                                    │
│  [SPACE/ENTER] = Siguiente prueba  │
│  [B] = Volver atrás               │
│  [R] = Repetir esta prueba        │
│  [Q] = Salir                      │
└────────────────────────────────────┘
```

### **Opciones disponibles:**

#### 1. **[SPACE / ENTER] - Siguiente**
- Avanza a la próxima prueba en la secuencia
- Guarda el resultado de la prueba actual
- Más usado: flujo normal hacia adelante

#### 2. **[B] - Atrás**
- Vuelve a la prueba anterior
- Útil si quieres revisar o cambiar algo
- Puedes volver múltiples pasos

**Ejemplo:**
```
Audio → [B] → Auto-Tests → [B] → Hardware
```

#### 3. **[R] - Repetir**
- Ejecuta de nuevo la prueba actual
- Útil si:
  - No estás seguro del resultado
  - Quieres verificar algo de nuevo
  - Hubo un error temporal

**Ejemplo:**
```
Audio (falló) → [R] → Audio (repite) → [SPACE] → Visual
```

#### 4. **[Q] - Salir**
- Sale del programa en cualquier momento
- **ATENCIÓN:** No guarda resultados si sales antes del final

---

## 💡 CASOS DE USO

### **Caso 1: Flujo normal (sin problemas)**
```
WiFi → Técnico → Hardware → Auto → Audio → Visual → Teclado → Wipe → Final
      [SPACE] [SPACE]  [SPACE] [SPACE] [SPACE]  [SPACE]  [SPACE] [SPACE]
```

### **Caso 2: Audio falló, repetir**
```
Audio (falló) → [R] → Audio (repite) → Audio (OK) → [SPACE] → Visual
```

### **Caso 3: Revisar prueba anterior**
```
Visual → [B] → Audio (repasa) → [SPACE] → Visual (continúa)
```

### **Caso 4: Saltar Wipe**
```
Teclado → [SPACE] → Wipe (confirmación) → [N] → Final (sin wipe)
```

### **Caso 5: Volver atrás 2 pruebas**
```
Teclado → [B] → Visual → [B] → Audio (revisa) → [SPACE] → Visual → [SPACE] → Teclado
```

---

## 🔄 PERSISTENCIA DE RESULTADOS

**Los resultados se guardan automáticamente:**

```python
results = {
    'auto': {...},     # Tests automáticos
    'audio': 'OK',     # Estado del audio
    'visual': 'OK',    # Estado visual
    'keyboard': 'OK',  # Estado teclado
    'wipe': 'OK'       # Estado wipe
}
```

**Si repites una prueba:**
- ✅ El nuevo resultado sobrescribe el anterior
- ✅ Al finalizar, se usa el resultado más reciente

**Si vuelves atrás:**
- ✅ Los resultados anteriores se mantienen
- ✅ Puedes revisarlos sin perderlos

---

## ⚠️ CONSIDERACIONES ESPECIALES

### **Pruebas que NO muestran navegación:**
Algunas pruebas avanzan automáticamente:
- **WiFi**: Conexión automática
- **Técnico**: Después de escribir nombre
- **Hardware**: Auto-avanza después de 3s

**Razón:** Son pruebas informativas o de setup inicial.

### **Prueba de Wipe:**
Tiene navegación especial:

```
┌────────────────────────────────────┐
│  ¿Deseas ejecutar WIPE?            │
│                                    │
│  [SPACE/ENTER] = Ejecutar WIPE    │
│  [B] = Volver atrás (saltar)      │
│  [N] = Saltar y continuar         │
└────────────────────────────────────┘
```

**Opciones:**
- **[SPACE/ENTER]**: Ejecuta el borrado de disco
- **[B]**: Vuelve a la prueba de teclado
- **[N]**: Marca como "SKIP" y continúa al informe

**IMPORTANTE:** 
- ⚠️ WIPE borra permanentemente el disco
- ⚠️ Usa [B] o [N] si no quieres borrar

---

## 🎯 VENTAJAS DEL SISTEMA

### **1. Flexibilidad**
- No estás atrapado en una secuencia lineal
- Puedes revisar cualquier prueba anterior
- Repite las que necesites

### **2. Verificación**
- Resultado dudoso → [R] para repetir
- Quieres confirmar → [B] para revisar

### **3. Corrección**
- Te saltaste algo → [B] para volver
- Error temporal → [R] para reintentar

### **4. Control**
- No quieres Wipe → [N] para saltar
- Problema serio → [Q] para salir

### **5. Seguridad**
- Confirmación antes de acciones destructivas (Wipe)
- Siempre puedes volver atrás

---

## 🐛 MANEJO DE ERRORES

Si una prueba falla con error:

```
┌────────────────────────────────────┐
│  Error en Audio: [mensaje]         │
│                                    │
│  [SPACE/ENTER] = Continuar         │
│  [B] = Volver atrás               │
│  [R] = Repetir                    │
└────────────────────────────────────┘
```

**Opciones:**
- **[R]**: Intentar de nuevo (recomendado)
- **[B]**: Volver y revisar prueba anterior
- **[SPACE]**: Continuar a pesar del error

---

## 📊 EJEMPLOS PRÁCTICOS

### **Ejemplo 1: Audio no se escuchó bien**
```
1. Audio ejecuta prueba LEFT y RIGHT
2. No estás seguro si funcionó
3. Presionas [R]
4. Audio se ejecuta de nuevo
5. Ahora sí lo escuchas claramente
6. Presionas [SPACE] para continuar
```

### **Ejemplo 2: Olvidaste revisar algo en Hardware**
```
1. Estás en prueba de Audio
2. Recuerdas que no anotaste el serial
3. Presionas [B] → vuelves a Auto-Tests
4. Presionas [B] → vuelves a Hardware
5. Anotas el serial
6. Presionas [SPACE] → Auto-Tests
7. Presionas [SPACE] → Audio
8. Continúas normalmente
```

### **Ejemplo 3: No quieres hacer Wipe**
```
1. Llegas a pantalla de Wipe
2. Ves: "¿Deseas ejecutar WIPE?"
3. Presionas [N] para saltar
4. Continúa al Informe Final
5. Wipe marcado como "SKIP"
```

### **Ejemplo 4: Teclado no detectó todas las teclas**
```
1. Teclado finaliza con 28 teclas (mínimo 35)
2. Resultado: "FAIL"
3. Presionas [R] para repetir
4. Esta vez pulsas más teclas
5. Ahora 37 teclas → "PASS"
6. Presionas [SPACE] para continuar
```

---

## 🔄 DIAGRAMA DE FLUJO

```
              ┌─────────┐
              │  WiFi   │
              └────┬────┘
                   │
              ┌────▼────┐
              │ Técnico │
              └────┬────┘
                   │
              ┌────▼────┐
              │Hardware │
              └────┬────┘
                   │
         ┌─────────▼─────────┐
         │                   │
    ┌────▼────┐         [B] Atrás
    │  Auto   │              │
    │  Tests  │◄─────────────┘
    └────┬────┘
         │
         │  [SPACE] Siguiente
         │  [R] Repetir ──┐
         │                │
    ┌────▼────┐          │
    │  Audio  │◄─────────┘
    └────┬────┘
         │
    ┌────▼────┐
    │ Visual  │
    └────┬────┘
         │
    ┌────▼────┐
    │ Teclado │
    └────┬────┘
         │
    ┌────▼────┐
    │  Wipe   │ [N] Saltar
    │(opcional)│
    └────┬────┘
         │
    ┌────▼────┐
    │  Final  │
    └─────────┘
```

---

## 🎓 TIPS DE USO

### **Para técnicos rápidos:**
- Simplemente presiona [SPACE] en cada prueba
- Flujo lineal sin interrupciones

### **Para técnicos cuidadosos:**
- Usa [R] si tienes dudas
- Usa [B] para revisar resultados anteriores

### **Para testing/desarrollo:**
- Usa [B] para probar mejoras en pruebas anteriores
- Usa [R] para verificar fixes múltiples veces

### **Para evitar errores:**
- Lee bien antes de presionar [SPACE] en Wipe
- Usa [N] si no quieres borrar el disco

---

## ✅ RESUMEN RÁPIDO

**Teclas principales:**
- `[SPACE]` / `[ENTER]` → Siguiente
- `[B]` → Atrás
- `[R]` → Repetir
- `[Q]` → Salir

**Flujo típico:**
```
Prueba → [SPACE] → Siguiente Prueba → [SPACE] → ... → Final
```

**Si tienes dudas:**
```
Prueba → [R] → Prueba (repite) → [SPACE] → Siguiente
```

**Si te equivocaste:**
```
Prueba Actual → [B] → Prueba Anterior → [SPACE] → Prueba Actual
```

---

**El sistema de navegación hace que NovaCheck sea más flexible, seguro y fácil de usar.**
