#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import curses
import os
import json
import datetime
import time
import subprocess
import shutil
import sys
import urllib.request
import urllib.error
import ssl
import re

# --- CONFIGURACIÓN ---
SERVER_BASE = "https://check.novadixital.es"
API_ENDPOINT = f"{SERVER_BASE}/api/report.php"
APP_TITLE = "NOVACHECK PRO v25 (Syntax Fixed)"

# --- CREDENCIALES WIFI ---
AUTO_SSID = "R8"
AUTO_PASS = "52404000"

# --- MAPAS DE TECLADO ---
KEY_LAYOUTS = {
    "ES": [
        "º 1 2 3 4 5 6 7 8 9 0 ' ¡",
        "Q W E R T Y U I O P ` +",
        "A S D F G H J K L Ñ ´ Ç",
        "< Z X C V B N M , . -",
        "SPACE ENTER BKSP TAB"
    ],
    "US": [
        "` 1 2 3 4 5 6 7 8 9 0 - =",
        "Q W E R T Y U I O P [ ] \\",
        "A S D F G H J K L ; ' ENTER",
        "Z X C V B N M , . /",
        "SPACE BKSP TAB"
    ]
}

# ==========================================
# 1. UTILIDADES
# ==========================================

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
    except:
        return ""

def leer_archivo(ruta):
    # CORREGIDO: Estructura expandida para evitar SyntaxError
    try:
        with open(ruta, 'r') as f:
            return f.read().strip()
    except:
        return "N/A"

def check_internet():
    return subprocess.call(["ping", "-c", "1", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def check_dependency(tool):
    return shutil.which(tool) is not None

# ==========================================
# 2. HARDWARE
# ==========================================

def get_hw():
    d = "/sys/class/dmi/id/"
    hw = {"discos":[]}
    hw["fabricante"] = leer_archivo(f"{d}/sys_vendor")
    hw["modelo"] = leer_archivo(f"{d}/product_name")
    hw["serial"] = leer_archivo(f"{d}/product_serial")
    c = run_cmd("grep -m1 'model name' /proc/cpuinfo")
    hw["cpu"] = c.split(":")[1].strip() if c else ""
    m = run_cmd("grep MemTotal /proc/meminfo")
    if m: hw["ram"] = f"{int(m.split()[1])/(1024**2):.2f} GB"
    return hw

def get_real_disks():
    disks = []
    raw = run_cmd("lsblk -d -n -o NAME,TYPE,TRAN,MODEL")
    for line in raw.splitlines():
        if not line.strip(): continue
        p = line.split()
        if len(p)<3: continue
        name, dtype, trans = p[0], p[1], p[2].lower()
        model = " ".join(p[3:]) if len(p)>3 else name
        if dtype!="disk" or name.startswith(("loop","zram","sr")) or "usb" in trans: continue
        disks.append({"dev":name, "model":model})
    return disks

def check_touchpad():
    try:
        devs = run_cmd("cat /proc/bus/input/devices")
        if any(x in devs for x in ["Touchpad","Synaptics","Elan","ALPS","ETPS"]): return "DETECTADO"
        if "TrackPoint" in devs: return "TRACKPOINT"
        return "NO DETECTADO"
    except: return "ERROR"

def test_battery():
    path = "/sys/class/power_supply/"
    bat = None
    if os.path.exists(path):
        for d in os.listdir(path):
            if d.startswith("BAT"): bat=os.path.join(path,d); break
    if not bat: return "NO_BATTERY", "No detectada"
    try:
        def g(n): p=os.path.join(bat,n); return int(open(p).read()) if os.path.exists(p) else None
        fd = g("energy_full_design") or g("charge_full_design")
        fc = g("energy_full") or g("charge_full")
        if fd and fc and fd>0:
            h = (fc/fd)*100
            st = "OK" if h > 40 else "POOR"
            return st, f"{h:.0f}% Vida"
    except: pass
    return "OK", "Detectada"

def test_smart(dev):
    if not check_dependency("smartctl"): return "SKIP", "No Tool"
    o = run_cmd(f"smartctl -H /dev/{dev}")
    return ("OK", "Sano") if "PASSED" in o or "OK" in o else ("FAIL", "Error SMART")

# ==========================================
# 3. AUDIO Y MICRO
# ==========================================

def fix_audio_mixer():
    # 1. Matar PulseAudio
    subprocess.run("pulseaudio -k", shell=True, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    # 2. Inicializar ALSA
    subprocess.run("alsactl init", shell=True, stderr=subprocess.DEVNULL)
    
    # 3. Fuerza bruta en mezclador
    for c in [0, 1]:
        subprocess.run(f"amixer -c {c} set 'Auto-Mute Mode' Disabled", shell=True, stderr=subprocess.DEVNULL)
        for t in ["Master", "Speaker", "Headphone", "PCM", "Front", "Capture", "Mic", "Internal Mic", "Digital"]:
            subprocess.run(f"amixer -c {c} set '{t}' 100% unmute", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"amixer -c {c} set '{t}' on", shell=True, stderr=subprocess.DEVNULL)
            subprocess.run(f"amixer -c {c} set '{t}' cap", shell=True, stderr=subprocess.DEVNULL)

def test_microphone():
    """Busca HW de captura y graba"""
    rec_file = "/tmp/mic.wav"
    if os.path.exists(rec_file): os.remove(rec_file)
    
    try:
        cards_out = run_cmd("arecord -l")
        match = re.search(r'card (\d+):.*device (\d+):', cards_out)
        if match:
            hw_id = f"plughw:{match.group(1)},{match.group(2)}"
            subprocess.run(f"arecord -D {hw_id} -d 2 -f cd -t wav {rec_file}", shell=True, stderr=subprocess.DEVNULL)
    except: pass

    # Fallback default
    if not os.path.exists(rec_file) or os.path.getsize(rec_file) < 100:
        subprocess.run(f"arecord -D default -d 2 -f cd -t wav {rec_file}", shell=True, stderr=subprocess.DEVNULL)

    if not os.path.exists(rec_file): return "FAIL", "No File"
    if os.path.getsize(rec_file) < 1000: return "FAIL", "Empty Rec"
    return "OK", "Grabado OK"

# ==========================================
# 4. INTERFAZ GRÁFICA
# ==========================================

def init_ui():
    s = curses.initscr()
    curses.start_color(); curses.use_default_colors(); curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLUE)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLUE)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(6, curses.COLOR_YELLOW, curses.COLOR_BLUE)  # Amarillo para destacar
    s.bkgd(' ', curses.color_pair(1))
    
    # Intentar ajustar el tamaño de fuente del terminal (puede no funcionar en todos los terminales)
    try:
        # Enviar secuencia de escape para aumentar tamaño de fuente
        sys.stdout.write('\033]50;fixed:pixelsize=20\007')
        sys.stdout.flush()
    except:
        pass
    
    return s

def draw_header(stdscr, sub=""):
    h, w = stdscr.getmaxyx()
    # Línea superior decorativa
    try: 
        stdscr.addstr(0, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
    except: pass
    
    # Título principal más grande
    t = f"  {APP_TITLE}  |  {sub}  "
    bar = t + " " * (w - len(t))
    try: 
        stdscr.addstr(1, 0, bar[:w-1], curses.color_pair(4)|curses.A_BOLD)
    except: pass
    
    # Línea inferior decorativa
    try: 
        stdscr.addstr(2, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
    except: pass

def safe_print(stdscr, y, x, txt, attr=0, large=False):
    """
    Imprime texto de forma segura. Si large=True, agrega espaciado adicional
    """
    h, w = stdscr.getmaxyx()
    # Ajustar Y para el nuevo header de 3 líneas
    y_adjusted = y + 3 if y > 2 else y
    if y_adjusted < h and x < w:
        try: 
            stdscr.addstr(y_adjusted, x, txt[:w-x-1], attr)
        except: pass

def center(stdscr, y, txt, attr=0, large=False):
    """
    Centra texto en la pantalla. Si large=True, usa fuente más grande
    """
    h, w = stdscr.getmaxyx()
    if large:
        txt_display = " ".join(txt)
    else:
        txt_display = txt
    x = max(0, int((w-len(txt_display))/2))
    safe_print(stdscr, y, x, txt, attr, large)

# --- NETWORKING ---
def send_to_server(hw_info, status, tests={}, wipe="PENDING", tech="Unknown"):
    payload = {"hardware":hw_info,"status":status,"timestamp":str(datetime.datetime.now()),"tests":tests,"data_erasure":wipe,"tech":tech}
    try:
        data = json.dumps(payload).encode('utf-8')
        headers = {'Content-Type':'application/json','User-Agent':'NovaCheck/25.0'}
        ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        req = urllib.request.Request(API_ENDPOINT, data=data, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r: return True, f"{r.getcode()}"
    except Exception as e: return False, str(e)[:15]

def connect_wifi(ssid, pwd):
    return subprocess.run(f"nmcli dev wifi connect '{ssid}' password '{pwd}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

# --- PANTALLAS ---

def screen_wifi_logic(stdscr):
    stdscr.nodelay(False); stdscr.clear(); draw_header(stdscr, "CONECTIVIDAD")
    center(stdscr, 10, "Verificando red...")
    stdscr.refresh()
    
    if check_internet(): center(stdscr, 12, "✔ ONLINE", curses.color_pair(2)); time.sleep(1); return
    
    if AUTO_SSID:
        center(stdscr, 12, f"Intentando conectar a {AUTO_SSID}...", curses.A_DIM); stdscr.refresh()
        for i in range(3):
            if connect_wifi(AUTO_SSID, AUTO_PASS):
                center(stdscr, 14, "✔ WIFI AUTO OK", curses.color_pair(2)); time.sleep(1); return
            time.sleep(3)

    while True:
        stdscr.clear(); draw_header(stdscr, "WIFI SCAN"); center(stdscr, 4, "Escaneando...")
        try:
            out = run_cmd("nmcli -f SSID,SIGNAL dev wifi list | awk 'NR>1 {print $0}'")
            nets = []
            for l in out.splitlines():
                if not l.strip(): continue
                p = l.rsplit(None, 1)
                if len(p)==2 and p[0]!="--": nets.append(p)
            nets = list({s:sig for s,sig in nets}.items())
        except: nets = []

        if not nets:
            center(stdscr, 6, "Sin redes."); center(stdscr, 8, "[R]eintentar [S]altar")
            if stdscr.getch() in [ord('s'),ord('S')]: return
            continue
        
        idx=0
        while True:
            stdscr.clear(); draw_header(stdscr, "SELECCIONAR WIFI")
            h, w = stdscr.getmaxyx(); limit = h-5
            for i, (s,sig) in enumerate(nets):
                if i>=limit: break
                attr = curses.A_REVERSE | curses.color_pair(4) if i==idx else 0
                safe_print(stdscr, 4+i, 4, f"{s} ({sig}%)", attr)
            k=stdscr.getch()
            if k==curses.KEY_UP and idx>0: idx-=1
            elif k==curses.KEY_DOWN and idx<len(nets)-1: idx+=1
            elif k in [ord('s'),ord('S')]: return
            elif k in [10,13]:
                ssid=nets[idx][0]
                stdscr.clear(); draw_header(stdscr, f"PASSWORD: {ssid}")
                curses.echo(); curses.curs_set(1); stdscr.move(10, w//2-10)
                try: pwd=stdscr.getstr().decode()
                except: pwd=""
                curses.noecho(); curses.curs_set(0)
                if not pwd: break
                center(stdscr,12,"Conectando...", curses.A_BLINK); stdscr.refresh()
                if connect_wifi(ssid, pwd): return
                else: center(stdscr,14,"ERROR CLAVE", curses.color_pair(3)); time.sleep(1); break

def screen_tech(stdscr):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # Header sin safe_print para evitar ajustes
    try:
        stdscr.addstr(0, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " NOVACHECK PRO | IDENTIFICACIÓN ".ljust(w-1), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
    except: pass
    
    # Título
    try:
        stdscr.addstr(6, 2, "═══════════════════════════════════════")
        stdscr.addstr(7, 2, "  IDENTIFICACIÓN DEL TÉCNICO  ", curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(8, 2, "═══════════════════════════════════════")
    except: pass
    
    # Prompt
    try:
        stdscr.addstr(11, 2, "Por favor, escribe tu nombre:", curses.A_BOLD)
    except: pass
    
    # Área limpia para input
    try:
        stdscr.addstr(13, 2, " " * (w-4))  # Limpiar línea
        stdscr.addstr(13, 2, ">> ")
    except: pass
    
    stdscr.refresh()
    
    # Input
    curses.echo()
    curses.curs_set(1)
    stdscr.move(13, 5)  # Posición después de ">> "
    
    try: 
        name = stdscr.getstr(13, 5, 40).decode().strip()
    except: 
        name = "Unknown"
    
    curses.noecho()
    curses.curs_set(0)
    
    return name if name else "Anónimo"

def screen_hw_info(stdscr, hw, tech):
    stdscr.clear()
    draw_header(stdscr, "INFORMACIÓN HARDWARE")
    
    r=5
    # Técnico con más espacio
    safe_print(stdscr, r, 4, "═══════════════════════════════════════", curses.color_pair(6) | curses.A_BOLD)
    r+=1
    safe_print(stdscr, r, 4, f"  TÉCNICO: {tech}", curses.color_pair(4) | curses.A_BOLD)
    r+=1
    safe_print(stdscr, r, 4, "═══════════════════════════════════════", curses.color_pair(6) | curses.A_BOLD)
    r+=3
    
    # Información del sistema con mejor formato
    safe_print(stdscr, r, 4, "SISTEMA:", curses.A_BOLD | curses.color_pair(6))
    r+=2
    for k,v in [("MODELO",hw["modelo"]),("SERIAL",hw["serial"]),("CPU",hw["cpu"]),("RAM",hw["ram"])]:
        safe_print(stdscr, r, 6, f"• {k}:", curses.A_BOLD)
        safe_print(stdscr, r, 20, f"{v}")
        r+=2
    
    r+=1
    safe_print(stdscr, r, 4, "ALMACENAMIENTO:", curses.A_BOLD | curses.color_pair(6))
    r+=2
    disks = get_real_disks()
    if disks:
        for d in disks:
            safe_print(stdscr, r, 6, f"• {d['model']} ({d['dev']})")
            r+=2
    else:
        safe_print(stdscr, r, 6, "• No detectado")
        r+=2
    
    r+=2
    center(stdscr, r, "[ Presiona ENTER para continuar ]", curses.color_pair(6) | curses.A_BOLD)
    stdscr.refresh()
    while stdscr.getch() not in [10,13]: pass

def screen_usb_interactive(stdscr):
    stdscr.clear()
    draw_header(stdscr, "TEST PUERTO USB")
    
    base_usb = run_cmd("lsusb").splitlines()
    count_base = len(base_usb)
    
    center(stdscr, 6, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 7, "   PRUEBA DE PUERTO USB   ", curses.A_BOLD | curses.color_pair(6))
    center(stdscr, 8, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, f"Dispositivos USB actuales: {count_base}", curses.A_DIM)
    center(stdscr, 14, "╔═══════════════════════════════════════╗", curses.color_pair(4))
    center(stdscr, 15, "║  CONECTA UN RATÓN O PENDRIVE AHORA   ║", curses.color_pair(4) | curses.A_BLINK | curses.A_BOLD)
    center(stdscr, 16, "╚═══════════════════════════════════════╝", curses.color_pair(4))
    center(stdscr, 19, "Esperando dispositivo... (15 segundos)", curses.A_DIM)
    center(stdscr, 21, "[S] Saltar si no hay dispositivo USB", curses.color_pair(3))
    stdscr.refresh()
    stdscr.nodelay(True)
    
    start = time.time()
    detected = False
    elapsed = 0
    
    while time.time() - start < 15:
        curr_usb = run_cmd("lsusb").splitlines()
        if len(curr_usb) > count_base:
            detected = True
            break
        
        # Actualizar contador
        elapsed = int(time.time() - start)
        remaining = 15 - elapsed
        center(stdscr, 19, f"Esperando dispositivo... ({remaining} segundos)  ", curses.A_DIM)
        stdscr.refresh()
        
        try:
            if stdscr.getch() in [ord('s'), ord('S')]: 
                break
        except: 
            pass
        time.sleep(0.5)
        
    stdscr.nodelay(False)
    stdscr.clear()
    draw_header(stdscr, "TEST PUERTO USB")
    
    if detected:
        center(stdscr, 10, "════════════════════════════════════", curses.A_BOLD)
        center(stdscr, 11, "  ✔  DISPOSITIVO DETECTADO  ✔  ", curses.color_pair(2) | curses.A_BOLD)
        center(stdscr, 12, "════════════════════════════════════", curses.A_BOLD)
        center(stdscr, 15, "Puerto USB funciona correctamente", curses.color_pair(2))
        stdscr.refresh()
        time.sleep(2)
        return "OK"
    else:
        center(stdscr, 10, "════════════════════════════════════", curses.A_BOLD)
        center(stdscr, 11, "  ✖  NO SE DETECTÓ DISPOSITIVO  ✖  ", curses.color_pair(3) | curses.A_BOLD)
        center(stdscr, 12, "════════════════════════════════════", curses.A_BOLD)
        center(stdscr, 15, "No se conectó ningún dispositivo USB", curses.color_pair(3))
        stdscr.refresh()
        time.sleep(2)
        return "FAIL"

def screen_auto(stdscr):
    stdscr.clear()
    draw_header(stdscr, "TESTS AUTOMÁTICOS")
    
    r=5
    safe_print(stdscr, r, 4, "EJECUTANDO DIAGNÓSTICO...", curses.A_BOLD | curses.color_pair(6))
    r+=3
    
    # Bateria
    safe_print(stdscr, r, 4, "• Comprobando BATERÍA...", curses.A_DIM)
    stdscr.refresh()
    st, msg = test_battery()
    col = curses.color_pair(2 if st in ["OK","NO_BATTERY"] else 3)
    safe_print(stdscr, r, 4, "• BATERÍA:", curses.A_BOLD)
    safe_print(stdscr, r, 20, f"{st} ({msg})", col | curses.A_BOLD)
    res={"bat":{"st":st,"msg":msg}}
    r+=2
    
    # Touch
    safe_print(stdscr, r, 4, "• Comprobando TOUCHPAD...", curses.A_DIM)
    stdscr.refresh()
    time.sleep(0.5)
    tp = check_touchpad()
    safe_print(stdscr, r, 4, "• TOUCHPAD:", curses.A_BOLD)
    safe_print(stdscr, r, 20, tp, curses.color_pair(2 if tp!="NO DETECTADO" else 3) | curses.A_BOLD)
    res["touch"]=tp
    r+=2
    stdscr.refresh()
    
    # USB Interactivo
    usb_st = screen_usb_interactive(stdscr)
    stdscr.clear()
    draw_header(stdscr, "TESTS AUTOMÁTICOS")
    
    r=5
    safe_print(stdscr, r, 4, "RESUMEN DE DIAGNÓSTICO:", curses.A_BOLD | curses.color_pair(6))
    r+=3
    
    safe_print(stdscr, r, 4, "• BATERÍA:", curses.A_BOLD)
    safe_print(stdscr, r, 20, f"{st} ({msg})", col | curses.A_BOLD)
    r+=2
    
    safe_print(stdscr, r, 4, "• TOUCHPAD:", curses.A_BOLD)
    safe_print(stdscr, r, 20, tp, curses.color_pair(2 if tp!="NO DETECTADO" else 3) | curses.A_BOLD)
    r+=2
    
    col_usb = curses.color_pair(2 if usb_st=="OK" else 3)
    safe_print(stdscr, r, 4, "• PUERTO USB:", curses.A_BOLD)
    safe_print(stdscr, r, 20, usb_st, col_usb | curses.A_BOLD)
    res["usb"]=usb_st
    r+=3
    
    # Discos
    safe_print(stdscr, r, 4, "• SMART CHECK (Discos):", curses.A_BOLD)
    r+=2
    real_disks = get_real_disks()
    sm=[]
    if not real_disks:
        safe_print(stdscr, r, 6, "No detectados.", curses.color_pair(3))
        r+=1
    else:
        for d in real_disks:
            s="OK"
            o=run_cmd(f"smartctl -H /dev/{d['dev']}") if check_dependency("smartctl") else "SKIP"
            if "PASSED" not in o and "OK" not in o and o!="SKIP": s="FAIL"
            col=curses.color_pair(2 if s=="OK" else 3)
            safe_print(stdscr, r, 6, f"[{d['dev']}]", curses.A_BOLD)
            safe_print(stdscr, r, 18, s, col | curses.A_BOLD)
            sm.append({"dev":d['dev'],"st":s})
            r+=1
    res["smart"]=sm
    
    r+=2
    center(stdscr, r, "[ Presiona ENTER para continuar ]", curses.color_pair(6) | curses.A_BOLD)
    stdscr.refresh()
    while stdscr.getch() not in [10,13]: pass
    return res

def play_test_sound():
    """Genera y reproduce un tono de prueba sin mostrar output"""
    # Generar archivo WAV de prueba con sox o usar beep
    test_file = "/tmp/test_beep.wav"
    
    # Intentar generar con sox
    if shutil.which("sox"):
        subprocess.run(f"sox -n {test_file} synth 1 sine 800", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        # Fallback: usar speaker-test pero en background y capturado
        subprocess.run("(speaker-test -t sine -f 800 -l 1 >/dev/null 2>&1) &", 
                      shell=True)
        time.sleep(2)
        return True
    
    # Reproducir con aplay (silencioso)
    if os.path.exists(test_file):
        subprocess.run(f"aplay -q {test_file}", 
                      shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(test_file)
        return True
    return False

def screen_audio_adv(stdscr):
    res={"L":"FAIL","R":"FAIL","MIC":"FAIL"}
    
    # Pantalla inicial - Reset audio
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO CHECK ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(8, 20, "Inicializando drivers de audio...")
        stdscr.refresh()
    except: pass
    
    fix_audio_mixer()
    time.sleep(2)
    
    # Prueba IZQUIERDO (Left)
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - ALTAVOZ IZQUIERDO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(11, 15, "  ALTAVOZ IZQUIERDO (LEFT)  ", curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(12, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(15, 20, "Reproduciendo sonido...", curses.A_BLINK)
        stdscr.refresh()
    except: pass
    
    time.sleep(1)
    
    # Reproducir sonido (sin output visible)
    play_test_sound()
    
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - ALTAVOZ IZQUIERDO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "¿Se escuchó el ALTAVOZ IZQUIERDO?", curses.A_BOLD)
        stdscr.addstr(13, 25, "[S] SI", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(15, 25, "[N] NO", curses.color_pair(3) | curses.A_BOLD)
        stdscr.refresh()
    except: pass
    
    if stdscr.getch() in [ord('s'),ord('S')]: 
        res["L"]="OK"
    
    # Prueba DERECHO (Right)
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - ALTAVOZ DERECHO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(11, 15, "  ALTAVOZ DERECHO (RIGHT)  ", curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(12, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(15, 20, "Reproduciendo sonido...", curses.A_BLINK)
        stdscr.refresh()
    except: pass
    
    time.sleep(1)
    
    # Reproducir sonido
    play_test_sound()
    
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - ALTAVOZ DERECHO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "¿Se escuchó el ALTAVOZ DERECHO?", curses.A_BOLD)
        stdscr.addstr(13, 25, "[S] SI", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(15, 25, "[N] NO", curses.color_pair(3) | curses.A_BOLD)
        stdscr.refresh()
    except: pass
    
    if stdscr.getch() in [ord('s'),ord('S')]: 
        res["R"]="OK"
    
    # Prueba de micrófono
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - MICRÓFONO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(8, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(9, 15, "  PRUEBA DE MICRÓFONO  ", curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(10, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(13, 15, "¡Di algo FUERTE durante 2 segundos!", curses.A_BLINK | curses.A_BOLD)
        stdscr.addstr(16, 15, "Grabando en 3 segundos...")
        stdscr.refresh()
    except: pass
    
    time.sleep(3)
    
    st, msg = test_microphone()
    
    # Mostrar resultado automáticamente por 2 segundos
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " AUDIO - MICRÓFONO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        col = curses.color_pair(2 if st=="OK" else 3)
        stdscr.addstr(10, 20, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(11, 20, f"  {msg}  ", col | curses.A_BOLD)
        stdscr.addstr(12, 20, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(15, 20, "Continuando automáticamente...", curses.A_DIM)
        stdscr.refresh()
    except: pass
    
    time.sleep(2)
    res["MIC"]=st
    
    return "OK" if res["L"]=="OK" and res["R"]=="OK" and res["MIC"]=="OK" else "FAIL"

def screen_visual(stdscr):
    cols=[(curses.COLOR_RED,"ROJO"),(curses.COLOR_GREEN,"VERDE"),(curses.COLOR_BLUE,"AZUL"),(curses.COLOR_WHITE,"BLANCO")]
    
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL")
    center(stdscr, 10, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  PRUEBA DE PANTALLA Y COLORES  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 15, "Se mostrarán 4 colores en pantalla COMPLETA", curses.color_pair(6))
    center(stdscr, 17, "Busca píxeles muertos, manchas o defectos", curses.A_BOLD)
    center(stdscr, 20, "Presiona cualquier tecla para comenzar", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()
    
    # Mostrar cada color SIN TEXTO (pantalla limpia para ver defectos)
    for c,n in cols:
        curses.init_pair(20,curses.COLOR_WHITE,c)
        stdscr.bkgd(' ',curses.color_pair(20))
        stdscr.erase()  # Limpiar TODO incluyendo background
        stdscr.refresh()
        time.sleep(0.5)
        stdscr.getch()
    
    # Restaurar y preguntar resultado
    stdscr.bkgd(' ',curses.color_pair(1))
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL - RESULTADO")
    center(stdscr, 10, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  ¿HAY DEFECTOS EN LA PANTALLA?  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 15, "(Píxeles muertos, manchas, líneas, etc.)", curses.A_DIM)
    center(stdscr, 18, "[N] NO - Todo perfecto", curses.color_pair(2) | curses.A_BOLD)
    center(stdscr, 20, "[S] SÍ - Hay defectos", curses.color_pair(3) | curses.A_BOLD)
    stdscr.refresh()
    
    return "OK" if stdscr.getch() in [ord('n'),ord('N')] else "FAIL"

def map_key(k):
    # Teclas especiales comunes
    if k in [10,13]: return "ENTER"
    if k==32: return "SPACE"
    if k in [263,127]: return "BKSP"
    if k==9: return "TAB"
    if k==60: return "<"
    
    # Caracteres especiales españoles (minúsculas)
    if k==241: return "Ñ"  # ñ
    if k==209: return "Ñ"  # Ñ
    if k==231: return "Ç"  # ç
    if k==199: return "Ç"  # Ç
    if k==180: return "´"  # acento agudo
    if k==96: return "`"   # acento grave
    if k==161: return "¡"  # ¡
    if k==191: return "¿"  # ¿
    if k==186: return "º"  # º
    if k==170: return "ª"  # ª
    if k==43: return "+"   # +
    if k==45: return "-"   # -
    if k==39: return "'"   # '
    if k==44: return ","   # ,
    if k==46: return "."   # .
    
    # Intentar convertir el resto
    try: 
        char = chr(k).upper()
        return char if char.isprintable() else None
    except: 
        return None

def screen_keyboard_vis(stdscr):
    """
    Método UNIVERSAL de test de teclado - NO depende de layout específico
    Simplemente muestra las teclas que se van pulsando en tiempo real
    """
    stdscr.clear()
    draw_header(stdscr, "TEST DE TECLADO UNIVERSAL")
    
    center(stdscr, 6, "════════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 7, "  PRUEBA DE TECLADO  ", curses.A_BOLD | curses.color_pair(6))
    center(stdscr, 8, "════════════════════════════════════════", curses.A_BOLD)
    
    center(stdscr, 11, "INSTRUCCIONES:", curses.A_BOLD | curses.color_pair(6))
    center(stdscr, 13, "• Pulsa TODAS las teclas de tu teclado")
    center(stdscr, 14, "• Verás aparecer cada tecla en la lista")
    center(stdscr, 15, "• Presiona [ESC] 3 veces para terminar")
    
    center(stdscr, 18, "Presiona cualquier tecla para comenzar...", curses.A_DIM)
    stdscr.refresh()
    stdscr.getch()
    
    pressed_keys = []
    pressed_set = set()
    esc_count = 0
    stdscr.nodelay(True)
    stdscr.timeout(100)
    
    while True:
        stdscr.clear()
        draw_header(stdscr, "TEST DE TECLADO - EN PROGRESO")
        
        # Instrucciones compactas
        safe_print(stdscr, 4, 4, "INSTRUCCIONES: Pulsa todas las teclas | [ESC] 3 veces para terminar", 
                  curses.A_BOLD | curses.color_pair(6))
        
        # Contador grande
        safe_print(stdscr, 6, 4, f"═══ TECLAS PRESIONADAS: {len(pressed_set)} ═══", 
                  curses.color_pair(2) | curses.A_BOLD)
        
        # Barra de progreso visual
        progress = min(len(pressed_set), 50)
        bar = "█" * progress + "░" * (50 - progress)
        safe_print(stdscr, 7, 4, f"[{bar}]")
        
        # Lista de teclas presionadas (últimas 40)
        safe_print(stdscr, 9, 4, "TECLAS DETECTADAS:", curses.A_BOLD | curses.A_UNDERLINE)
        
        start_row = 10
        max_display = 15  # Máximo número de filas
        cols = 5  # Número de columnas
        
        # Mostrar en formato de columnas
        display_keys = pressed_keys[-60:]  # Últimas 60 teclas
        for idx, key in enumerate(display_keys):
            col_num = idx % cols
            row_num = idx // cols
            if row_num < max_display:
                x_pos = 6 + (col_num * 15)
                y_pos = start_row + row_num
                safe_print(stdscr, y_pos, x_pos, f"• {key}", curses.color_pair(5))
        
        # Indicador ESC
        if esc_count > 0:
            safe_print(stdscr, start_row + max_display + 2, 4, 
                      f"ESC presionado: {esc_count}/3", 
                      curses.color_pair(3) | curses.A_BOLD)
        
        stdscr.refresh()
        
        try:
            k = stdscr.getch()
        except:
            k = -1
        
        if k != -1:
            # Detectar ESC (código 27)
            if k == 27:
                esc_count += 1
                if esc_count >= 3:
                    break
            else:
                esc_count = 0  # Reset si se pulsa otra tecla
            
            # Mapear la tecla
            char = map_key(k)
            
            # Si no hay mapeo, usar el código directamente
            if not char:
                char = f"KEY_{k}"
            
            # Agregar a la lista si no está duplicada consecutivamente
            if not pressed_keys or pressed_keys[-1] != char:
                pressed_keys.append(char)
                pressed_set.add(char)
        
        time.sleep(0.05)  # Pequeña pausa para no saturar CPU
    
    stdscr.nodelay(False)
    
    # Pantalla de resumen
    stdscr.clear()
    draw_header(stdscr, "TEST DE TECLADO - COMPLETADO")
    
    center(stdscr, 8, "════════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 9, f"  TOTAL: {len(pressed_set)} TECLAS DETECTADAS  ", 
           curses.color_pair(2) | curses.A_BOLD)
    center(stdscr, 10, "════════════════════════════════════════", curses.A_BOLD)
    
    # Determinar resultado
    if len(pressed_set) >= 30:
        center(stdscr, 13, "✓ TEST PASADO", curses.color_pair(2) | curses.A_BOLD)
        result = "OK"
    else:
        center(stdscr, 13, "✗ Pocas teclas detectadas", curses.color_pair(3) | curses.A_BOLD)
        result = "FAIL"
    
    center(stdscr, 16, "Presiona cualquier tecla para continuar...")
    stdscr.refresh()
    stdscr.getch()
    
    return result

def screen_wipe(stdscr):
    stdscr.clear(); draw_header(stdscr, "BORRADO SEGURO")
    disks = get_real_disks()
    if not disks: center(stdscr, 10, "Sin disco."); stdscr.getch(); return "SKIP"
    tgt = disks[0]["dev"]
    center(stdscr, 10, f"DISCO: {tgt}"); center(stdscr, 12, "Escribe 'SI':")
    curses.echo(); h,w=stdscr.getmaxyx(); stdscr.move(14, w//2-5)
    ans=stdscr.getstr().decode(); curses.noecho()
    if ans.upper()!="SI": return "SKIP"
    center(stdscr, 16, "BORRANDO... (NO APAGAR)", curses.A_BLINK); stdscr.refresh()
    subprocess.run(f"shred -n 1 -z /dev/{tgt}", shell=True, stderr=subprocess.DEVNULL)
    return "OK"

def main(stdscr):
    stdscr = init_ui()
    try: 
        if int(datetime.datetime.now().year)<2024: subprocess.run('date -s "2025-01-01 12:00:00"',shell=True)
    except: pass
    
    screen_wifi_logic(stdscr)
    tech = screen_tech(stdscr)
    hw = get_hw()
    
    screen_hw_info(stdscr, hw, tech)
    
    ra = screen_auto(stdscr)
    rs = screen_audio_adv(stdscr)
    rv = screen_visual(stdscr)
    rk = screen_keyboard_vis(stdscr)
    rw = screen_wipe(stdscr)
    
    final = "PASS" if rs=="OK" and rw!="FAIL" and rv!="FAIL" and rk=="OK" else "FAIL"
    for d in ra.get("smart",[]):
        if d["st"]=="FAIL": final="FAIL"
        
    ok, msg = send_to_server(hw, final, {"auto":ra,"aud":rs,"vis":rv,"kbd":rk,"wipe":rw}, rw, tech)
    
    stdscr.clear(); draw_header(stdscr, "INFORME FINAL")
    r=4
    safe_print(stdscr, r, 2, f"RESULTADO: {final}", curses.color_pair(2 if final=="PASS" else 3)); r+=2
    safe_print(stdscr, r, 2, f"SERVIDOR: {'ENVIADO' if ok else msg}", curses.color_pair(2 if ok else 3)); r+=2
    
    if shutil.which("qrencode"):
        try:
            qr = subprocess.run(["qrencode","-t","ASCII",f"{hw['serial']}|{final}"],capture_output=True,text=True).stdout.splitlines()
            for l in qr: safe_print(stdscr, r, 4, l); r+=1
        except: pass
        
    h,w=stdscr.getmaxyx(); safe_print(stdscr, h-1, 2, "[Q] Apagar")
    while stdscr.getch() not in [ord('q'),ord('Q')]: pass
    os.system("poweroff")

if __name__ == "__main__":
    if os.geteuid()!=0: print("ROOT REQUIRED"); exit()
    try: curses.wrapper(main)
    except Exception as e: print(e)