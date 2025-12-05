# SOLUCIÓN: PYNPUT NO ENCONTRADO

## 🔴 PROBLEMA

El script muestra el error:
```
ERROR: pynput no instalado
```

A pesar de que pynput está instalado en `/home/novacheck/venv`.

---

## ✅ CAUSA

El script se ejecuta con el Python del **sistema**, no con el Python del **virtualenv**.

Por eso no encuentra pynput aunque esté instalado en el venv.

---

## 🔧 SOLUCIONES

### **Solución 1: Usar el script de ejecución (RECOMENDADO)**

He creado un script que activa el virtualenv automáticamente:

```bash
sudo bash /app/run_novacheck.sh
```

**Este script:**
1. ✅ Busca el virtualenv en `/home/novacheck/venv`
2. ✅ Lo activa automáticamente
3. ✅ Verifica que pynput esté instalado
4. ✅ Si falta, lo instala
5. ✅ Ejecuta NovaCheck con el Python del venv

---

### **Solución 2: Activar virtualenv manualmente**

```bash
# Activar virtualenv
source /home/novacheck/venv/bin/activate

# Verificar que pynput está disponible
python3 -c "import pynput"

# Si da error, instalar:
pip3 install pynput

# Ejecutar NovaCheck
sudo python3 /app/main.py
```

---

### **Solución 3: Reinstalar con el script de instalación**

El script de instalación ahora configura el virtualenv correctamente:

```bash
sudo bash /app/install_dependencies.sh
```

**Luego ejecutar con:**
```bash
sudo bash /app/run_novacheck.sh
```

---

### **Solución 4: Instalar pynput globalmente (no recomendado)**

Si prefieres no usar virtualenv:

```bash
sudo pip3 install pynput
```

**Desventaja:** Instala en el sistema global, puede causar conflictos.

---

## 📋 VERIFICACIÓN

### **Verificar que el venv existe:**
```bash
ls -la /home/novacheck/venv
```

Debería mostrar:
```
bin/
lib/
include/
...
```

### **Verificar que pynput está en el venv:**
```bash
source /home/novacheck/venv/bin/activate
pip3 list | grep pynput
```

Debería mostrar:
```
pynput    1.7.6
```

### **Verificar que el script puede importar pynput:**
```bash
source /home/novacheck/venv/bin/activate
python3 -c "import pynput; print('✓ pynput OK')"
```

---

## 🆕 CAMBIOS REALIZADOS

### **1. Script de ejecución: `/app/run_novacheck.sh`**

Script nuevo que:
- Busca el virtualenv
- Lo activa automáticamente
- Verifica dependencias
- Ejecuta NovaCheck

**Uso:**
```bash
sudo bash /app/run_novacheck.sh
```

### **2. Modificación en `/app/main.py`**

Agregado al inicio del script:
```python
# Agregar virtualenv al path si existe
venv_paths = [
    '/home/novacheck/venv/lib/python3.9/site-packages',
    '/home/novacheck/venv/lib/python3.10/site-packages',
    '/home/novacheck/venv/lib/python3.11/site-packages',
    '/home/novacheck/venv/lib/python3.12/site-packages',
]

for venv_path in venv_paths:
    if os.path.exists(venv_path) and venv_path not in sys.path:
        sys.path.insert(0, venv_path)
```

**Esto permite que el script encuentre pynput en el venv automáticamente.**

### **3. Script de instalación actualizado**

Ahora el script de instalación:
- Crea el virtualenv si no existe
- Instala pynput en el venv
- Configura todo correctamente

---

## 🎯 USO RECOMENDADO

### **Primera vez (instalación):**
```bash
# 1. Instalar dependencias
sudo bash /app/install_dependencies.sh

# 2. Ejecutar NovaCheck
sudo bash /app/run_novacheck.sh
```

### **Usos posteriores:**
```bash
# Simplemente ejecutar:
sudo bash /app/run_novacheck.sh
```

---

## 🐛 TROUBLESHOOTING

### **Problema: "pynput no instalado" persiste**

**Verificar:**
```bash
# 1. Ver versión de Python
python3 --version

# 2. Verificar si el venv existe
ls /home/novacheck/venv

# 3. Ver paquetes en venv
source /home/novacheck/venv/bin/activate
pip3 list

# 4. Si pynput no está, instalar:
pip3 install pynput
deactivate
```

### **Problema: "virtualenv no existe"**

**Crear manualmente:**
```bash
# Crear virtualenv
python3 -m venv /home/novacheck/venv

# Activar
source /home/novacheck/venv/bin/activate

# Instalar dependencias
pip3 install pynput pygame numpy

# Desactivar
deactivate
```

### **Problema: "Permission denied" al crear venv**

**Crear como usuario correcto:**
```bash
# Si necesitas cambiar permisos
sudo mkdir -p /home/novacheck
sudo chown -R $USER:$USER /home/novacheck

# Crear venv
python3 -m venv /home/novacheck/venv
```

---

## 📝 NOTAS IMPORTANTES

### **Sobre virtualenv:**
- Es la forma recomendada de manejar dependencias en Python
- Aísla las librerías del proyecto del sistema
- Evita conflictos entre versiones

### **Sobre pynput:**
- Requiere Python 3.6+
- Funciona en Linux con X11 (Lubuntu tiene X11)
- Es necesario para la detección correcta del teclado

### **Sobre pygame:**
- También se instala en el venv
- Necesario para audio L/R
- Requiere numpy

---

## ✅ RESUMEN RÁPIDO

**Problema:** pynput no encontrado

**Solución rápida:**
```bash
sudo bash /app/run_novacheck.sh
```

**Si falla:**
```bash
# Reinstalar todo
sudo bash /app/install_dependencies.sh

# Ejecutar
sudo bash /app/run_novacheck.sh
```

**Verificar instalación:**
```bash
source /home/novacheck/venv/bin/activate
python3 -c "import pynput; print('OK')"
```

---

**Con estos cambios, NovaCheck debería encontrar pynput automáticamente.**
