# Need a FIX !
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic.experimental")

import os
import sys
import ctypes
import json
import logging
import psutil
from ctypes import wintypes
from llm_backend import LLMBackend

# ===== INIT LOGGING =====
LOG_FILE = os.path.join(os.environ.get("USERPROFILE", "."), 'python_plugin.log')
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ====== PATCH DLL PATH FOR NVML ======
nvml_path = r"C:\Windows\System32\nvml.dll"
try:
    ctypes.WinDLL(nvml_path)
except Exception as e:
    logging.warning(f"Échec chargement nvml.dll : {e}")
if hasattr(os, "add_dll_directory"):
    os.add_dll_directory(r"C:\Windows\System32")
sys.path.append(r"C:\Windows\System32")
os.environ["PATH"] = r"C:\Windows\System32;" + os.environ.get("PATH", "")

# ===== LOAD NVML ======
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

# ====== LLM INIT ======
llm_backend = None

def get_llm_backend():
    global llm_backend
    if llm_backend is None:
        try:
            print("[DeadBot] Initialisation LLM backend crowd...")
            llm_backend = LLMBackend()
        except Exception as e:
            logging.error(f"Erreur lors du chargement LLM : {e}")
            return None
    return llm_backend

# ===== MAIN DISPATCH =====
def main():
    TOOL_CALLS_PROPERTY = 'tool_calls'
    FUNCTION_PROPERTY = 'func'
    PARAMS_PROPERTY = 'properties'
    CONTEXT_PROPERTY = 'messages'
    SYSTEM_INFO_PROPERTY = 'system_info'
    SHUTDOWN_COMMAND = 'shutdown'
    INITIALIZE_COMMAND = 'initialize'
    ERROR_MESSAGE = 'Plugin Error!'
    cmd = ''

    commands = {
        'initialize': execute_initialize_command,
        'shutdown': execute_shutdown_command,
        'cpu_diag': execute_cpu_diag_command,
        'gpu_diag': execute_gpu_diag_command,
        'llm_diag': execute_llm_diag_command,
        'llm_status': execute_llm_status_command,
        'chat_handler': execute_chat_handler_command
    }

    logging.info('DeadBot Plugin started')
    while cmd != SHUTDOWN_COMMAND:
        input_data = read_command()
        if input_data is None:
            logging.error('Error reading command')
            continue

        logging.info(f"Received input: {input_data}")
        if TOOL_CALLS_PROPERTY in input_data:
            for tool_call in input_data[TOOL_CALLS_PROPERTY]:
                cmd = tool_call.get(FUNCTION_PROPERTY)
                logging.info(f"Processing command: {cmd}")
                if cmd in commands:
                    if cmd in ['initialize', 'shutdown']:
                        response = commands[cmd]()
                    else:
                        params = tool_call.get(PARAMS_PROPERTY)
                        context = input_data.get(CONTEXT_PROPERTY)
                        system_info = input_data.get(SYSTEM_INFO_PROPERTY)
                        try:
                            response = commands[cmd](params, context, system_info)
                        except Exception as e:
                            logging.error(f"Error in command {cmd}: {e}")
                            response = generate_failure_response(str(e))
                else:
                    response = generate_failure_response(f"{ERROR_MESSAGE} Unknown command: {cmd}")
                logging.info(f"Sending response: {response}")
                write_response(response)

        if cmd == SHUTDOWN_COMMAND:
            logging.info('Shutdown command received, terminating plugin')
            break

    logging.info('DeadBot Plugin stopped.')

# ====== COMMUNICATION ======
def read_command():
    try:
        STD_INPUT_HANDLE = -10
        pipe = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
        BUFFER_SIZE = 4096
        message_bytes = wintypes.DWORD()
        buffer = ctypes.create_string_buffer(BUFFER_SIZE)
        success = ctypes.windll.kernel32.ReadFile(pipe, buffer, BUFFER_SIZE, ctypes.byref(message_bytes), None)
        if not success:
            return None
        chunk = buffer.raw[:message_bytes.value].decode('utf-8')
        return json.loads(chunk)
    except Exception as e:
        logging.error(f"Error in read_command: {e}")
        return None

def write_response(response):
    try:
        STD_OUTPUT_HANDLE = -11
        pipe = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        json_message = json.dumps(response)
        message_bytes = json_message.encode('utf-8')
        bytes_written = wintypes.DWORD()
        ctypes.windll.kernel32.WriteFile(pipe, message_bytes, len(message_bytes), ctypes.byref(bytes_written), None)
    except Exception as e:
        logging.error(f"Failed to write response: {e}")

# ====== UTIL ======
def generate_success_response(message=None):
    return {'success': True, 'message': message} if message else {'success': True}

def generate_failure_response(message=None):
    return {'success': False, 'message': message} if message else {'success': False}

# ====== HANDLERS ======
def execute_initialize_command():
    return generate_success_response("DeadBot initialized.")

def execute_shutdown_command():
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
        clock_percent = clock_current / clock_max * 100 if clock_max else None
        power = pynvml.nvmlDeviceGetPowerUsage(h) // 1000
        power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(h) // 1000
        fan_speed = pynvml.nvmlDeviceGetFanSpeed(h)
        vram_util = mem.used / mem.total * 100 if mem.total else None

        diag = []
        freq_str = f"{clock_current}/{clock_max} MHz"
        if util.gpu < 10:
            diag.append(f"GPU idle, aucun souci détecté. (Fréq: {freq_str})")
        elif util.gpu > 90 and clock_percent < 70:
            diag.append(f"ALERTE: Charge GPU critique ET fréquence réduite ({freq_str})")
        elif util.gpu > 90:
            diag.append(f"ALERTE: Charge GPU critique ! (Fréq: {freq_str})")
        else:
            diag.append(f"Charge GPU normale. (Fréq: {freq_str})")

        if temp > 85:
            diag.append(f"ALERTE: Température GPU élevée ({temp}°C) !")
        if vram_util > 95:
            diag.append(f"ALERTE: VRAM saturée ({vram_util:.1f}%) !")
        if power > 0.98 * power_limit:
            diag.append(f"ALERTE: Limite de puissance atteinte ({power}/{power_limit}W) !")

        return {
            "success": True,
            "gpu_name": name.decode() if hasattr(name, "decode") else str(name),
            "gpu_usage_percent": util.gpu,
            "graphics_clock_MHz": clock_current,
            "temperature_C": temp,
            "vram_util_percent": vram_util,
            "diagnostic": " | ".join(diag)
        }
    except Exception as e:
        return generate_failure_response(f"Erreur GPU : {e}")
    
def execute_perf_diag_command(params=None, context=None, system_info=None):
    try:
        # CPU
        cpu = execute_cpu_diag_command()
        # GPU
        gpu = execute_gpu_diag_command()
        # RAM
        ram = psutil.virtual_memory()
        ram_used = ram.used / (1024**3)
        ram_total = ram.total / (1024**3)
        ram_percent = ram.percent
        # Disque
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


def execute_llm_diag_command(params=None, context=None, system_info=None):
    backend = get_llm_backend()
    if backend is None:
        return generate_failure_response("LLM backend non disponible.")
    try:
        prompt = params.get("prompt", "test prompt") if params else "test prompt"
        response = backend.generate(prompt)
        return generate_success_response(response)
    except Exception as e:
        return generate_failure_response(str(e))

def execute_llm_status_command(params=None, context=None, system_info=None):
    backend = get_llm_backend()
    if backend is None:
        return generate_failure_response("LLM backend non disponible.")
    return generate_success_response("LLM backend OK.")

def execute_chat_handler_command(params=None, context=None, system_info=None):
    user_input = ""
    if context and isinstance(context, list):
        for msg in reversed(context):
            if msg.get("role") == "user":
                user_input = msg.get("content", "")
                break

    # Les lignes suivantes remplacent l’appel direct à llm_backend
    backend = get_llm_backend()
    if backend is None:
        return generate_failure_response("LLM backend non disponible.")

    # Si tu veux garder ton crowd-logic :
    if "fonctionne" in user_input and "pc" in user_input:
        cpu = execute_cpu_diag_command()
        gpu = execute_gpu_diag_command()
        summary = f"Résumé système : {cpu.get('diagnostic')} | {gpu.get('diagnostic')}"
        return generate_success_response(summary)

    try:
        response = backend.generate(user_input)
        return generate_success_response(response)
    except Exception as e:
        return generate_failure_response(f"Erreur LLM: {e}")
    
# === FONCTIONS QA POUR TEST_PLUGIN ===

#def cpu_diag():
    return execute_cpu_diag_command()

#def gpu_diag():
    return execute_gpu_diag_command()


if __name__ == "__main__":
    main()
