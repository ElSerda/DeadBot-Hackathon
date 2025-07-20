import requests
from path_utils import get_config_path
import yaml

def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        print("[AVERTISSEMENT] Fichier config.yaml introuvable. Utilisation d'un modèle par défaut.")
        return {}  # ou charger `config_template.yaml` si dispo

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def check_llm_services():
    config = load_config()
    statuses = {}

    def check(url, key):
        try:
            r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=4)
            return r.status_code == 200
        except:
            return False

    if "openai" in config:
        statuses["OpenAI"] = check("https://api.openai.com/v1/models", config["openai"].get("api_key", ""))

    if "deepseek" in config:
        statuses["DeepSeek"] = check("https://api.deepseek.com/v1/models", config["deepseek"].get("api_key", ""))

    if "mammouth" in config:
        statuses["Mammouth"] = check("https://api.mammouth.ai/v1/models", config["mammouth"].get("api_key", ""))

    return statuses

def llm_status_command():
    statuses = check_llm_services()
    status_msg = "🧠 LLM actifs : "

    for name, is_up in statuses.items():
        emoji = "✅" if is_up else "❌"
        status_msg += f"{name} {emoji} / "

    return status_msg.strip(" / ")
