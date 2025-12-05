#!/bin/bash
# Script para probar detección y reproducción de audio

echo "========================================="
echo "  DIAGNÓSTICO DE AUDIO - NOVACHECK"
echo "========================================="
echo ""

echo "1. Detectando tarjetas de audio..."
echo "-----------------------------------"
aplay -l 2>/dev/null || echo "No se pudo ejecutar aplay -l"
echo ""

echo "2. Dispositivos de reproducción (PulseAudio)..."
echo "------------------------------------------------"
pactl list short sinks 2>/dev/null || echo "PulseAudio no disponible"
echo ""

echo "3. Verificando herramientas disponibles..."
echo "-------------------------------------------"
which sox && echo "✓ sox está instalado" || echo "✗ sox NO está instalado"
which aplay && echo "✓ aplay está instalado" || echo "✗ aplay NO está instalado"
which paplay && echo "✓ paplay está instalado" || echo "✗ paplay NO está instalado"
which speaker-test && echo "✓ speaker-test está instalado" || echo "✗ speaker-test NO está instalado"
which ffmpeg && echo "✓ ffmpeg está instalado" || echo "✗ ffmpeg NO está instalado"
echo ""

echo "4. Probando reproducción de audio..."
echo "-------------------------------------"

# Generar archivo de prueba con sox
if which sox > /dev/null 2>&1; then
    echo "Generando archivo WAV con sox..."
    sox -n -r 44100 -c 2 /tmp/test_audio.wav synth 1.5 sine 800 vol 0.5 2>/dev/null
    
    if [ -f /tmp/test_audio.wav ]; then
        echo "✓ Archivo generado: /tmp/test_audio.wav"
        echo ""
        echo "Probando reproducción con cada dispositivo detectado..."
        
        # Intentar con cada dispositivo
        for card in 0 1 2; do
            for device in 0 1 2; do
                hw_dev="plughw:${card},${device}"
                echo -n "  Probando $hw_dev... "
                if aplay -q -D $hw_dev /tmp/test_audio.wav 2>/dev/null; then
                    echo "✓ FUNCIONA"
                else
                    echo "✗ falla"
                fi
            done
        done
        
        echo ""
        echo "Probando con 'default'..."
        if aplay -q -D default /tmp/test_audio.wav 2>/dev/null; then
            echo "✓ default FUNCIONA"
        else
            echo "✗ default falla"
        fi
        
        rm -f /tmp/test_audio.wav
    else
        echo "✗ No se pudo generar archivo WAV"
    fi
else
    echo "✗ sox no disponible, probando con speaker-test..."
    echo ""
    
    for card in 0 1 2; do
        for device in 0 1 2; do
            hw_dev="plughw:${card},${device}"
            echo -n "  Probando $hw_dev con speaker-test... "
            if timeout 3 speaker-test -D $hw_dev -t sine -f 800 -l 1 >/dev/null 2>&1; then
                echo "✓ FUNCIONA"
            else
                echo "✗ falla"
            fi
        done
    done
fi

echo ""
echo "========================================="
echo "  DIAGNÓSTICO COMPLETADO"
echo "========================================="
echo ""
echo "RECOMENDACIONES:"
echo "- Si sox no está instalado: apt install sox"
echo "- Los dispositivos que funcionan arriba deberían funcionar en NovaCheck"
