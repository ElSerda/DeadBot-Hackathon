import os
import sys
from pathlib import Path

def resource_path(relative_path: str) -> str:
    """
    Renvoie le chemin absolu d'un fichier, compatible .exe PyInstaller.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

def get_base_path():
    if getattr(sys, 'frozen', False):
        # Exécuté depuis un .exe PyInstaller
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def get_config_path(filename: str = "config.yaml") -> str:
    return resource_path(filename)

def get_logs_dir() -> Path:
    """
    Retourne le dossier `logs/`, crée-le s'il n'existe pas.
    """
    logs_path = Path(resource_path("logs"))
    logs_path.mkdir(parents=True, exist_ok=True)
    return logs_path
