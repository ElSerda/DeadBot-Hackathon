# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import ctypes
import json
import logging
import psutil

from ctypes import wintypes

# --- PATCH DLL / PATH (avant tout import NVML)
nvml_path = r"C:\Windows\System32\nvml.dll"
try:
    ctypes.WinDLL(nvml_path)
    print("[DEBUG] nvml.dll chargée en direct")
except Exception as e:
    print("[DEBUG] Echec chargement nvml.dll :", e)

if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(r"C:\Windows\System32")
sys.path.append(r"C:\Windows\System32")
os.environ["PATH"] = r"C:\Windows\System32;" + os.environ.get("PATH", "")

# --- IMPORT NVML WRAPPERS (multi-compatible)
NVML_OK = False
pynvml = None
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_OK = True
    print("[DEBUG] pynvml chargé")
except Exception as e:
    try:
        import nvidia_smi as pynvml  # fallback: nvidia-ml-py3 parfois installée sous ce nom
        pynvml.nvmlInit()
        NVML_OK = True
        print("[DEBUG] nvidia-ml-py3 chargé (as nvidia_smi)")
    except Exception as ee:
        NVML_OK = False
        logging.warning(f"NVML init failed: {ee}")

# --- Command functions ---
def gpu_diag(params=None, context=None, system_info=None):
    # Cas 1 : NVML non dispo / driver crashé / jamais initialisé
    if not NVML_OK:
        return {
            "success": False,
            "message": (
                "Crash driver GPU détecté : DeadBot ne peut plus accéder au driver NVIDIA. "
                "Monitoring impossible tant que le driver n’est pas réinitialisé."
            )
        }
    try:
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(h)
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        temp = pynvml.nvmlDeviceGetTemperature(h, getattr(pynvml, 'NVML_TEMPERATURE_GPU', 0))
        driver = pynvml.nvmlSystemGetDriverVersion()
        name = pynvml.nvmlDeviceGetName(h)
        clock_current = pynvml.nvmlDeviceGetClockInfo(h, getattr(pynvml, 'NVML_CLOCK_GRAPHICS', 0))
        clock_max = pynvml.nvmlDeviceGetMaxClockInfo(h, getattr(pynvml, 'NVML_CLOCK_GRAPHICS', 0))
        clock_percent = clock_current / clock_max * 100 if clock_max else None
        try:
            power = pynvml.nvmlDeviceGetPowerUsage(h) // 1000
            power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(h) // 1000
        except Exception:
            power, power_limit = None, None
        try:
            fan_speed = pynvml.nvmlDeviceGetFanSpeed(h)
        except Exception:
            fan_speed = None
        try:
            pstate = pynvml.nvmlDeviceGetPowerState(h)
        except Exception:
            pstate = None
        vram_util = mem.used / mem.total * 100 if mem.total else None
        try:
            throttle = pynvml.nvmlDeviceGetCurrentClocksThrottleReasons(h)
        except Exception:
            throttle = None

        gpu_usage = util.gpu
        # Mini-diag croisé ultra light
                # Mini-diag pondéré sur charge, fréquence, throttle, etc.
        diag = []

        # Fréquence lisible à chaque diagnostic
        freq_str = f"{clock_current}/{clock_max} MHz" if clock_current and clock_max else "inconnue"
        
        # Pondération crowd sur la charge et la fréquence
        if gpu_usage < 10:
            diag.append(f"GPU idle, aucun souci détecté. (Fréq: {freq_str})")
        elif gpu_usage > 90:
            if clock_percent and clock_percent < 70:
                diag.append(
                    f"ALERTE: Charge GPU critique ET fréquence réduite ({freq_str}) — possible throttling !"
                )
            else:
                diag.append(f"ALERTE: Charge GPU critique ! (Fréq: {freq_str})")
        elif gpu_usage > 50 and clock_percent and clock_percent < 70:
            diag.append(
                f"Attention : Fréquence GPU réduite sous charge ({freq_str}), limitation probable (throttle/power/temp) !"
            )
        elif gpu_usage < 30 and clock_percent and clock_percent < 50:
            diag.append(f"GPU en économie d’énergie (fréquence réduite : {freq_str}, idle).")
        else:
            diag.append(f"Charge GPU normale. (Fréq: {freq_str})")

        # Alertes supplémentaires
        if temp > 85:
            diag.append(f"ALERTE: Température GPU élevée ({temp}°C) !")
        if vram_util and vram_util > 95:
            diag.append(f"ALERTE: VRAM saturée ({vram_util:.1f}%) !")
        if power and power_limit and power > 0.98 * power_limit:
            diag.append(f"ALERTE: Limite de puissance atteinte ({power}/{power_limit}W) !")

        # Decode throttle reason code (si non nul)
        def decode_throttle_reason(code):
            # Référence NVML : https://docs.nvidia.com/deploy/nvml-api/structnvml__clocks__throttle__reasons__t.html
            mapping = {
                0x00000001: "Idle",
                0x00000002: "Application clocks setting",
                0x00000004: "SW Power Cap",
                0x00000008: "HW Slowdown (Thermal, Power, External)",
                0x00000010: "Sync Boost",
                0x00000020: "SW Thermal Slowdown",
                0x00000040: "HW Thermal Slowdown",
                0x00000080: "HW Power Brake Slowdown",
                # Étends au besoin selon doc NVIDIA
            }
            reasons = [label for val, label in mapping.items() if code & val]
            return reasons if reasons else [f"Code inconnu ({code})"]

        if throttle:
            throttle_human = ", ".join(decode_throttle_reason(throttle))
            diag.append(f"Raison throttle détectée : {throttle_human}")

        diagnostic = " | ".join(diag)


        return {
            "success": True,
            "gpu_name": name.decode() if hasattr(name, "decode") else str(name),
            "gpu_usage_percent": gpu_usage,
            "graphics_clock_MHz": clock_current,
            "graphics_clock_max_MHz": clock_max,
            "graphics_clock_percent": clock_percent,
            "vram_used_MB": mem.used // (1024 ** 2),
            "vram_total_MB": mem.total // (1024 ** 2),
            "vram_util_percent": vram_util,
            "temperature_C": temp,
            "fan_speed_percent": fan_speed,
            "power_usage_W": power,
            "power_limit_W": power_limit,
            "perf_state": pstate,
            "driver_version": driver.decode() if hasattr(driver, "decode") else str(driver),
            "diagnostic": diagnostic
        }
    except Exception as e:
        err = str(e)
        # Si erreur typée driver/NVML, message crowd explicite
        if "NVML" in err or "driver" in err.lower():
            msg = (
                "Crash driver GPU détecté : DeadBot ne peut plus accéder au driver NVIDIA. "
                "Monitoring impossible tant que le driver n’est pas réinitialisé."
            )
        else:
            msg = (
                "Erreur inattendue lors de la récupération des infos GPU : "
                + err
            )
        logging.error(f"Error in gpu_diag: {err}")
        return {"success": False, "message": msg}


def cpu_diag(params=None, context=None, system_info=None):
    try:
        usage = psutil.cpu_percent(interval=0.2)
        core_count = psutil.cpu_count(logical=False)
        thread_count = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        freq_current = getattr(freq, "current", None) if freq else None
        freq_max = getattr(freq, "max", None) if freq else None
        freq_percent = None
        diag = ""

        # Cas où les infos freq sont manquantes ou incohérentes
        if freq_current is None or freq_max in (None, 0):
            diag = "Erreur : impossible de lire la fréquence CPU (donnée manquante ou invalide)."
        else:
            try:
                freq_percent = freq_current / freq_max * 100
            except Exception:
                freq_percent = None

            if usage < 10:
                diag = "CPU idle, aucun souci détecté."
            elif usage > 90:
                if freq_percent is not None and freq_percent < 70:
                    diag = f"ALERTE: Charge CPU critique ET fréquence réduite ({freq_current or '???'}/{freq_max or '???'} MHz) – possible throttling !"
                else:
                    diag = "ALERTE: Charge CPU critique !"
            else:
                diag = "Charge CPU normale."

        return {
            "success": True,
            "cpu_usage_percent": usage,
            "cores": core_count,
            "threads": thread_count,
            "frequency_MHz": freq_current,
            "frequency_max_MHz": freq_max,
            "diagnostic": diag
        }
    except Exception as e:
        logging.error(f"Error in cpu_diag: {e}")
        return {
            "success": False,
            "diagnostic": f"Error getting CPU info: {e}",
            "message": str(e)
        }



# --- Pipe communication (idem)
def main():
    LOG_FILE = os.path.join(os.environ.get("USERPROFILE", "."), 'python_plugin.log')
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    COMMANDS = {
        'gpu_diag': gpu_diag,
        'cpu_diag': cpu_diag,
        'initialize': lambda *a, **k: {"success": True, "message": "initialized"},
        'shutdown': lambda *a, **k: {"success": True, "message": "shutdown"}
    }
    SHUTDOWN_COMMAND = 'shutdown'
    cmd = ''

    logging.info('DeadBot Light Plugin started')
    try:
        while cmd != SHUTDOWN_COMMAND:
            input_data = read_command()
            if input_data is None:
                logging.error('Error reading command')
                continue

            logging.info(f'Received input: {input_data}')

            if "tool_calls" in input_data:
                for tool_call in input_data["tool_calls"]:
                    cmd = tool_call.get("func")
                    logging.info(f"Processing command: {cmd}")
                    func = COMMANDS.get(cmd)
                    if func:
                        params = tool_call.get("properties")
                        context = input_data.get("messages")
                        system_info = input_data.get("system_info")
                        try:
                            response = func(params, context, system_info)
                        except Exception as e:
                            response = {"success": False, "message": str(e)}
                    else:
                        response = {"success": False, "message": f"Unknown command: {cmd}"}
                    logging.info(f"Sending response: {response}")
                    write_response(response)

            if cmd == SHUTDOWN_COMMAND:
                logging.info('Shutdown command received, terminating plugin')
                break
    except KeyboardInterrupt:
        logging.info('Plugin stopped by user (KeyboardInterrupt). Exiting cleanly.')
        sys.exit(0)
    except Exception as e:
        logging.error(f'Unexpected error in main loop: {e}')
        sys.exit(1)

    logging.info('DeadBot Light Plugin stopped.')


def read_command():
    try:
        STD_INPUT_HANDLE = -10
        kernel32 = ctypes.windll.kernel32
        pipe = kernel32.GetStdHandle(STD_INPUT_HANDLE)
        BUFFER_SIZE = 4096
        message_bytes = wintypes.DWORD()
        buffer = ctypes.create_string_buffer(BUFFER_SIZE)
        success = kernel32.ReadFile(
            pipe,
            buffer,
            BUFFER_SIZE,
            ctypes.byref(message_bytes),
            None
        )
        if not success:
            logging.error('Error reading from command pipe')
            return None
        chunk = buffer.raw[:message_bytes.value].decode('utf-8')
        return json.loads(chunk)
    except Exception as e:
        logging.error(f"Error in read_command: {e}")
        return None

def write_response(response):
    try:
        STD_OUTPUT_HANDLE = -11
        kernel32 = ctypes.windll.kernel32
        pipe = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        json_message = json.dumps(response) + "\n"  # <-- Ajout saut de ligne ici
        message_bytes = json_message.encode('utf-8')
        message_len = len(message_bytes)
        bytes_written = wintypes.DWORD()
        kernel32.WriteFile(
            pipe,
            message_bytes,
            message_len,
            ctypes.byref(bytes_written),
            None
        )
    except Exception as e:
        logging.error(f"Failed to write response: {e}")


if __name__ == "__main__":
    # DEBUG ONLY :
    # print("=== CPU DIAG ===")
    # print(cpu_diag())
    # print("\n=== GPU DIAG ===")
    # print(gpu_diag())
    # PROD ONLY :
    main()

