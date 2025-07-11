# DeadBot Light – G-Assist Diagnostic Plugin
[![G-Assist Ready](https://img.shields.io/badge/G--Assist-ready-brightgreen)]()

[![CrowdQA](https://img.shields.io/badge/CROWD--QA-green)]()  
**Version limitée – Hackathon NVIDIA G-Assist 2025**

---

## Description

Ce plugin Python est une version **light** du projet *DeadBot* (pipeline diagnostic système et jeu).  
Il permet de collecter des métriques système (CPU, GPU, RAM, VRAM, DISK, etc.) et de les exposer via une interface standard compatible G-Assist/NVIDIA.  
Toutes les fonctions crowd, fun, overlay, logs avancés ou plugins communautaires ont été retirées de cette version.

---

## Fonctionnalités

- Pipeline diagnostic basique : récupération et export de métriques système pour diagnostic IA.
- Interface compatible plugin G-Assist (`manifest.json`, communication pipes).
- Diagnostic pondéré : charge GPU/CPU, throttling, VRAM, température, power limit, crash driver, edge cases…
- **Aucune clé API, aucun secret, aucune feature propriétaire n’est incluse.**

---

## Exemples – manifest, JSON d’appel, réponse

### manifest.json

```json
{
  "manifestVersion": 1,
  "executable": "./g-assist-plugin-python.exe",
  "persistent": true,
  "functions": [
    {
      "name": "gpu_diag",
      "description": "Returns NVIDIA GPU diagnostics (usage, vram, temperature, etc.)"
    },
    {
      "name": "cpu_diag",
      "description": "Returns CPU diagnostics (usage, cores, threads)"
    }
  ]
}

Appel JSON

{
  "tool_calls": [
    { "func": "gpu_diag" }
  ],
  "messages": [
    { "role": "system", "content": "Réponds toujours en français." },
    { "role": "user", "content": "Donne-moi l’état de ma carte graphique." }
  ]
}

Réponse plugin

{
  "success": true,
  "message": "La carte graphique NVIDIA est à 45 % d’utilisation, température 62 °C, 4 Go/8 Go de VRAM utilisés."
}

Schéma rapide

flowchart TD
    User["Utilisateur (ex : Streamer)"] -->|Question/commande| GAssist["G-Assist / Manager"]
    GAssist -->|JSON {tool_calls, messages}| Plugin["DeadBot Plugin (plugin.py)"]
    Plugin -->|Diagnostic JSON| GAssist
    GAssist -->|Prompt LLM| LLM["NVIDIA LLM (Llama3/LoRA)"]
    LLM -->|Réponse vulgarisée| GAssist
    GAssist -->|Message crowd| User

Exemple de test CLI/script rapide

echo '{"tool_calls":[{"func":"gpu_diag"}],"messages":[{"role":"system","content":"Réponds en français."},{"role":"user","content":"Diagnostic GPU ?"}]}' | ./g-assist-plugin-python.exe

en Python :

import subprocess
payload = '{"tool_calls":[{"func":"gpu_diag"}],"messages":[{"role":"system","content":"Réponds en français."},{"role":"user","content":"Diagnostic GPU ?"}]}'
proc = subprocess.run(["./g-assist-plugin-python.exe"], input=payload.encode(), stdout=subprocess.PIPE)
print(proc.stdout.decode())





Licence
AGPLv3 (ou Apache 2.0 sur demande)
Merci de préciser lors du fork ou de la réutilisation.