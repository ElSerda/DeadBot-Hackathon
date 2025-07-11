import os
import sys
import datetime
import pprint
import json

from colorama import Fore, Style, init as colorama_init

import plugin

colorama_init()

# --- Helpers

def banner(title):
    print("\n" + "="*10 + f" {title} " + "="*10)

def highlight(msg, level="info"):
    if "ALERTE" in msg or "CRITIQUE" in msg or level == "error":
        return Fore.RED + msg + Style.RESET_ALL
    elif "idle" in msg or "aucun souci" in msg or level == "ok":
        return Fore.GREEN + msg + Style.RESET_ALL
    elif "normale" in msg or "mi-charge" in msg:
        return Fore.YELLOW + msg + Style.RESET_ALL
    return msg

def format_diag(label, diag, log_list, scenario=""):
    d = dict(diag) if isinstance(diag, dict) else {"message": str(diag)}
    msg = d.get("diagnostic", d.get("message", "N/A"))
    status = "✅" if d.get("success", False) else "❌"
    # Print
    print(f"\n{Style.BRIGHT}{label}{Style.RESET_ALL}  {status}")
    print("Diagnostic :", highlight(msg))
    # Optionally print details if error or verbose
    if not d.get("success", True):
        print(Fore.LIGHTBLACK_EX + "Details :" + Style.RESET_ALL)
        pprint.pprint(d, width=120, compact=True)
    # Log
    log_list.append({
        "scenario": scenario or label,
        "status": status,
        "diagnostic": msg,
        "result": d
    })

def ensure_logdir():
    logdir = os.path.join(os.getcwd(), "log")
    os.makedirs(logdir, exist_ok=True)
    return logdir

def export_logs(loglist):
    logdir = ensure_logdir()
    now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    txtfile = os.path.join(logdir, f"deadbot_report_{now}.txt")
    jsonfile = os.path.join(logdir, f"deadbot_report_{now}.json")

    # TXT: résumé humain
    with open(txtfile, "w", encoding="utf-8") as f:
        for log in loglist:
            f.write(f"=== {log['scenario']} ===\n")
            f.write(f"Status : {log['status']}\n")
            f.write(f"Diagnostic : {log['diagnostic']}\n")
            f.write(f"Result : {json.dumps(log['result'], ensure_ascii=False, indent=2)}\n\n")
        f.write("=== FIN REPORT DEADBOT ===\n")
    print(Fore.CYAN + f"\n[LOG] Rapport humain exporté : {txtfile}" + Style.RESET_ALL)

    # JSON: tous les détails
    with open(jsonfile, "w", encoding="utf-8") as f:
        json.dump(loglist, f, ensure_ascii=False, indent=2)
    print(Fore.CYAN + f"[LOG] Rapport JSON exporté : {jsonfile}" + Style.RESET_ALL)

# --- Début test
if __name__ == "__main__":
    loglist = []
    print("=== TESTS DEADBOT PLUGIN — REPORT LISIBLE ===")

    # --- TEST RÉEL
    banner("TEST RÉEL")
    format_diag("CPU DIAG (réel)", plugin.cpu_diag(), loglist, scenario="cpu_diag_reel")
    format_diag("GPU DIAG (réel)", plugin.gpu_diag(), loglist, scenario="gpu_diag_reel")

    # --- FAKE CPU DIAGs (Monkeypatch)
    banner("FAKE CPU DIAGS (idle, 100%, mi-charge, freq throttle, crash)")
    orig_cpu_percent = plugin.psutil.cpu_percent
    orig_cpu_freq = plugin.psutil.cpu_freq

    # Idle
    plugin.psutil.cpu_percent = lambda interval=0.2: 2.5
    plugin.psutil.cpu_freq = lambda: type("F", (), {"current": 4300, "max": 4300})()
    format_diag("CPU idle", plugin.cpu_diag(), loglist, scenario="cpu_idle")

    # Full
    plugin.psutil.cpu_percent = lambda interval=0.2: 99.9
    plugin.psutil.cpu_freq = lambda: type("F", (), {"current": 4300, "max": 4300})()
    format_diag("CPU full", plugin.cpu_diag(), loglist, scenario="cpu_full")

    # Throttle (freq basse sous charge)
    plugin.psutil.cpu_percent = lambda interval=0.2: 99.9
    plugin.psutil.cpu_freq = lambda: type("F", (), {"current": 2100, "max": 4300})()
    format_diag("CPU throttle", plugin.cpu_diag(), loglist, scenario="cpu_throttle")

    # Mi-charge
    plugin.psutil.cpu_percent = lambda interval=0.2: 55.0
    plugin.psutil.cpu_freq = lambda: type("F", (), {"current": 3500, "max": 4300})()
    format_diag("CPU mi-charge", plugin.cpu_diag(), loglist, scenario="cpu_mi_charge")

    # Crash test (attribut manquant)
    def fake_freq_crash():
        class F: pass  # no current/max
        return F()
    plugin.psutil.cpu_percent = lambda interval=0.2: 90.0
    plugin.psutil.cpu_freq = fake_freq_crash
    try:
        format_diag("CPU freq crash", plugin.cpu_diag(), loglist, scenario="cpu_freq_crash")
    except Exception as e:
        format_diag("CPU freq crash — catch", {"success": False, "message": str(e)}, loglist, scenario="cpu_freq_crash_catch")

    # Restore real CPU
    plugin.psutil.cpu_percent = orig_cpu_percent
    plugin.psutil.cpu_freq = orig_cpu_freq

    # --- FAKE GPU DIAGs (Monkeypatch)
    banner("FAKE GPU DIAGS (idle, 100%, mi-charge, VRAM saturée, temp élevée, crash)")

    if hasattr(plugin, "pynvml") and plugin.pynvml is not None:
        class FakeHandle: pass
        fake_h = FakeHandle()

        # Backup
        orig_nvmlDeviceGetHandleByIndex = plugin.pynvml.nvmlDeviceGetHandleByIndex
        orig_nvmlDeviceGetUtilizationRates = plugin.pynvml.nvmlDeviceGetUtilizationRates
        orig_nvmlDeviceGetMemoryInfo = plugin.pynvml.nvmlDeviceGetMemoryInfo
        orig_nvmlDeviceGetTemperature = plugin.pynvml.nvmlDeviceGetTemperature
        orig_nvmlDeviceGetName = plugin.pynvml.nvmlDeviceGetName
        orig_nvmlDeviceGetClockInfo = plugin.pynvml.nvmlDeviceGetClockInfo
        orig_nvmlDeviceGetMaxClockInfo = plugin.pynvml.nvmlDeviceGetMaxClockInfo
        orig_nvmlDeviceGetPowerUsage = getattr(plugin.pynvml, "nvmlDeviceGetPowerUsage", None)
        orig_nvmlDeviceGetEnforcedPowerLimit = getattr(plugin.pynvml, "nvmlDeviceGetEnforcedPowerLimit", None)
        orig_nvmlDeviceGetFanSpeed = getattr(plugin.pynvml, "nvmlDeviceGetFanSpeed", None)
        orig_nvmlDeviceGetPowerState = getattr(plugin.pynvml, "nvmlDeviceGetPowerState", None)
        orig_nvmlSystemGetDriverVersion = plugin.pynvml.nvmlSystemGetDriverVersion
        orig_nvmlDeviceGetCurrentClocksThrottleReasons = getattr(plugin.pynvml, "nvmlDeviceGetCurrentClocksThrottleReasons", None)

        # Helpers fakes
        class Util: gpu = 0; memory = 10
        class Mem: used = 1024*1024*100; total = 1024*1024*1024
        class MemSat: used = 1024*1024*1020; total = 1024*1024*1024
        class MemFake: used = -1; total = 1024

        # Patch functions
        plugin.pynvml.nvmlDeviceGetHandleByIndex = lambda i: fake_h
        plugin.pynvml.nvmlDeviceGetUtilizationRates = lambda h: Util()
        plugin.pynvml.nvmlDeviceGetMemoryInfo = lambda h: Mem()
        plugin.pynvml.nvmlDeviceGetTemperature = lambda h, t: 42
        plugin.pynvml.nvmlDeviceGetName = lambda h: b"FakeGPU"
        plugin.pynvml.nvmlDeviceGetClockInfo = lambda h, c: 900
        plugin.pynvml.nvmlDeviceGetMaxClockInfo = lambda h, c: 1800
        plugin.pynvml.nvmlDeviceGetPowerUsage = lambda h: 80000
        plugin.pynvml.nvmlDeviceGetEnforcedPowerLimit = lambda h: 80000
        plugin.pynvml.nvmlDeviceGetFanSpeed = lambda h: 33
        plugin.pynvml.nvmlDeviceGetPowerState = lambda h: 1
        plugin.pynvml.nvmlSystemGetDriverVersion = lambda: b"576.88"
        plugin.pynvml.nvmlDeviceGetCurrentClocksThrottleReasons = lambda h: 0

        # GPU idle
        Util.gpu = 2
        format_diag("GPU idle", plugin.gpu_diag(), loglist, scenario="gpu_idle")

        # GPU full
        Util.gpu = 99
        format_diag("GPU full", plugin.gpu_diag(), loglist, scenario="gpu_full")

        # GPU mi-charge
        Util.gpu = 55
        format_diag("GPU mi-charge", plugin.gpu_diag(), loglist, scenario="gpu_mi_charge")

        # VRAM saturée
        plugin.pynvml.nvmlDeviceGetMemoryInfo = lambda h: MemSat()
        Util.gpu = 40
        format_diag("GPU VRAM saturée", plugin.gpu_diag(), loglist, scenario="gpu_vram_sat")

        # Temp élevée
        plugin.pynvml.nvmlDeviceGetTemperature = lambda h, t: 90
        format_diag("GPU Temp haute", plugin.gpu_diag(), loglist, scenario="gpu_temp_haute")

        # Fausse valeur/crash (negatif)
        plugin.pynvml.nvmlDeviceGetMemoryInfo = lambda h: MemFake()
        try:
            format_diag("GPU crash valeur fausse", plugin.gpu_diag(), loglist, scenario="gpu_crash_valeur")
        except Exception as e:
            format_diag("GPU crash valeur fausse — catch", {"success": False, "message": str(e)}, loglist, scenario="gpu_crash_valeur_catch")

        # --- Simule NVML KO / driver crashé ---
        print("\n--- SIMULATEUR : Crash driver GPU (NVML KO) ---")
        orig_NVML_OK = plugin.NVML_OK
        plugin.NVML_OK = False  # Force le plugin à croire que le driver est KO
        format_diag("GPU driver crash/NVML KO", plugin.gpu_diag(), loglist, scenario="gpu_driver_crash")
        plugin.NVML_OK = orig_NVML_OK

        # --- Simule exception NVML / driver lost ---
        print("\n--- SIMULATEUR : Exception NVML (driver lost) ---")
        def raise_nvml_error(*a, **kw):
            raise Exception("NVML driver lost: device is gone")
        orig_nvmlDeviceGetHandleByIndex = plugin.pynvml.nvmlDeviceGetHandleByIndex
        plugin.pynvml.nvmlDeviceGetHandleByIndex = raise_nvml_error
        format_diag("GPU exception driver lost", plugin.gpu_diag(), loglist, scenario="gpu_nvml_driver_lost")
        plugin.pynvml.nvmlDeviceGetHandleByIndex = orig_nvmlDeviceGetHandleByIndex

            # === BATCH SCÉNARIOS GPU CROWD/EXTREMES ===
    banner("BATCH SCÉNARIOS GPU EXTREMES (crowd QA hackathon)")
    # Helpers généraux pour reset/fake
    def set_gpu(fake_util, fake_mem, fake_temp, fake_clock, fake_max_clock, fake_power, fake_power_limit, fake_fan, fake_throttle, fake_driver=True, fake_name=None, pstate=1):
        plugin.pynvml.nvmlDeviceGetUtilizationRates = lambda h: type("U", (), {"gpu": fake_util, "memory": 10})()
        plugin.pynvml.nvmlDeviceGetMemoryInfo = lambda h: type("M", (), {"used": fake_mem, "total": 1024*1024*1024})()
        plugin.pynvml.nvmlDeviceGetTemperature = lambda h, t: fake_temp
        plugin.pynvml.nvmlDeviceGetClockInfo = lambda h, c: fake_clock
        plugin.pynvml.nvmlDeviceGetMaxClockInfo = lambda h, c: fake_max_clock
        plugin.pynvml.nvmlDeviceGetPowerUsage = lambda h: fake_power
        plugin.pynvml.nvmlDeviceGetEnforcedPowerLimit = lambda h: fake_power_limit
        plugin.pynvml.nvmlDeviceGetFanSpeed = lambda h: fake_fan
        plugin.pynvml.nvmlDeviceGetCurrentClocksThrottleReasons = lambda h: fake_throttle
        plugin.pynvml.nvmlDeviceGetPowerState = lambda h: pstate
        plugin.pynvml.nvmlDeviceGetName = lambda h: (fake_name or b"FakeGPU")
        if fake_driver:
            plugin.pynvml.nvmlSystemGetDriverVersion = lambda: b"576.88"
        else:
            plugin.pynvml.nvmlSystemGetDriverVersion = lambda: Exception("No driver!")

    scenarios = [
        #   (label,          gpu%,  vram(MB), temp, clk, maxclk, power, pwlim, fan, throttle, driverOK, name, pstate)
        ("Idle pur",         3,     80,      35,   500, 1800,  30000, 80000, 33, 0, True, b"FakeGPU", 1),
        ("Mi-charge",        55,    400,     60,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1),
        ("Full",             99,    600,     75,   1800,1800,  70000, 80000, 80, 0, True, b"FakeGPU", 1),
        ("Throttling (power)",99,   600,     70,   1000,1800,  80000, 80000, 70, 0x04, True, b"FakeGPU", 1),
        ("Throttling (thermal)",99, 600,     90,   900, 1800,  70000, 80000, 95, 0x40, True, b"FakeGPU", 1),
        ("Power limit only", 80,    500,     65,   1700,1800,  80000, 80000, 70, 0, True, b"FakeGPU", 1),
        ("Temp élevée",      50,    400,     95,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1),
        ("VRAM saturée",     60,    1024*1024*990,55, 1400,1800,60000,80000,60,0,True,b"FakeGPU",1),
        ("Throttle reason multi",95,600,70,1000,1800,80000,80000,70,0x44,True,b"FakeGPU",1),
        ("Driver KO",        50,    400,     60,   1300,1800,  60000, 80000, 60, 0, False, b"FakeGPU", 1),
        ("Exception NVML",   50,    400,     60,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1),  # handled below
        ("Sensors zero/device lost",0,0,0,0,1800,0,80000,0,0,True,b"FakeGPU",8),
        ("Fréquence instable",55,   400,     60,   600, 1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1),
        ("pstate élevé",     50,    400,     60,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 8),
        ("Fan à zéro/temp OK",40,   400,     50,   1300,1800,  60000, 80000, 0, 0, True, b"FakeGPU", 1),
        ("Fan à 0 mais temp haute",60,400,   90,   1400,1800,  60000, 80000, 0, 0, True, b"FakeGPU", 1),
        ("Handle perdu",     50,    400,     60,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1), # handled below
        ("GPU locked 100% VRAM basse",100,   80,   60,   1800,1800,  80000, 80000, 80, 0, True, b"FakeGPU", 1),
        ("VRAM full GPU faible",10, 1024*1024*990,50, 900,1800,40000,80000,33,0,True,b"FakeGPU",1),
        ("GPU idle fan 100%",5,    100,     30,   500, 1800,  30000, 80000, 100,0,True,b"FakeGPU",1),
        ("Driver trop ancien",60,   400,     60,   1300,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1), # handled below
        ("Undervolting/OC",  60,   400,     60,   2000,1800,  60000, 80000, 60, 0, True, b"FakeGPU", 1),
    ]
    # Mapping pour label crowd dans le log
    scenario_labels = [
        "gpu_idle_pur", "gpu_mi_charge", "gpu_full", "gpu_throttle_power", "gpu_throttle_thermal",
        "gpu_power_limit_only", "gpu_temp_haute", "gpu_vram_saturee", "gpu_throttle_multi",
        "gpu_driver_ko", "gpu_nvml_exception", "gpu_sensors_zero", "gpu_freq_instable", "gpu_pstate_eleve",
        "gpu_fan_zero_ok", "gpu_fan_zero_temp_haute", "gpu_handle_perdu", "gpu_locked_vram_basse",
        "gpu_vram_full_usage_faible", "gpu_idle_fan_100", "gpu_driver_old", "gpu_undervolting_oc"
    ]
    # Normalisation
    for idx, (label, gpu, vram, temp, clk, maxclk, power, pwlim, fan, throttle, drv, name, pstate) in enumerate(scenarios):
        if "Exception NVML" in label:
            # Monkeypatch function to raise Exception
            plugin.pynvml.nvmlDeviceGetHandleByIndex = lambda i: (_ for _ in ()).throw(Exception("NVML driver lost: device is gone"))
            try:
                format_diag(f"{label}", plugin.gpu_diag(), loglist, scenario=scenario_labels[idx])
            except Exception as e:
                format_diag(f"{label} — catch", {"success": False, "message": str(e)}, loglist, scenario=f"{scenario_labels[idx]}_catch")
            # Restore
            plugin.pynvml.nvmlDeviceGetHandleByIndex = orig_nvmlDeviceGetHandleByIndex
            continue
        if "Handle perdu" in label:
            # Simule un handle perdu (None)
            plugin.pynvml.nvmlDeviceGetHandleByIndex = lambda i: None
            try:
                format_diag(f"{label}", plugin.gpu_diag(), loglist, scenario=scenario_labels[idx])
            except Exception as e:
                format_diag(f"{label} — catch", {"success": False, "message": str(e)}, loglist, scenario=f"{scenario_labels[idx]}_catch")
            plugin.pynvml.nvmlDeviceGetHandleByIndex = orig_nvmlDeviceGetHandleByIndex
            continue
        if "Driver KO" in label:
            plugin.NVML_OK = False
            format_diag(f"{label}", plugin.gpu_diag(), loglist, scenario=scenario_labels[idx])
            plugin.NVML_OK = orig_NVML_OK
            continue
        if "Driver trop ancien" in label:
            # Simule version ancienne
            plugin.pynvml.nvmlSystemGetDriverVersion = lambda: b"410.00"
        set_gpu(gpu, vram, temp, clk, maxclk, power, pwlim, fan, throttle, drv, name, pstate)
        format_diag(f"{label}", plugin.gpu_diag(), loglist, scenario=scenario_labels[idx])
        # Reset all
        plugin.pynvml.nvmlDeviceGetUtilizationRates = orig_nvmlDeviceGetUtilizationRates
        plugin.pynvml.nvmlDeviceGetMemoryInfo = orig_nvmlDeviceGetMemoryInfo
        plugin.pynvml.nvmlDeviceGetTemperature = orig_nvmlDeviceGetTemperature
        plugin.pynvml.nvmlDeviceGetClockInfo = orig_nvmlDeviceGetClockInfo
        plugin.pynvml.nvmlDeviceGetMaxClockInfo = orig_nvmlDeviceGetMaxClockInfo
        plugin.pynvml.nvmlDeviceGetPowerUsage = orig_nvmlDeviceGetPowerUsage
        plugin.pynvml.nvmlDeviceGetEnforcedPowerLimit = orig_nvmlDeviceGetEnforcedPowerLimit
        plugin.pynvml.nvmlDeviceGetFanSpeed = orig_nvmlDeviceGetFanSpeed
        plugin.pynvml.nvmlDeviceGetCurrentClocksThrottleReasons = orig_nvmlDeviceGetCurrentClocksThrottleReasons
        plugin.pynvml.nvmlDeviceGetPowerState = orig_nvmlDeviceGetPowerState
        plugin.pynvml.nvmlDeviceGetName = orig_nvmlDeviceGetName
        plugin.pynvml.nvmlSystemGetDriverVersion = orig_nvmlSystemGetDriverVersion


        # Restore originals
        plugin.pynvml.nvmlDeviceGetHandleByIndex = orig_nvmlDeviceGetHandleByIndex
        plugin.pynvml.nvmlDeviceGetUtilizationRates = orig_nvmlDeviceGetUtilizationRates
        plugin.pynvml.nvmlDeviceGetMemoryInfo = orig_nvmlDeviceGetMemoryInfo
        plugin.pynvml.nvmlDeviceGetTemperature = orig_nvmlDeviceGetTemperature
        plugin.pynvml.nvmlDeviceGetName = orig_nvmlDeviceGetName
        plugin.pynvml.nvmlDeviceGetClockInfo = orig_nvmlDeviceGetClockInfo
        plugin.pynvml.nvmlDeviceGetMaxClockInfo = orig_nvmlDeviceGetMaxClockInfo
        if orig_nvmlDeviceGetPowerUsage:
            plugin.pynvml.nvmlDeviceGetPowerUsage = orig_nvmlDeviceGetPowerUsage
        if orig_nvmlDeviceGetEnforcedPowerLimit:
            plugin.pynvml.nvmlDeviceGetEnforcedPowerLimit = orig_nvmlDeviceGetEnforcedPowerLimit
        if orig_nvmlDeviceGetFanSpeed:
            plugin.pynvml.nvmlDeviceGetFanSpeed = orig_nvmlDeviceGetFanSpeed
        if orig_nvmlDeviceGetPowerState:
            plugin.pynvml.nvmlDeviceGetPowerState = orig_nvmlDeviceGetPowerState
        plugin.pynvml.nvmlSystemGetDriverVersion = orig_nvmlSystemGetDriverVersion
        if orig_nvmlDeviceGetCurrentClocksThrottleReasons:
            plugin.pynvml.nvmlDeviceGetCurrentClocksThrottleReasons = orig_nvmlDeviceGetCurrentClocksThrottleReasons

    else:
        format_diag("[SKIP] Monkeypatch GPU: pynvml not available in plugin module.", {"success": False, "message": "no pynvml"}, loglist, scenario="gpu_pynvml_not_available")

    # Export logs
    export_logs(loglist)
