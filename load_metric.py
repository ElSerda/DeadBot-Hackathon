# load_metric.py
# Squelette du chargeur de métriques intelligent pour DeadBot
# standard vs pwned_mode

import os

def plugin_enabled(plugin_name, config_path="config.yaml"):
    import yaml
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        return config.get("plugins", {}).get(plugin_name, False)
    except Exception:
        return False

def is_hwinfo_running():
    # Placeholder : à remplacer par un vrai check Shared Memory
    return Path("HWiNFO64.exe").exists()

def is_presentmon_available():
    return Path("PresentMon.exe").exists()

def get_metrics_internal():
    # Métriques de base, récupérées sans plugin
    return {
        "cpu": {"value": 70.0, "source": "internal"},
        "ram": {"value": 55.0, "source": "internal"},
        "gpu": {"value": 65.5, "source": "internal"},
    }

def get_metrics_hwinfo():
    # Placeholder : implémenter lecture des données HWINFO
    return {
        "gpu_power": {"value": 132.4, "source": "hwinfo"},
        "cpu_temp": {"value": 78.1, "source": "hwinfo"},
    }

def get_metrics_presentmon():
    # Placeholder : lire FPS depuis fichier ou pipe
    return {
        "fps": {"value": 59.3, "source": "presentmon"},
    }

def load_all_metrics():
    metrics = get_metrics_internal()

    if plugin_enabled("plugin_hwinfo") and is_hwinfo_running():
        metrics.update(get_metrics_hwinfo())

    if plugin_enabled("plugin_presentmon") and is_presentmon_available():
        metrics.update(get_metrics_presentmon())

    return metrics

if __name__ == "__main__":
    all_metrics = load_all_metrics()
    for name, data in all_metrics.items():
        print(f"{name}: {data['value']} (source: {data['source']})")
