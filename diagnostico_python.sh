#!/bin/bash
# Script de diagnóstico para identificar problemas de Python/pynput

echo "========================================="
echo "  DIAGNÓSTICO DE ENTORNO PYTHON"
echo "========================================="
echo ""

echo "1. IDENTIFICACIÓN DE PYTHON"
echo "-------------------------------------------"
echo "which python3:"
which python3
echo ""

echo "/usr/bin/python3 version:"
/usr/bin/python3 --version
echo ""

echo "python3 --version (usando PATH):"
python3 --version
echo ""

echo "2. VERIFICAR SHEBANG DEL SCRIPT"
echo "-------------------------------------------"
head -1 /app/main.py
echo ""

echo "3. PYTHONPATH del sistema Python"
echo "-------------------------------------------"
/usr/bin/python3 -c "import sys; print('\n'.join(sys.path))"
echo ""

echo "4. PYTHONPATH del python3 en PATH"
echo "-------------------------------------------"
python3 -c "import sys; print('\n'.join(sys.path))"
echo ""

echo "5. VERIFICAR PYNPUT EN SISTEMA"
echo "-------------------------------------------"
echo "Test con /usr/bin/python3:"
/usr/bin/python3 -c "import pynput; print('✓ pynput encontrado en sistema Python')" 2>&1 || echo "✗ pynput NO encontrado"
echo ""

echo "Test con python3 (PATH):"
python3 -c "import pynput; print('✓ pynput encontrado')" 2>&1 || echo "✗ pynput NO encontrado"
echo ""

echo "6. VERIFICAR SI HAY VENV ACTIVO"
echo "-------------------------------------------"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "⚠ VENV ACTIVO: $VIRTUAL_ENV"
else
    echo "✓ No hay venv activo"
fi
echo ""

echo "7. UBICACIONES DE PYNPUT"
echo "-------------------------------------------"
echo "Global (sistema):"
ls -la /usr/local/lib/python3.11/dist-packages/ | grep pynput || echo "No encontrado"
echo ""

echo "En venv (si existe):"
ls -la /root/.venv/lib/python3.11/site-packages/ 2>/dev/null | grep pynput || echo "No hay venv o no está ahí"
echo ""

echo "8. PRUEBA DE EJECUCIÓN DEL SCRIPT"
echo "-------------------------------------------"
echo "Ejecutando: /app/main.py --version (simulación)"
echo "Python que usaría el shebang actual:"
head -1 /app/main.py | sed 's/#!//'
echo ""

echo "========================================="
echo "RECOMENDACIÓN"
echo "========================================="
echo ""
echo "Si el script main.py usa #!/usr/bin/python3,"
echo "ese Python debe tener pynput instalado."
echo ""
echo "Para instalar en sistema:"
echo "  sudo /usr/bin/python3 -m pip install --break-system-packages pynput"
echo ""
echo "O para instalar en venv:"
echo "  /root/.venv/bin/pip install pynput"
echo ""
