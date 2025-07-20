import requests
import os
import yaml
from utils.path_utils import get_config_path

def load_config():
    from path_utils import resource_path
    with open(resource_path("config.yaml"), "r") as f:
        return yaml.safe_load(f)

def check_openai(api_key):
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get("https://api.openai.com/v1/models", headers=headers, timeout=4)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def check_deepseek(api_key):
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get("https://api.deepseek.com/v1/models", headers=headers, timeout=4)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def check_mammouth(api_key):
    try:
        headers = {"Authorization": f"Bearer {api_key}"}
        r = requests.get("https://api.mammouth.ai/v1/models", headers=headers, timeout=4)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)

def main():
    config = load_config()

    print("=== 🔍 DIAGNOSTIC DES BACKENDS LLM ===\n")

    if "openai" in config:
        status, msg = check_openai(config["openai"].get("api_key", ""))
        print(f"🧠 OpenAI: {status} → {'✅ OK' if status == 200 else '❌'}")
        if status != 200: print("   ↳", msg[:120])

    if "deepseek" in config:
        status, msg = check_deepseek(config["deepseek"].get("api_key", ""))
        print(f"🧠 DeepSeek: {status} → {'✅ OK' if status == 200 else '❌'}")
        if status != 200: print("   ↳", msg[:120])

    if "mammouth" in config:
        status, msg = check_mammouth(config["mammouth"].get("api_key", ""))
        print(f"🧠 Mammouth: {status} → {'✅ OK' if status == 200 else '❌'}")
        if status != 200: print("   ↳", msg[:120])

if __name__ == "__main__":
    main()
