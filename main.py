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
    y_adjusted = y + 2 if y > 2 else y
    if y_adjusted < h and x < w:
        try: 
            if large:
                # Texto más grande usando espacios adicionales
                txt_large = " ".join(txt)
                stdscr.addstr(y_adjusted, x, txt_large[:w-x-1], attr)
            else:
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
    stdscr.clear(); draw_header(stdscr, "IDENTIFICACIÓN")
    center(stdscr, 8, "Nombre del Técnico:"); curses.echo(); curses.curs_set(1)
    h, w = stdscr.getmaxyx(); stdscr.move(10, w//2 - 10)
    try: name = stdscr.getstr().decode()
    except: name = "Unknown"
    curses.noecho(); curses.curs_set(0)
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
    stdscr.clear(); draw_header(stdscr, "TEST USB")
    base_usb = run_cmd("lsusb").splitlines()
    count_base = len(base_usb)
    
    center(stdscr, 6, "ESTADO: Escaneando...")
    center(stdscr, 8, f"Dispositivos iniciales: {count_base}")
    center(stdscr, 12, ">>> CONECTA AHORA UN RATÓN/PENDRIVE <<<", curses.color_pair(4) | curses.A_BLINK)
    center(stdscr, 14, "[S]altar si no tienes nada")
    stdscr.refresh()
    stdscr.nodelay(True)
    
    start = time.time()
    detected = False
    
    while time.time() - start < 15:
        curr_usb = run_cmd("lsusb").splitlines()
        if len(curr_usb) > count_base:
            detected = True
            break
        try:
            if stdscr.getch() in [ord('s'), ord('S')]: break
        except: pass
        time.sleep(0.5)
        
    stdscr.nodelay(False)
    if detected:
        center(stdscr, 16, "✔ DISPOSITIVO DETECTADO", curses.color_pair(2)); time.sleep(1.5); return "OK"
    else:
        center(stdscr, 16, "✖ SIN CAMBIOS", curses.color_pair(3)); time.sleep(1.5); return "FAIL"

def screen_auto(stdscr):
    stdscr.clear(); draw_header(stdscr, "AUTO TESTS")
    r=3
    # Bateria
    st, msg = test_battery()
    col = curses.color_pair(2 if st in ["OK","NO_BATTERY"] else 3)
    safe_print(stdscr, r, 2, "BATERÍA:"); safe_print(stdscr, r, 12, f"{st} ({msg})", col)
    res={"bat":{"st":st,"msg":msg}}; r+=2
    
    # Touch
    tp = check_touchpad()
    safe_print(stdscr, r, 2, "TOUCHPAD:"); safe_print(stdscr, r, 12, tp, curses.color_pair(2 if tp!="NO DETECTADO" else 3))
    res["touch"]=tp; r+=2
    
    # USB Interactivo
    usb_st = screen_usb_interactive(stdscr)
    stdscr.clear(); draw_header(stdscr, "AUTO TESTS")
    safe_print(stdscr, 3, 2, "BATERÍA:"); safe_print(stdscr, 3, 12, f"{st} ({msg})", col)
    safe_print(stdscr, 5, 2, "TOUCHPAD:"); safe_print(stdscr, 5, 12, tp, curses.color_pair(2 if tp!="NO DETECTADO" else 3))
    col_usb = curses.color_pair(2 if usb_st=="OK" else 3)
    safe_print(stdscr, 7, 2, "USB PORT:"); safe_print(stdscr, 7, 12, usb_st, col_usb)
    res["usb"]=usb_st; r=9
    
    # Discos
    safe_print(stdscr, r, 2, "SMART CHECK:", curses.A_BOLD); r+=1
    real_disks = get_real_disks(); sm=[]
    if not real_disks: safe_print(stdscr, r, 4, "No detectados."); r+=1
    for d in real_disks:
        s="OK"; o=run_cmd(f"smartctl -H /dev/{d['dev']}") if check_dependency("smartctl") else "SKIP"
        if "PASSED" not in o and "OK" not in o and o!="SKIP": s="FAIL"
        col=curses.color_pair(2 if s=="OK" else 3)
        safe_print(stdscr, r, 4, f"[{d['dev']}] {s}", col)
        sm.append({"dev":d['dev'],"st":s}); r+=1
    res["smart"]=sm
    
    center(stdscr, r+1, "[ENTER]"); 
    while stdscr.getch() not in [10,13]: pass
    return res

def screen_audio_adv(stdscr):
    res={"L":"FAIL","R":"FAIL","MIC":"FAIL"}
    
    # Pantalla inicial - Reset audio
    stdscr.clear()
    draw_header(stdscr, "AUDIO CHECK")
    center(stdscr, 6, "Inicializando drivers de audio...", curses.A_BOLD)
    stdscr.refresh()
    fix_audio_mixer()
    time.sleep(1)
    
    # Primera prueba de audio
    stdscr.clear()
    draw_header(stdscr, "AUDIO CHECK")
    center(stdscr, 6, "==================", curses.A_BOLD)
    center(stdscr, 7, "  🔊 ALTAVOCES  ", curses.A_BOLD)
    center(stdscr, 8, "==================", curses.A_BOLD)
    center(stdscr, 10, "Reproduciendo sonido de prueba...", curses.A_BLINK)
    stdscr.refresh()
    time.sleep(1)
    subprocess.run("speaker-test -D plughw:0,0 -t sine -f 440 -l 1 -p 2000", shell=True, stderr=subprocess.DEVNULL)
    
    stdscr.clear()
    draw_header(stdscr, "AUDIO CHECK")
    center(stdscr, 8, "¿Se escuchó algo?", curses.A_BOLD)
    center(stdscr, 10, "[S] SI    /    [N] NO")
    stdscr.refresh()
    
    if stdscr.getch() in [ord('s'),ord('S')]: 
        res["L"]="OK"
    else:
        # Prueba alternativa
        stdscr.clear()
        draw_header(stdscr, "AUDIO CHECK")
        center(stdscr, 6, "Probando salida alternativa...", curses.A_BLINK)
        stdscr.refresh()
        time.sleep(1)
        subprocess.run("speaker-test -D plughw:1,0 -t sine -f 440 -l 1 -p 2000", shell=True, stderr=subprocess.DEVNULL)
        
        stdscr.clear()
        draw_header(stdscr, "AUDIO CHECK")
        center(stdscr, 8, "¿Se escuchó ahora?", curses.A_BOLD)
        center(stdscr, 10, "[S] SI    /    [N] NO")
        stdscr.refresh()
        
        if stdscr.getch() in [ord('s'),ord('S')]: 
            res["L"]="OK"
    
    res["R"] = res["L"]
    
    # Prueba de micrófono
    stdscr.clear()
    draw_header(stdscr, "MICRÓFONO")
    center(stdscr, 6, "=====================", curses.A_BOLD)
    center(stdscr, 7, "  🎙️ MICRÓFONO  ", curses.A_BOLD)
    center(stdscr, 8, "=====================", curses.A_BOLD)
    center(stdscr, 11, "¡Di algo FUERTE durante 2 segundos!", curses.A_BLINK | curses.A_BOLD)
    center(stdscr, 13, "Iniciando grabación...")
    stdscr.refresh()
    time.sleep(1)
    
    st, msg = test_microphone()
    
    stdscr.clear()
    draw_header(stdscr, "MICRÓFONO")
    col = curses.color_pair(2 if st=="OK" else 3)
    center(stdscr, 8, f"Resultado: {msg}", col | curses.A_BOLD)
    center(stdscr, 11, "[ENTER] Continuar")
    stdscr.refresh()
    stdscr.getch()
    res["MIC"]=st
    
    return "OK" if res["L"]=="OK" and res["MIC"]=="OK" else "FAIL"

def screen_visual(stdscr):
    cols=[(curses.COLOR_RED,"ROJO"),(curses.COLOR_GREEN,"VERDE"),(curses.COLOR_BLUE,"AZUL"),(curses.COLOR_WHITE,"BLANCO")]
    
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL")
    center(stdscr, 10, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  PRUEBA DE PANTALLA Y COLORES  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 15, "Presiona cualquier tecla para comenzar", curses.color_pair(6))
    stdscr.refresh()
    stdscr.getch()
    
    for c,n in cols:
        curses.init_pair(20,curses.COLOR_WHITE,c)
        stdscr.bkgd(' ',curses.color_pair(20))
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        # Texto más grande en el centro
        center(stdscr, h//2 - 2, "═══════════════════════════════════", curses.A_BOLD)
        center(stdscr, h//2 - 1, f"        COLOR: {n}        ", curses.A_BOLD)
        center(stdscr, h//2, "═══════════════════════════════════", curses.A_BOLD)
        center(stdscr, h//2 + 3, "¿Se ve este color correctamente?", curses.A_BOLD)
        center(stdscr, h//2 + 5, "[ Presiona cualquier tecla ]")
        stdscr.refresh()
        stdscr.getch()
    
    stdscr.bkgd(' ',curses.color_pair(1))
    stdscr.clear()
    draw_header(stdscr,"TEST VISUAL - RESULTADO")
    center(stdscr, 10, "════════════════════════════════", curses.A_BOLD)
    center(stdscr, 11, "  ¿HAY DEFECTOS EN LA PANTALLA?  ", curses.A_BOLD)
    center(stdscr, 12, "════════════════════════════════", curses.A_BOLD)
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
    stdscr.clear()
    draw_header(stdscr, "SELECCIÓN TECLADO")
    center(stdscr, 8, "==========================================", curses.A_BOLD)
    center(stdscr, 9, "  SELECCIONA TU DISTRIBUCIÓN DE TECLADO  ", curses.A_BOLD)
    center(stdscr, 10, "==========================================", curses.A_BOLD)
    center(stdscr, 13, "[1] Teclado ESPAÑOL", curses.color_pair(6) | curses.A_BOLD)
    center(stdscr, 15, "[2] Teclado INGLÉS (US)", curses.color_pair(6) | curses.A_BOLD)
    stdscr.refresh()
    
    layout = "US" if stdscr.getch()==ord('2') else "ES"
    rows = KEY_LAYOUTS[layout]
    pressed = set()
    stdscr.nodelay(True); stdscr.timeout(100)
    
    while True:
        stdscr.clear()
        draw_header(stdscr, f"TEST TECLADO ({layout})")
        
        # Instrucciones más grandes
        safe_print(stdscr, 4, 4, "INSTRUCCIONES:", curses.A_BOLD | curses.color_pair(6))
        safe_print(stdscr, 5, 4, "• Pulsa todas las teclas del teclado")
        safe_print(stdscr, 6, 4, "• Las teclas pulsadas se pondrán VERDES")
        safe_print(stdscr, 7, 4, "• Presiona [F10] para terminar")
        
        # Teclado virtual con más espacio
        start_y = 10
        for i, r in enumerate(rows):
            cx = 6
            for key in r.split():
                attr = curses.color_pair(5) | curses.A_BOLD if key in pressed else curses.color_pair(1)
                # Aumentar el tamaño de cada tecla
                key_display = f"[ {key} ]"
                safe_print(stdscr, start_y+i*3, cx, key_display, attr)
                cx += len(key_display) + 2
        
        # Contador de teclas presionadas
        safe_print(stdscr, start_y + len(rows)*3 + 2, 4, 
                  f"Teclas presionadas: {len(pressed)}", 
                  curses.color_pair(2) | curses.A_BOLD)
        
        stdscr.refresh()
        
        try: k=stdscr.getch()
        except: k=-1
        
        if k!=-1:
            if k==curses.KEY_F10: break
            char = map_key(k)
            if char: 
                pressed.add(char)
            
    stdscr.nodelay(False)
    return "OK" if len(pressed)>3 else "FAIL"

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