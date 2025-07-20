import ctypes
import json
import logging
import os
import sys
import traceback
import ctypes
from ctypes import wintypes, windll
from ctypes import byref, wintypes

# ========== LOGGING ==========
LOG_FILE = os.path.join(os.environ.get("USERPROFILE", "."), 'deadbot_plugin.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Ajout pour logger l'input et l'output à côté du .exe
LOG_IO_FILE = os.path.join(os.path.dirname(sys.argv[0]), "deadbot_io.log")

def log_io(entry_type, content):
    try:
        with open(LOG_IO_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{entry_type}] {content}\n")
            f.flush()
            os.fsync(f.fileno())
        print(f"[{entry_type}] {content}")  # Debug
    except Exception as e:
        logging.error(f"Log IO failed: {e}")

# ========== NVML INIT ==========
NVML_OK = False
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_OK = True
except Exception:
    try:
        import nvidia_smi as pynvml
        pynvml.nvmlInit()
        NVML_OK = True
    except Exception as e:
        logging.warning(f"NVML init failed: {e}")

import psutil

# ========== UTILS ==========
def generate_success_response(message: str = None) -> dict:
    response = {'success': True}
    if message:
        response['message'] = message
    return response

def generate_failure_response(message: str = None) -> dict:
    response = {'success': False}
    if message:
        response['message'] = message
    return response

# ========== COMM PIPE HANDLING ==========
def read_command() -> dict | None:
    """Lit la commande depuis stdin pipe, robuste, chunks."""
    try:
        STD_INPUT_HANDLE = -10
        pipe = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
        chunks = []
        while True:
            BUFFER_SIZE = 4096
            message_bytes = wintypes.DWORD()
            buffer = ctypes.create_string_buffer(BUFFER_SIZE)
            success = ctypes.windll.kernel32.ReadFile(
                pipe, buffer, BUFFER_SIZE, byref(message_bytes), None
            )
            if not success:
                logging.error('Error reading from pipe')
                return None
            chunk = buffer.raw[:message_bytes.value].decode('utf-8', errors='replace')
            chunks.append(chunk)
            if message_bytes.value < BUFFER_SIZE:
                break
        raw_input = ''.join(chunks)
        logging.info(f'Raw Input: {raw_input}')
        # Nettoie les caractères bizarres
        clean_text = ''.join(ch for ch in raw_input if ch.isprintable() or ch in ['\n', '\t', '\r'])
        return json.loads(clean_text)
    except json.JSONDecodeError:
        logging.error(f"Received invalid JSON")
        logging.exception("JSON decoding failed:")
        return None
    except Exception as e:
        logging.error(f"Exception in read_command(): {str(e)}")
        logging.error(traceback.format_exc())
        return None

def write_response(response):
    """Envoie la réponse JSON crowd sur stdout pipe, + <<END>>"""
    try:
        STD_OUTPUT_HANDLE = -11
        pipe = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        json_message = json.dumps(response) + '<<END>>'
        message_bytes = json_message.encode('utf-8')
        message_len = len(message_bytes)
        bytes_written = wintypes.DWORD()
        windll.kernel32.WriteFile(
            pipe,
            message_bytes,
            message_len,
            ctypes.byref(bytes_written),
            None
        )
    except Exception as e:
        logging.error(f"Failed to write response: {e}")
        logging.error(traceback.format_exc())

# ========== HANDLERS ==========

def execute_initialize_command(*_):
    logging.info('DeadBot initialized.')
    return generate_success_response("DeadBot initialized.")

def execute_shutdown_command(*_):
    logging.info('DeadBot shutdown.')
    return generate_success_response("DeadBot shutdown.")

def execute_cpu_diag_command(params=None, context=None, system_info=None):
    try:
        usage = psutil.cpu_percent(interval=0.2)
        core_count = psutil.cpu_count(logical=False)
        thread_count = psutil.cpu_count(logical=True)
        freq = psutil.cpu_freq()
        freq_current = getattr(freq, "current", None)
        freq_max = getattr(freq, "max", None)
        freq_percent = (freq_current / freq_max * 100) if freq_current and freq_max else None

        if usage < 10:
            diag = "CPU idle, aucun souci détecté."
        elif usage > 90 and freq_percent and freq_percent < 70:
            diag = f"ALERTE: Charge CPU critique ET fréquence réduite ({freq_current}/{freq_max} MHz)"
        elif usage > 90:
            diag = "ALERTE: Charge CPU critique !"
        else:
            diag = "Charge CPU normale."

        return {
            "success": True,
            "message": diag,
            "cpu_usage_percent": usage,
            "cores": core_count,
            "threads": thread_count,
            "frequency_MHz": freq_current,
            "frequency_max_MHz": freq_max,
            "diagnostic": diag
        }
    except Exception as e:
        return generate_failure_response(f"Error getting CPU info: {e}")

def execute_gpu_diag_command(params=None, context=None, system_info=None):
    if not NVML_OK:
        return generate_failure_response("Driver NVIDIA non dispo. Reboot requis.")
    try:
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(h)
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
        name = pynvml.nvmlDeviceGetName(h)
        clock_current = pynvml.nvmlDeviceGetClockInfo(h, pynvml.NVML_CLOCK_GRAPHICS)
        clock_max = pynvml.nvmlDeviceGetMaxClockInfo(h, pynvml.NVML_CLOCK_GRAPHICS)
        power = pynvml.nvmlDeviceGetPowerUsage(h) // 1000
        power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(h) // 1000
        fan_speed = pynvml.nvmlDeviceGetFanSpeed(h)

        util_gpu = float(util.gpu)
        clock_current = float(clock_current)
        clock_max = float(clock_max)
        clock_percent = (clock_current / clock_max * 100) if clock_max else None
        mem_used = float(mem.used)
        mem_total = float(mem.total)
        vram_util = (mem_used / mem_total * 100) if mem_total else None
        temp = float(temp)
        power = float(power)
        power_limit = float(power_limit)
        fan_speed = float(fan_speed)

        diag = []
        freq_str = f"{int(clock_current)}/{int(clock_max)} MHz"
        if util_gpu < 10:
            diag.append(f"GPU idle, aucun souci détecté. (Fréq: {freq_str})")
        elif util_gpu > 90 and clock_percent and clock_percent < 70:
            diag.append(f"ALERTE: Charge GPU critique ET fréquence réduite ({freq_str})")
        elif util_gpu > 90:
            diag.append(f"ALERTE: Charge GPU critique ! (Fréq: {freq_str})")
        else:
            diag.append(f"Charge GPU normale. (Fréq: {freq_str})")

        if temp > 85:
            diag.append(f"ALERTE: Température GPU élevée ({temp:.1f}°C) !")
        if vram_util and vram_util > 95:
            diag.append(f"ALERTE: VRAM saturée ({vram_util:.1f}%) !")
        if power > 0.98 * power_limit:
            diag.append(f"ALERTE: Limite de puissance atteinte ({int(power)}/{int(power_limit)}W) !")

        return {
            "success": True,
            "gpu_name": name.decode() if hasattr(name, "decode") else str(name),
            "gpu_usage_percent": util_gpu,
            "graphics_clock_MHz": clock_current,
            "temperature_C": temp,
            "vram_util_percent": vram_util,
            "diagnostic": " | ".join(diag),
            "message": " | ".join(diag)
        }
    except Exception as e:
        return generate_failure_response(f"Erreur GPU : {e}")

def execute_perf_diag_command(params=None, context=None, system_info=None):
    try:
        cpu = execute_cpu_diag_command()
        gpu = execute_gpu_diag_command()
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024**3)
        ram_total = ram.total / (1024**3)
        ram_percent = ram.percent
        disk = psutil.disk_usage('/')
        disk_used = disk.used / (1024**3)
        disk_total = disk.total / (1024**3)
        disk_percent = disk.percent

        summary = []
        summary.append(cpu.get("diagnostic", ""))
        summary.append(gpu.get("diagnostic", ""))
        summary.append(f"RAM : {ram_percent:.1f}% utilisée ({ram_used:.1f} Go / {ram_total:.1f} Go)")
        if ram_percent > 90:
            summary.append("⚠️ RAM presque saturée.")
        summary.append(f"Disque : {disk_percent:.1f}% utilisé ({disk_used:.1f} Go / {disk_total:.1f} Go)")
        if disk_percent > 95:
            summary.append("⚠️ Disque très plein, risque de lag ou crash.")

        return {
            "success": True,
            "diagnostic": " | ".join(summary),
            "message": " | ".join(summary),
            "cpu": cpu,
            "gpu": gpu,
            "ram_used_GB": ram_used,
            "ram_total_GB": ram_total,
            "ram_percent": ram_percent,
            "disk_used_GB": disk_used,
            "disk_total_GB": disk_total,
            "disk_percent": disk_percent
        }
    except Exception as e:
        return generate_failure_response(f"Erreur dans perf_diag: {e}")

# ========== MAIN LOOP ==========
def main():
    TOOL_CALLS_PROPERTY = 'tool_calls'
    CONTEXT_PROPERTY = 'messages'
    SYSTEM_INFO_PROPERTY = 'system_info'
    FUNCTION_PROPERTY = 'func'
    PARAMS_PROPERTY = 'properties'
    INITIALIZE_COMMAND = 'initialize'
    SHUTDOWN_COMMAND = 'shutdown'
    ERROR_MESSAGE = 'Plugin Error!'

    commands = {
        "initialize": execute_initialize_command,
        "shutdown": execute_shutdown_command,
        "cpu_diag": execute_cpu_diag_command,
        "gpu_diag": execute_gpu_diag_command,
        "perf_diag": execute_perf_diag_command,
    }
    cmd = ''
    logging.info('DeadBot plugin started.')

    shutdown_requested = False

    while not shutdown_requested:
        input_data = read_command()
        if input_data is None:
            logging.error('Error reading command')
            break

        if TOOL_CALLS_PROPERTY in input_data:
            tool_calls = input_data[TOOL_CALLS_PROPERTY]
            for tool_call in tool_calls:
                if FUNCTION_PROPERTY in tool_call:
                    cmd = tool_call[FUNCTION_PROPERTY]
                    if cmd in commands:
                        try:
                            if cmd in [INITIALIZE_COMMAND, SHUTDOWN_COMMAND]:
                                response = commands[cmd]()
                            else:
                                params = tool_call.get(PARAMS_PROPERTY)
                                context = input_data.get(CONTEXT_PROPERTY)
                                system_info = input_data.get(SYSTEM_INFO_PROPERTY)
                                response = commands[cmd](params, context, system_info)
                        except Exception as e:
                            logging.error(f'Error in command {cmd}: {str(e)}')
                            logging.error(traceback.format_exc())
                            response = generate_failure_response(str(e))
                    else:
                        logging.warning(f'Unknown command: {cmd}')
                        response = generate_failure_response(f'{ERROR_MESSAGE} Unknown command: {cmd}')
                else:
                    logging.warning('Malformed input.')
                    response = generate_failure_response(f'{ERROR_MESSAGE} Malformed input.')

                logging.info(f'Response: {response}')
                log_io("OUTPUT", str(response))
                write_response(response)

                # 🟢 PATCH : Dès qu'on croise shutdown, on sort du while
                if cmd == SHUTDOWN_COMMAND:
                    shutdown_requested = True
                    break  # on sort du for (tool_calls)
        else:
            logging.warning('Malformed input.')
            response = generate_failure_response(f'{ERROR_MESSAGE} Malformed input.')
            log_io("OUTPUT", str(response))
            write_response(response)

if __name__ == "__main__":
    main()