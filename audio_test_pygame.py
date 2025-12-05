#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de audio usando pygame para control preciso de canales L/R
"""

import numpy as np
import pygame
import sys

def generate_tone(frequency=800, duration=1.5, sample_rate=44100):
    """Genera un tono sinusoidal"""
    t = np.linspace(0, duration, int(sample_rate * duration))
    tone = np.sin(2 * np.pi * frequency * t)
    # Normalizar a 16-bit
    tone = (tone * 32767).astype(np.int16)
    return tone

def create_stereo_audio(channel='both', frequency=800, duration=1.5):
    """
    Crea audio estéreo con paneo específico
    channel: 'left', 'right', 'both'
    """
    tone = generate_tone(frequency, duration)
    
    if channel == 'left':
        # Solo canal izquierdo (L=tone, R=silence)
        left = tone
        right = np.zeros_like(tone)
    elif channel == 'right':
        # Solo canal derecho (L=silence, R=tone)
        left = np.zeros_like(tone)
        right = tone
    else:
        # Ambos canales
        left = tone
        right = tone
    
    # Combinar en array estéreo (samples, 2)
    stereo = np.column_stack((left, right))
    return stereo

def play_audio_channel(channel='both'):
    """
    Reproduce audio en canal específico usando pygame
    channel: 'left', 'right', 'both'
    """
    try:
        # Inicializar pygame mixer
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # Generar audio estéreo
        stereo_audio = create_stereo_audio(channel, frequency=800, duration=1.5)
        
        # Crear objeto Sound desde array
        sound = pygame.sndarray.make_sound(stereo_audio)
        
        # Reproducir
        sound.play()
        
        # Esperar a que termine
        while pygame.mixer.get_busy():
            pygame.time.wait(100)
        
        pygame.mixer.quit()
        return True
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    print("Test de audio con pygame")
    print("=" * 40)
    
    # Test LEFT
    print("\n1. Reproduciendo en canal IZQUIERDO (LEFT)...")
    play_audio_channel('left')
    
    input("Presiona ENTER para continuar...")
    
    # Test RIGHT
    print("\n2. Reproduciendo en canal DERECHO (RIGHT)...")
    play_audio_channel('right')
    
    input("Presiona ENTER para continuar...")
    
    # Test BOTH
    print("\n3. Reproduciendo en AMBOS canales...")
    play_audio_channel('both')
    
    print("\n✓ Test completado")
