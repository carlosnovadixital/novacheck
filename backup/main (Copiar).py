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

# --- CONFIGURACIÓN ---
SERVER_BASE = "https://check.novadixital.es"
API_ENDPOINT = f"{SERVER_BASE}/api/report.php"
APP_TITLE = "NOVACHECK AGENT v16 (Smart Filter)"

# ==========================================
# 1. UTILIDADES BASE
# ==========================================

def run_cmd(cmd):
    try: return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode().strip()
    except: return ""

def leer_archivo(ruta):
    try:
        with open(ruta, 'r') as f: return f.read().strip()
    except: return "N/A"

def check_internet():
    return subprocess.call(["ping", "-c", "1", "8.8.8.8"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

# ==========================================
# 2. AUDIO & HARDWARE
# ==========================================

def fix_audio_universal():
    try:
        subprocess.run("alsactl init", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for c in [0, 1, 2]:
            subprocess.run(f"amixer -c {c} set 'Auto-Mute Mode' Disabled", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            targets = ["Master", "Speaker", "Headphone", "PCM", "Front", "Surround", "LFE"]
            for t in targets:
                subprocess.run(f"amixer -c {c} set '{t}' 100% unmute", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f"amixer -c {c} set '{t}' on", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except: pass

def play_noise_universal():
    subprocess.run("timeout 1 cat /dev/urandom | aplay -f cd", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("timeout 1 cat /dev/urandom | aplay -f cd -D plughw:0,0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("timeout 1 cat /dev/urandom | aplay -f cd -D plughw:1,0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    
    # Listar discos para Info General (Solo nombres)
    ls = run_cmd("lsblk -d -n -o NAME,SIZE,TYPE,TRAN")
    if ls:
        for l in ls.splitlines():
            # Filtro visual básico
            if "disk" in l and "zram" not in l and "loop" not in l:
                parts = l.split()
                hw["discos"].append(f"{parts[0]} ({parts[1]})")
    return hw

def get_real_disks():
    """FILTRO AVANZADO: Devuelve solo discos físicos reales (SATA/NVMe)"""
    disks = []
    # NAME, TYPE (disk/rom), TRAN (sata/nvme/usb), MODEL
    raw = run_cmd("lsblk -d -n -o NAME,TYPE,TRAN,MODEL")
    for line in raw.splitlines():
        if not line.strip(): continue
        
        # Ejemplo: sda disk sata Samsung_SSD_860
        # Ejemplo: sr0 rom sata DVD-RAM
        # Ejemplo: zram0 disk
        
        parts = line.split()
        name = parts[0]
        dtype = parts[1] if len(parts) > 1 else ""
        trans = parts[2].lower() if len(parts) > 2 else ""
        model = " ".join(parts[3:]) if len(parts) > 3 else name
        
        # 1. Ignorar ROM (CD/DVD), Loop, Ramdisk
        if dtype != "disk": continue
        if name.startswith("loop") or name.startswith("zram") or name.startswith("sr"): continue
        
        # 2. Ignorar USB (El pendrive de arranque)
        if "usb" in trans: continue
        
        disks.append({"dev": name, "model": model, "type": trans})
        
    return disks

def test_battery():
    path = "/sys/class/power_supply/"
    bat = None
    if os.path.exists(path):
        for d in os.listdir(path):
            if d.startswith("BAT"): bat = os.path.join(path, d); break
    if not bat: return "NO_BATTERY", "No detectada"
    try:
        def g(n): p=os.path.join(bat,n); return int(open(p).read()) if os.path.exists(p) else None
        fd = g("energy_full_design") or g("charge_full_design")
        fc = g("energy_full") or g("charge_full")
        if fd and fc and fd > 0:
            h = (fc/fd)*100
            st = "OK" if h > 40 else "POOR"
            return st, f"{h:.0f}% Vida"
    except: pass
    return "OK", "Detectada (Sin %)"

# ==========================================
# 3. INTERFAZ GRÁFICA
# ==========================================

def init_ui():
    curses.initscr(); curses.start_color(); curses.use_default_colors(); curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)

def draw_header(stdscr, sub=""):
    h, w = stdscr.getmaxyx()
    txt = f" {APP_TITLE} | {sub}"
    bar = txt + " " * (w - len(txt))
    try: stdscr.addstr(0, 0, bar[:w-1], curses.color_pair(4)|curses.A_BOLD)
    except: pass

def safe_print(stdscr, y, x, txt, attr=0):
    h, w = stdscr.getmaxyx()
    if y < h and x < w:
        try: 
            max_len = w - x - 1
            if len(txt) > max_len: txt = txt[:max_len]
            stdscr.addstr(y, x, txt, attr)
        except: pass

def center(stdscr, y, txt, attr=0):
    h, w = stdscr.getmaxyx()
    x = max(0, int((w - len(txt)) / 2))
    safe_print(stdscr, y, x, txt, attr)

# --- PANTALLAS ---

def screen_wifi(stdscr):
    stdscr.nodelay(False)
    stdscr.clear(); draw_header(stdscr, "RED")
    center(stdscr, 10, "Verificando conexión..."); stdscr.refresh()
    if check_internet():
        center(stdscr, 12, "✔ ONLINE", curses.color_pair(2)); time.sleep(1); return
    while True:
        stdscr.clear(); draw_header(stdscr, "WIFI SCAN"); center(stdscr, 2, "Escaneando...")
        try:
            raw = run_cmd("nmcli -f SSID,SIGNAL dev wifi list | awk 'NR>1 {print $0}'")
            nets = []
            for l in raw.splitlines():
                if not l.strip(): continue
                p = l.rsplit(None, 1)
                if len(p)==2 and p[0]!="--": nets.append(p)
            u_nets = list({s:sig for s,sig in nets}.items())
        except: u_nets = []

        if not u_nets:
            center(stdscr, 5, "Sin redes. [R]etry [S]kip")
            if stdscr.getch() in [ord('s'), ord('S')]: return
            continue
        idx = 0
        while True:
            stdscr.clear(); draw_header(stdscr, "ELIGE WIFI")
            safe_print(stdscr, 2, 2, "↑/↓ Navegar, ENTER Conectar, S Saltar")
            h, w = stdscr.getmaxyx(); max_rows = h - 5
            for i, (ssid, sig) in enumerate(u_nets):
                if i >= max_rows: break
                attr = curses.A_REVERSE if i==idx else 0
                safe_print(stdscr, 4+i, 2, f"{ssid} ({sig})", attr)
            k = stdscr.getch()
            if k == curses.KEY_UP and idx > 0: idx -= 1
            elif k == curses.KEY_DOWN and idx < len(u_nets)-1: idx += 1
            elif k in [ord('s'), ord('S')]: return
            elif k in [10, 13]:
                target = u_nets[idx][0]
                stdscr.clear(); draw_header(stdscr, f"PASS: {target}")
                center(stdscr, 8, "Password:"); curses.echo(); curses.curs_set(1)
                stdscr.move(10, w//2 - 10)
                try: pwd = stdscr.getstr().decode()
                except: pwd = ""
                curses.noecho(); curses.curs_set(0)
                if not pwd: break
                center(stdscr, 12, "Conectando...", curses.A_BLINK); stdscr.refresh()
                if subprocess.call(f"nmcli dev wifi connect '{target}' password '{pwd}'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
                    center(stdscr, 14, "OK", curses.color_pair(2)); time.sleep(1); return
                else: center(stdscr, 14, "ERROR", curses.color_pair(3)); time.sleep(1); break

def screen_tech(stdscr):
    stdscr.clear(); draw_header(stdscr, "OPERARIO")
    center(stdscr, 8, "Nombre del Técnico / ID:")
    curses.echo(); curses.curs_set(1); h, w = stdscr.getmaxyx(); stdscr.move(10, w//2 - 10)
    try: name = stdscr.getstr().decode()
    except: name = "Unknown"
    curses.noecho(); curses.curs_set(0)
    return name if name else "Anónimo"

def screen_hw(stdscr, hw, tech):
    stdscr.clear(); draw_header(stdscr, "INFO")
    r = 2
    safe_print(stdscr, r, 2, f"TECH: {tech}", curses.color_pair(4)); r+=2
    for k,v in [("MOD",hw["modelo"]),("SN",hw["serial"]),("CPU",hw["cpu"]),("RAM",hw["ram"])]:
        safe_print(stdscr, r, 2, f"{k}: {v}"); r+=1
    r+=1; safe_print(stdscr, r, 2, "DISCOS:", curses.A_BOLD); r+=1
    for d in hw["discos"]: safe_print(stdscr, r, 4, d); r+=1
    center(stdscr, r+2, "[ENTER] Iniciar Tests"); 
    while stdscr.getch() not in [10,13]: pass

def screen_auto(stdscr):
    stdscr.clear(); draw_header(stdscr, "AUTO TESTS")
    r = 3
    # Bateria
    st, msg = test_battery()
    col = curses.color_pair(2 if st in ["OK","NO_BATTERY"] else 3)
    safe_print(stdscr, r, 2, "BAT:"); safe_print(stdscr, r, 8, f"{st} ({msg})", col)
    res_bat = {"st":st, "msg":msg}
    r += 2
    
    # DISCOS REALE (FILTRADOS)
    safe_print(stdscr, r, 2, "SMART CHECK:", curses.A_BOLD); r+=1
    real_disks = get_real_disks()
    res_smart = []
    
    if not real_disks:
        safe_print(stdscr, r, 4, "No se encontraron discos físicos.")
        r += 1
    else:
        for d in real_disks:
            dev = d["dev"]
            model = d["model"]
            s = "OK"
            if shutil.which("smartctl"):
                o = run_cmd(f"smartctl -H /dev/{dev}")
                if "PASSED" not in o and "OK" not in o: s="FAIL"
            
            # Formato bonito: [ sda ] Samsung... : OK
            col = curses.color_pair(2 if s=="OK" else 3)
            txt = f"[ {dev} ] {model[:15]} : {s}"
            safe_print(stdscr, r, 4, txt, col)
            res_smart.append({"dev":dev, "st":s})
            r += 1
            
    center(stdscr, r+2, "[ENTER]")
    while stdscr.getch() not in [10,13]: pass
    return {"bat": res_bat, "smart": res_smart}

def screen_audio(stdscr):
    stdscr.clear(); draw_header(stdscr, "AUDIO")
    center(stdscr, 5, "Configurando Audio..."); stdscr.refresh()
    fix_audio_universal(); time.sleep(0.5)
    center(stdscr, 7, "Probando Estática..."); stdscr.refresh()
    play_noise_universal()
    center(stdscr, 10, "¿Escuchaste estática/ruido?"); center(stdscr, 12, "[S] SÍ   /   [N] NO")
    return "OK" if stdscr.getch() in [ord('s'),ord('S')] else "FAIL"

def screen_visual(stdscr):
    cols=[(curses.COLOR_RED,"ROJO"),(curses.COLOR_GREEN,"VERDE"),(curses.COLOR_BLUE,"AZUL"),(curses.COLOR_WHITE,"BLANCO")]
    stdscr.clear(); draw_header(stdscr,"VISUAL"); center(stdscr,10,"Tecla cambiar color."); stdscr.getch()
    for c,n in cols:
        curses.init_pair(20,curses.COLOR_WHITE,c); stdscr.bkgd(' ',curses.color_pair(20)); stdscr.clear()
        stdscr.addstr(0,0,f" {n} ",curses.A_BOLD); stdscr.refresh(); stdscr.getch()
    stdscr.bkgd(' ',curses.color_pair(1)); stdscr.clear(); draw_header(stdscr,"VISUAL")
    center(stdscr,10,"¿Defectos?"); center(stdscr,12,"[N] NO   /   [S] SÍ")
    return "OK" if stdscr.getch() in [ord('n'),ord('N')] else "FAIL"

def screen_keyboard(stdscr):
    stdscr.nodelay(True); tests=[(ord('a'),"A"),(ord('s'),"S"),(32,"ESPACIO"),(10,"ENTER")]; r={}
    for c,n in tests:
        stdscr.clear(); draw_header(stdscr,"TECLADO"); center(stdscr,10,f"PULSA: {n}",curses.A_BOLD|curses.A_BLINK)
        st=time.time(); ok=False
        while time.time()-st<5:
            safe_print(stdscr, 12, 5, f"{5-int(time.time()-st)}s")
            try: k=stdscr.getch()
            except: k=-1
            if k!=-1 and (k==c or (n=="ENTER" and k in [10,13])): ok=True; break
            time.sleep(0.05)
        r[n]="OK" if ok else "FAIL"
    stdscr.nodelay(False); return r

def screen_wipe(stdscr):
    stdscr.clear(); draw_header(stdscr, "BORRADO")
    # Usamos el filtro inteligente para encontrar el disco principal
    real_disks = get_real_disks()
    if not real_disks: center(stdscr, 10, "Sin disco interno."); stdscr.getch(); return "SKIP"
    
    target = real_disks[0]["dev"] # Tomamos el primero de la lista limpia
    center(stdscr,10,f"TARGET: {target}"); center(stdscr,12,"Escribe 'SI':")
    curses.echo(); h,w=stdscr.getmaxyx(); stdscr.move(14, w//2 - 5)
    ans = stdscr.getstr().decode(); curses.noecho()
    if ans.upper() != "SI": return "SKIP"
    center(stdscr, 16, "BORRANDO...", curses.A_BLINK); stdscr.refresh()
    subprocess.run(f"shred -n 1 -z /dev/{target}", shell=True, stderr=subprocess.DEVNULL)
    return "OK"

def main(stdscr):
    init_ui(); screen_wifi(stdscr)
    tech_name = screen_tech(stdscr)
    hw = get_hw()
    
    try:
        ping_data = {"status":"RUNNING", "hw":hw, "tech":tech_name}
        req = urllib.request.Request(API_ENDPOINT, data=json.dumps(ping_data).encode(), headers={'Content-Type':'application/json'})
        ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        urllib.request.urlopen(req, context=ctx, timeout=5)
    except: pass

    ra = screen_auto(stdscr)
    rs = screen_audio(stdscr)
    rv = screen_visual(stdscr)
    rk = screen_keyboard(stdscr)
    rw = screen_wipe(stdscr)
    
    kbd_fails = sum(1 for v in rk.values() if v == "FAIL")
    final = "PASS" if (rs=="OK" and rw!="FAIL" and rv!="FAIL" and kbd_fails==0) else "FAIL"
    
    # Comprobar si falló algún disco
    for d in ra.get("smart", []):
        if d["st"] == "FAIL": final = "FAIL"

    srv_msg = "Error Envío"
    try:
        pl = {"hw": hw, "tech": tech_name, "st": final, "res": {"auto": ra, "aud": rs, "vis": rv, "kbd": rk, "wipe": rw}}
        req = urllib.request.Request(API_ENDPOINT, data=json.dumps(pl).encode(), headers={'Content-Type':'application/json'})
        ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r: srv_msg = f"OK ({r.getcode()})"
    except Exception as e: srv_msg = str(e)[:15]

    stdscr.clear(); draw_header(stdscr, "FINAL")
    r = 4
    safe_print(stdscr, r, 2, f"RES: {final}", curses.color_pair(2 if final=="PASS" else 3)); r+=2
    safe_print(stdscr, r, 2, f"SRV: {srv_msg}"); r+=2
    
    if shutil.which("qrencode"):
        try:
            qr = subprocess.run(["qrencode","-t","ASCII",f"{hw['serial']}|{final}"],capture_output=True,text=True).stdout.splitlines()
            h, w = stdscr.getmaxyx()
            for l in qr:
                if r < h-2: safe_print(stdscr, r, 4, l); r+=1
        except: pass
    
    h, w = stdscr.getmaxyx()
    safe_print(stdscr, h-1, 2, "[Q] Apagar")
    while stdscr.getch() not in [ord('q'), ord('Q')]: pass
    os.system("poweroff")

if __name__ == "__main__":
    if os.geteuid()!=0: print("ROOT REQUIRED"); exit()
    try: curses.wrapper(main)
    except Exception as e: print(e)