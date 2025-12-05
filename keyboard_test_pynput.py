#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de teclado usando pynput para detección correcta independiente del layout
"""

import sys
import time
from pynput import keyboard

# Layout del teclado español
KEYBOARD_LAYOUT = [
    ["ESC", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12"],
    ["º", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "'", "¡", "BKSP"],
    ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "`", "+", "ENTER"],
    ["CAPS", "A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ", "´", "Ç"],
    ["SHIFT", "<", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "-"],
    ["CTRL", "ALT", "SPACE", "ALTGR", "CTRL"]
]

class KeyboardTester:
    def __init__(self):
        self.pressed_keys = set()
        self.listener = None
        self.running = True
        
    def normalize_key(self, key):
        """Normaliza el nombre de la tecla"""
        try:
            # Teclas con carácter
            if hasattr(key, 'char') and key.char:
                return key.char.upper()
            
            # Teclas especiales
            key_name = str(key).replace('Key.', '').upper()
            
            # Mapeos especiales
            mappings = {
                'BACKSPACE': 'BKSP',
                'RETURN': 'ENTER',
                'DELETE': 'DEL',
                'ESC': 'ESC',
                'SPACE': 'SPACE',
                'TAB': 'TAB',
                'CAPS_LOCK': 'CAPS',
                'SHIFT': 'SHIFT',
                'SHIFT_R': 'SHIFT',
                'SHIFT_L': 'SHIFT',
                'CTRL': 'CTRL',
                'CTRL_L': 'CTRL',
                'CTRL_R': 'CTRL',
                'ALT': 'ALT',
                'ALT_L': 'ALT',
                'ALT_R': 'ALTGR',
                'ALT_GR': 'ALTGR',
                'CMD': 'CMD',
            }
            
            # Teclas F
            for i in range(1, 13):
                if f'F{i}' in key_name:
                    return f'F{i}'
            
            return mappings.get(key_name, key_name)
            
        except:
            return None
    
    def on_press(self, key):
        """Callback cuando se presiona una tecla"""
        try:
            normalized = self.normalize_key(key)
            if normalized:
                self.pressed_keys.add(normalized)
                
                # ESC 3 veces para salir
                if normalized == 'ESC' and self.pressed_keys.count('ESC') >= 3:
                    self.running = False
                    return False
                    
        except Exception as e:
            pass
    
    def start(self):
        """Inicia el listener"""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
    
    def stop(self):
        """Detiene el listener"""
        if self.listener:
            self.listener.stop()
    
    def get_pressed_keys(self):
        """Retorna las teclas presionadas"""
        return self.pressed_keys


def draw_keyboard(pressed_keys):
    """Dibuja el teclado con las teclas presionadas marcadas"""
    print("\033[2J\033[H")  # Limpiar pantalla
    print("="*80)
    print(" TEST DE TECLADO CON PYNPUT ".center(80))
    print("="*80)
    print()
    print(f"Teclas detectadas: {len(pressed_keys)}")
    print("Pulsa ESC 3 veces para terminar")
    print()
    
    # Dibujar teclado
    for row in KEYBOARD_LAYOUT:
        line = ""
        for key in row:
            if key in pressed_keys:
                # Verde si está presionada
                line += f"\033[92m[{key:^6s}]\033[0m "
            else:
                # Gris si no
                line += f"\033[90m[{key:^6s}]\033[0m "
        print(line)
    
    print()
    print("Teclas presionadas:")
    for i, key in enumerate(sorted(pressed_keys)):
        print(f"{key:10s}", end="")
        if (i + 1) % 8 == 0:
            print()


if __name__ == "__main__":
    tester = KeyboardTester()
    tester.start()
    
    try:
        while tester.running:
            draw_keyboard(tester.get_pressed_keys())
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        tester.stop()
        
        print("\n\n" + "="*80)
        print(f" RESULTADO: {len(tester.get_pressed_keys())} teclas detectadas")
        print("="*80)
