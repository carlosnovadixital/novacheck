#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys, os, time, subprocess, datetime, shutil, json, curses
import warnings

# Silenciar todos los RuntimeWarnings (incluido AVX2 de pygame)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# Silenciar mensajes de pygame y ALSA ANTES de cualquier import
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_AUDIODRIVER'] = 'alsa'
os.environ['PYGAME_DETECT_AVX2'] = '0'  # Silenciar warning de AVX2

# Configurar logging antes de cualquier cosa
LOG_FILE = "/tmp/novacheck_debug.log"
log_handle = open(LOG_FILE, 'w')

def log_debug(msg):
    """Escribir mensaje de debug al log"""
    try:
        log_handle.write(f"[{datetime.datetime.now()}] {msg}\n")
        log_handle.flush()
    except:
        pass

import curses
import json
import datetime
import time
import subprocess
import shutil
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
    subprocess.run("pulseaudio -k", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    # 2. Inicializar ALSA
    subprocess.run("alsactl init", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 3. Fuerza bruta en mezclador - SILENCIAR COMPLETAMENTE
    for c in [0, 1]:
        subprocess.run(f"amixer -c {c} set 'Auto-Mute Mode' Disabled 2>/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for t in ["Master", "Speaker", "Headphone", "PCM", "Front", "Capture", "Mic", "Internal Mic", "Digital"]:
            subprocess.run(f"amixer -c {c} set '{t}' 100% unmute 2>/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(f"amixer -c {c} set '{t}' on 2>/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(f"amixer -c {c} set '{t}' cap 2>/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    
    # Header
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
        stdscr.addstr(13, 2, " " * 50)  # Limpiar área amplia
        stdscr.addstr(13, 2, ">> ", curses.A_BOLD)
    except: pass
    
    stdscr.refresh()
    
    # Input - SIN timeout, espera indefinidamente
    curses.echo()
    curses.curs_set(1)
    stdscr.nodelay(False)  # Asegurar que NO hay timeout
    stdscr.timeout(-1)      # Esperar indefinidamente
    
    try:
        # Posicionar cursor y leer string
        stdscr.move(13, 5)
        name_bytes = stdscr.getstr(13, 5, 40)  # Max 40 caracteres
        name = name_bytes.decode('utf-8', errors='ignore').strip()
    except Exception as e:
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
    center(stdscr, r, "Continuando automáticamente...", curses.A_DIM)
    stdscr.refresh()
    time.sleep(3)  # Continuar automáticamente después de 3 segundos

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

def detect_audio_devices():
    """Detecta todos los dispositivos de audio disponibles"""
    devices = []
    
    # Obtener lista de dispositivos de reproducción
    output = run_cmd("aplay -l 2>/dev/null")
    
    if not output:
        # Fallback: intentar con pactl si está disponible
        output = run_cmd("pactl list short sinks 2>/dev/null")
    
    # Parsear dispositivos de aplay -l
    # Formato: card X: ... device Y: ...
    import re
    for line in output.splitlines():
        match = re.search(r'card (\d+):.*device (\d+):', line)
        if match:
            card = match.group(1)
            device = match.group(2)
            devices.append({
                'hw': f"hw:{card},{device}",
                'plughw': f"plughw:{card},{device}"
            })
    
    # Si no encontramos nada, usar defaults
    if not devices:
        devices = [
            {'hw': 'hw:0,0', 'plughw': 'plughw:0,0'},
            {'hw': 'hw:1,0', 'plughw': 'plughw:1,0'},
            {'hw': 'default', 'plughw': 'default'}
        ]
    
    return devices

def play_audio_pygame(channel='both'):
    """
    Reproduce audio usando pygame con control preciso de canales L/R
    channel: 'left', 'right', 'both'
    """
    try:
        import numpy as np
        import pygame
        import os
        
        log_debug(f"=== Iniciando play_audio_pygame para canal: {channel} ===")
        
        # Redirigir stderr temporalmente pero guardarlo en log
        import sys
        old_stderr = sys.stderr
        old_stdout = sys.stdout
        
        # Crear un buffer temporal para capturar mensajes
        import io
        stderr_buffer = io.StringIO()
        sys.stderr = stderr_buffer
        sys.stdout = stderr_buffer
        
        try:
            # Generar tono sinusoidal
            frequency = 800
            duration = 1.5
            sample_rate = 44100
            
            t = np.linspace(0, duration, int(sample_rate * duration))
            tone = np.sin(2 * np.pi * frequency * t)
            tone = (tone * 32767).astype(np.int16)
            
            # Crear audio estéreo según canal
            if channel == 'left':
                left = tone
                right = np.zeros_like(tone)
            elif channel == 'right':
                left = np.zeros_like(tone)
                right = tone
            else:
                left = tone
                right = tone
            
            stereo = np.column_stack((left, right))
            
            # Inicializar pygame mixer con más intentos
            try:
                pygame.mixer.quit()  # Por si acaso
            except:
                pass
            
            # Intentar inicializar con varios dispositivos
            init_success = False
            device_attempts = [None, 'default', 'hw:0,0', 'plughw:0,0']
            
            for device in device_attempts:
                try:
                    log_debug(f"Intentando inicializar pygame.mixer con device={device}")
                    if device:
                        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=1024, devicename=device)
                    else:
                        pygame.mixer.init(frequency=sample_rate, size=-16, channels=2, buffer=1024)
                    init_success = True
                    log_debug(f"Inicialización exitosa con device={device}")
                    break
                except Exception as e:
                    log_debug(f"Falló con device={device}: {e}")
                    continue
            
            if not init_success:
                log_debug("No se pudo inicializar pygame.mixer con ningún dispositivo")
                return False
            
            # Crear y reproducir sonido
            sound = pygame.sndarray.make_sound(stereo)
            sound.play()
            
            # Esperar a que termine
            while pygame.mixer.get_busy():
                pygame.time.wait(100)
            
            pygame.mixer.quit()
            log_debug(f"Audio {channel} reproducido exitosamente")
            return True
        finally:
            # Capturar y guardar los mensajes antes de restaurar
            captured = stderr_buffer.getvalue()
            if captured:
                log_debug(f"Mensajes capturados durante reproducción:\n{captured}")
            
            # Restaurar stderr y stdout
            sys.stderr = old_stderr
            sys.stdout = old_stdout
        
    except ImportError as e:
        log_debug(f"ImportError en pygame: {e}")
        # Fallback a sox si pygame no está disponible
        return play_simple_audio_test_fallback()
    except Exception as e:
        log_debug(f"Error en play_audio_pygame: {type(e).__name__}: {e}")
        import traceback
        log_debug(f"Traceback:\n{traceback.format_exc()}")
        return False

def play_simple_audio_test_fallback():
    """
    Fallback usando sox si pygame no está disponible
    """
    test_file = "/tmp/test_audio.wav"
    
    if shutil.which("sox"):
        subprocess.run(
            f"sox -n -r 44100 -c 2 {test_file} synth 1.5 sine 800 2>/dev/null",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    
    if not os.path.exists(test_file):
        return False
    
    devices = detect_audio_devices()
    
    for dev in devices:
        for dev_name in [dev['plughw'], dev['hw']]:
            result = subprocess.run(
                f"aplay -q -D {dev_name} {test_file} 2>/dev/null",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                try:
                    os.remove(test_file)
                except:
                    pass
                return True
    
    result = subprocess.run(
        f"aplay -q {test_file} 2>/dev/null",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    try:
        os.remove(test_file)
    except:
        pass
    
    return result.returncode == 0

def screen_speakers(stdscr):
    """Test solo de altavoces LEFT/RIGHT"""
    res={"L":"FAIL","R":"FAIL"}
    
    log_debug("=== Iniciando test de SPEAKERS ===")
    
    # Matar pipewire y pulseaudio para acceso directo a ALSA
    log_debug("Matando pipewire y pulseaudio...")
    subprocess.run("killall -9 pipewire pipewire-pulse wireplumber pulseaudio 2>/dev/null", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Inicializar audio silenciosamente
    log_debug("Inicializando mixer de audio...")
    fix_audio_mixer()
    time.sleep(1)
    
    # PRUEBA ALTAVOZ IZQUIERDO (LEFT)
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " ALTAVOZ IZQUIERDO (LEFT) ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 20, "Reproduciendo en canal IZQUIERDO...")
        stdscr.addstr(12, 20, "Escucha atentamente...", curses.A_DIM)
        stdscr.refresh()
    except: pass
    
    time.sleep(1)
    
    # Reproducir solo en canal LEFT usando pygame
    play_audio_pygame('left')
    
    time.sleep(1)
    
    # Preguntar resultado
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " ALTAVOZ IZQUIERDO (LEFT) ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "¿Se ESCUCHÓ el altavoz IZQUIERDO?", curses.A_BOLD)
        stdscr.addstr(14, 20, "[SPACE / ENTER] = SÍ", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(16, 20, "[N] = NO", curses.color_pair(3) | curses.A_BOLD)
        stdscr.refresh()
    except: pass
    
    key = stdscr.getch()
    log_debug(f"Tecla capturada para LEFT: {key}")
    if key in [32, 10, 13, 115, 83]:  # SPACE, ENTER, 's', 'S'
        res["L"]="OK"
        log_debug("LEFT marcado como OK")
    else:
        log_debug(f"LEFT marcado como FAIL (tecla {key} no válida)")
    
    # PRUEBA ALTAVOZ DERECHO (RIGHT)
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " ALTAVOZ DERECHO (RIGHT) ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 20, "Reproduciendo en canal DERECHO...")
        stdscr.addstr(12, 20, "Escucha atentamente...", curses.A_DIM)
        stdscr.refresh()
    except: pass
    
    time.sleep(1)
    
    # Reproducir solo en canal RIGHT usando pygame
    play_audio_pygame('right')
    
    time.sleep(1)
    
    # Preguntar resultado
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " ALTAVOZ DERECHO (RIGHT) ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(10, 15, "¿Se ESCUCHÓ el altavoz DERECHO?", curses.A_BOLD)
        stdscr.addstr(14, 20, "[SPACE / ENTER] = SÍ", curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(16, 20, "[N] = NO", curses.color_pair(3) | curses.A_BOLD)
        stdscr.refresh()
    except: pass
    
    key = stdscr.getch()
    log_debug(f"Tecla capturada para RIGHT: {key}")
    if key in [32, 10, 13, 115, 83]:  # SPACE, ENTER, 's', 'S'
        res["R"]="OK"
        log_debug("RIGHT marcado como OK")
    else:
        log_debug(f"RIGHT marcado como FAIL (tecla {key} no válida)")
    
    log_debug(f"Resultado final SPEAKERS: {res}")
    return "OK" if res["L"]=="OK" and res["R"]=="OK" else "FAIL"

def screen_microphone(stdscr):
    """Test solo de micrófono"""
    log_debug("=== Iniciando test de MICRÓFONO ===")
    
    # PRUEBA DE MICRÓFONO
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " PRUEBA DE MICRÓFONO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(9, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(10, 15, "  PRUEBA DE MICRÓFONO  ", curses.color_pair(6) | curses.A_BOLD)
        stdscr.addstr(11, 15, "════════════════════════════════════", curses.A_BOLD)
        stdscr.addstr(14, 15, "¡Habla FUERTE durante 2 segundos!", curses.A_BLINK | curses.A_BOLD)
        stdscr.addstr(16, 15, "Empezando en 2 segundos...")
        stdscr.refresh()
    except: pass
    
    time.sleep(2)
    
    st, msg = test_microphone()
    
    # Mostrar resultado y continuar automáticamente
    stdscr.erase()
    stdscr.refresh()
    
    try:
        stdscr.addstr(0, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " PRUEBA DE MICRÓFONO ".center(79), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * 79, curses.color_pair(4)|curses.A_BOLD)
        
        col = curses.color_pair(2 if st=="OK" else 3)
        stdscr.addstr(10, 25, "════════════════════════", curses.A_BOLD)
        stdscr.addstr(11, 25, f"  {msg}  ", col | curses.A_BOLD)
        stdscr.addstr(12, 25, "════════════════════════", curses.A_BOLD)
        stdscr.addstr(15, 20, "Continuando automáticamente...", curses.A_DIM)
        stdscr.refresh()
    except: pass
    
    time.sleep(2)
    
    log_debug(f"Resultado MICRÓFONO: {st}")
    return st

def screen_visual(stdscr):
    cols=[(curses.COLOR_RED,"ROJO"),(curses.COLOR_GREEN,"VERDE"),(curses.COLOR_BLUE,"AZUL"),(curses.COLOR_WHITE,"BLANCO")]
    
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL")
    center(stdscr, 10, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  PRUEBA DE PANTALLA Y COLORES  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 15, "Se mostrarán 4 colores en pantalla COMPLETA", curses.color_pair(6))
    center(stdscr, 17, "Busca píxeles muertos, manchas o defectos", curses.A_BOLD)
    center(stdscr, 20, "[SPACE / ENTER] para comenzar", curses.A_DIM)
    stdscr.refresh()
    
    # Esperar SPACE o ENTER
    while True:
        k = stdscr.getch()
        if k in [32, 10, 13]:  # SPACE, ENTER
            break
    
    # Mostrar cada color SIN TEXTO (pantalla limpia para ver defectos)
    for c,n in cols:
        curses.init_pair(20,curses.COLOR_WHITE,c)
        stdscr.bkgd(' ',curses.color_pair(20))
        stdscr.erase()  # Limpiar TODO incluyendo background
        stdscr.refresh()
        time.sleep(0.5)
        
        # Siguiente color con SPACE/ENTER
        while True:
            k = stdscr.getch()
            if k in [32, 10, 13]:
                break
    
    # Restaurar y preguntar resultado - UX CONSISTENTE
    stdscr.bkgd(' ',curses.color_pair(1))
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL - RESULTADO")
    center(stdscr, 10, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  ¿HAY DEFECTOS EN LA PANTALLA?  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════════", curses.A_BOLD)
    center(stdscr, 15, "(Píxeles muertos, manchas, líneas, etc.)", curses.A_DIM)
    center(stdscr, 18, "[SPACE / ENTER] = NO - Todo perfecto", curses.color_pair(2) | curses.A_BOLD)
    center(stdscr, 20, "[N] = SÍ - Hay defectos", curses.color_pair(3) | curses.A_BOLD)
    stdscr.refresh()
    
    key = stdscr.getch()
    return "OK" if key in [32, 10, 13] else "FAIL"

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
    Test de teclado usando pynput para detección correcta del layout
    Detecta teclas físicas respetando la configuración del sistema
    """
    # Verificar si pynput está disponible
    try:
        from pynput import keyboard
    except ImportError:
        # Fallback al método antiguo si no está pynput
        stdscr.clear()
        try:
            stdscr.addstr(10, 10, "ERROR: pynput no instalado", curses.color_pair(3))
            stdscr.addstr(12, 10, "Ejecuta: pip3 install pynput")
            stdscr.addstr(14, 10, "[ENTER] para continuar")
            stdscr.refresh()
            stdscr.getch()
        except: pass
        return "FAIL"
    
    # Layout del teclado español (sin F10-F12 y AltGr que no se detectan bien)
    keyboard_layout = [
        ["ESC", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"],
        ["º", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "'", "¡", "BKSP"],
        ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "`", "+", "ENTER"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", "Ñ", "´", "Ç"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "-"],
        ["CTRL", "ALT", "SPACE"]
    ]
    
    pressed_keys = set()
    esc_count = 0
    running = [True]  # Usar lista para poder modificar en callback
    
    def normalize_key(key):
        """Normaliza el nombre de la tecla"""
        try:
            # Teclas con carácter
            if hasattr(key, 'char') and key.char:
                return key.char.upper()
            
            # Teclas especiales
            key_name = str(key).replace('Key.', '').upper()
            
            # Mapeos
            mappings = {
                'BACKSPACE': 'BKSP', 'RETURN': 'ENTER', 'DELETE': 'DEL',
                'ESC': 'ESC', 'SPACE': 'SPACE', 'TAB': 'TAB',
                'CAPS_LOCK': 'CAPS', 'SHIFT': 'SHIFT', 'SHIFT_R': 'SHIFT', 'SHIFT_L': 'SHIFT',
                'CTRL': 'CTRL', 'CTRL_L': 'CTRL', 'CTRL_R': 'CTRL',
                'ALT': 'ALT', 'ALT_L': 'ALT', 'ALT_R': 'ALTGR', 'ALT_GR': 'ALTGR',
            }
            
            # Teclas F
            for i in range(1, 13):
                if f'F{i}' in key_name:
                    return f'F{i}'
            
            return mappings.get(key_name, key_name)
        except:
            return None
    
    def on_press(key):
        """Callback cuando se presiona una tecla"""
        nonlocal esc_count
        try:
            normalized = normalize_key(key)
            if normalized:
                pressed_keys.add(normalized)
                
                # ESC 3 veces para salir
                if normalized == 'ESC':
                    esc_count += 1
                    if esc_count >= 3:
                        running[0] = False
                        return False
                else:
                    esc_count = 0  # Reset si no es ESC
        except:
            pass
    
    # Iniciar listener
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    
    stdscr.nodelay(True)
    stdscr.timeout(100)
    
    # Bucle principal
    while running[0]:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        # Header
        try:
            stdscr.addstr(0, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
            stdscr.addstr(1, 0, " TEST DE TECLADO (PYNPUT) ".center(w-1), curses.color_pair(4)|curses.A_BOLD)
            stdscr.addstr(2, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
        except: pass
        
        # Instrucciones
        try:
            stdscr.addstr(4, 2, "INSTRUCCIONES: Pulsa TODAS las teclas", curses.A_BOLD | curses.color_pair(6))
            stdscr.addstr(5, 2, "[ESC] x3 para terminar", curses.A_DIM)
        except: pass
        
        # Contador
        try:
            stdscr.addstr(7, 2, f"═══ TECLAS DETECTADAS: {len(pressed_keys)} ═══", 
                         curses.color_pair(2) | curses.A_BOLD)
        except: pass
        
        # Info ESC
        if esc_count > 0:
            try:
                stdscr.addstr(8, 2, f"ESC presionado {esc_count}/3", curses.color_pair(6) | curses.A_BLINK)
            except: pass
        
        # Dibujar teclado
        start_y = 10
        for row_idx, row in enumerate(keyboard_layout):
            x = 2
            y = start_y + row_idx * 2
            
            for key in row:
                attr = curses.color_pair(5) | curses.A_BOLD if key in pressed_keys else curses.color_pair(1)
                try:
                    key_display = f"[{key:^5s}]"
                    stdscr.addstr(y, x, key_display, attr)
                    x += len(key_display) + 1
                except: pass
        
        stdscr.refresh()
        time.sleep(0.1)
    
    stdscr.nodelay(False)
    listener.stop()
    
    # Resumen
    stdscr.clear()
    try:
        stdscr.addstr(0, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(1, 0, " TEST COMPLETADO ".center(w-1), curses.color_pair(4)|curses.A_BOLD)
        stdscr.addstr(2, 0, "=" * (w-1), curses.color_pair(4)|curses.A_BOLD)
        
        stdscr.addstr(8, 20, f"TECLAS DETECTADAS: {len(pressed_keys)}", curses.color_pair(2) | curses.A_BOLD)
        
        if len(pressed_keys) >= 35:
            stdscr.addstr(10, 30, "✓ TEST PASADO", curses.color_pair(2) | curses.A_BOLD)
            result = "OK"
        else:
            stdscr.addstr(10, 25, f"✗ Solo {len(pressed_keys)} teclas (mínimo 35)", curses.color_pair(3))
            result = "FAIL"
        
        stdscr.addstr(12, 20, "Continuando automáticamente...", curses.A_DIM)
        stdscr.refresh()
        time.sleep(2)
    except: pass
    
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

def show_navigation_help(stdscr):
    """Muestra ayuda de navegación en la parte inferior"""
    h, w = stdscr.getmaxyx()
    try:
        help_text = "[SPACE/ENTER]=Siguiente | [B]=Atrás | [R]=Repetir | [Q]=Salir"
        stdscr.addstr(h-1, 2, help_text, curses.color_pair(6) | curses.A_DIM)
    except: pass

def wait_for_navigation(stdscr):
    """
    Espera input de navegación del usuario
    Retorna: 'next', 'back', 'repeat', 'quit'
    """
    show_navigation_help(stdscr)
    stdscr.refresh()
    
    while True:
        key = stdscr.getch()
        
        # Siguiente (SPACE o ENTER)
        if key in [32, 10, 13]:
            return 'next'
        
        # Atrás (B)
        elif key in [ord('b'), ord('B')]:
            return 'back'
        
        # Repetir (R)
        elif key in [ord('r'), ord('R')]:
            return 'repeat'
        
        # Salir (Q)
        elif key in [ord('q'), ord('Q')]:
            return 'quit'

def main(stdscr):
    stdscr = init_ui()
    try: 
        if int(datetime.datetime.now().year)<2024: subprocess.run('date -s "2025-01-01 12:00:00"',shell=True)
    except: pass
    
    # Datos persistentes
    tech = None
    hw = None
    results = {
        'auto': None,
        'audio': None,
        'visual': None,
        'keyboard': None,
        'wipe': None
    }
    
    # Definir secuencia de pruebas
    tests = [
        {'name': 'WiFi', 'func': lambda: screen_wifi_logic(stdscr), 'skippable': True},
        {'name': 'Técnico', 'func': lambda: screen_tech(stdscr), 'result_var': 'tech'},
        {'name': 'Hardware', 'func': lambda: (get_hw(), screen_hw_info(stdscr, hw, tech))[0], 'result_var': 'hw'},
        {'name': 'Auto-Tests', 'func': lambda: screen_auto(stdscr), 'result_key': 'auto'},
        {'name': 'Speakers', 'func': lambda: screen_speakers(stdscr), 'result_key': 'speakers'},
        {'name': 'Micrófono', 'func': lambda: screen_microphone(stdscr), 'result_key': 'microphone'},
        {'name': 'Visual', 'func': lambda: screen_visual(stdscr), 'result_key': 'visual'},
        {'name': 'Teclado', 'func': lambda: screen_keyboard_vis(stdscr), 'result_key': 'keyboard'},
        {'name': 'Wipe', 'func': lambda: screen_wipe(stdscr), 'result_key': 'wipe'},
    ]
    
    current_test = 0
    
    while current_test < len(tests):
        test = tests[current_test]
        
        try:
            # Ejecutar prueba
            if test['name'] == 'WiFi':
                screen_wifi_logic(stdscr)
                
            elif test['name'] == 'Técnico':
                tech = screen_tech(stdscr)
                
            elif test['name'] == 'Hardware':
                hw = get_hw()
                screen_hw_info(stdscr, hw, tech)
                
            elif test['name'] == 'Auto-Tests':
                results['auto'] = screen_auto(stdscr)
                
            elif test['name'] == 'Speakers':
                results['speakers'] = screen_speakers(stdscr)
                
            elif test['name'] == 'Micrófono':
                results['microphone'] = screen_microphone(stdscr)
                
            elif test['name'] == 'Visual':
                results['visual'] = screen_visual(stdscr)
                
            elif test['name'] == 'Teclado':
                results['keyboard'] = screen_keyboard_vis(stdscr)
                
            elif test['name'] == 'Wipe':
                # Mostrar navegación antes de wipe
                stdscr.clear()
                draw_header(stdscr, "NAVEGACIÓN")
                try:
                    stdscr.addstr(10, 10, "¿Deseas ejecutar el borrado de disco (WIPE)?", curses.A_BOLD)
                    stdscr.addstr(12, 10, "[SPACE/ENTER] = Ejecutar WIPE")
                    stdscr.addstr(13, 10, "[B] = Volver atrás (saltar WIPE)")
                    stdscr.addstr(14, 10, "[N] = Saltar WIPE y continuar")
                    stdscr.refresh()
                except: pass
                
                action = wait_for_navigation(stdscr)
                
                if action == 'back':
                    current_test -= 1
                    continue
                elif action == 'next':
                    results['wipe'] = "SKIP"
                    current_test += 1
                    continue
                else:
                    results['wipe'] = screen_wipe(stdscr)
            
            # Avanzar automáticamente a siguiente prueba (sin navegación)
            current_test += 1
            
        except Exception as e:
            # Error en prueba, mostrar y permitir navegación
            stdscr.clear()
            try:
                stdscr.addstr(10, 10, f"Error en {test['name']}: {str(e)}", curses.color_pair(3))
                stdscr.addstr(12, 10, "[SPACE/ENTER] = Continuar")
                stdscr.addstr(13, 10, "[B] = Volver atrás")
                stdscr.addstr(14, 10, "[R] = Repetir")
                stdscr.refresh()
            except: pass
            
            action = wait_for_navigation(stdscr)
            
            if action == 'back':
                current_test -= 1
            elif action == 'repeat':
                pass  # No cambiar current_test
            else:
                current_test += 1
    
    # Calcular resultado final
    final = "PASS"
    if results.get('speakers') != "OK": final = "FAIL"
    if results.get('microphone') != "OK": final = "FAIL"
    if results['visual'] == "FAIL": final = "FAIL"
    if results['keyboard'] != "OK": final = "FAIL"
    if results['wipe'] == "FAIL": final = "FAIL"
    if results['auto']:
        for d in results['auto'].get("smart", []):
            if d["st"] == "FAIL": 
                final = "FAIL"
    
    # Enviar a servidor
    ok, msg = send_to_server(hw, final, results, results['wipe'], tech)
    
    # Pantalla final
    stdscr.clear()
    draw_header(stdscr, "INFORME FINAL")
    r=4
    safe_print(stdscr, r, 2, f"RESULTADO: {final}", curses.color_pair(2 if final=="PASS" else 3)); r+=2
    safe_print(stdscr, r, 2, f"SERVIDOR: {'ENVIADO' if ok else msg}", curses.color_pair(2 if ok else 3)); r+=2
    
    if shutil.which("qrencode"):
        try:
            qr = subprocess.run(["qrencode","-t","ASCII",f"{hw['serial']}|{final}"],capture_output=True,text=True).stdout.splitlines()
            for l in qr: safe_print(stdscr, r, 4, l); r+=1
        except: pass
    
    h,w=stdscr.getmaxyx()
    safe_print(stdscr, h-1, 2, "[Q] Apagar")
    while stdscr.getch() not in [ord('q'),ord('Q')]: pass
    os.system("poweroff")

if __name__ == "__main__":
    if os.geteuid()!=0: print("ROOT REQUIRED"); exit()
    try: curses.wrapper(main)
    except Exception as e: print(e)