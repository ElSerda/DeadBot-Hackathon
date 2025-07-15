DeadBot – NVIDIA G-Assist Plugin
DeadBot est un plugin léger et performant conçu pour NVIDIA G-Assist, permettant un diagnostic en temps réel des ressources CPU et GPU sur les machines Windows. Il offre une interface graphique intuitive et interactive pour aider les utilisateurs — streamers, gamers, technophiles — à comprendre rapidement l’état de leur système et à détecter les éventuels goulets d’étranglement ou anomalies.

Fonctionnalités:

- Diagnostic CPU & GPU précis : Utilisation de la bibliothèque pynvml pour extraire les métriques clés (charge, température, fréquence, VRAM, throttling).

- Interface utilisateur ergonomique : Zone de logs, chat interactif, boutons de commandes (!diag, !bench, !switch).

- Batterie de benchmarks : Collecte dynamique des données de charge en temps réel avec export automatique CSV et génération de graphiques visuels (matplotlib).

- Intelligence artificielle intégrée : Interaction avec des backends LLM (OpenAI et Ollama) pour fournir des diagnostics en langage naturel, contextualisés selon les métriques du système.

- Support multi-backend LLM : Possibilité de basculer dynamiquement entre plusieurs modèles IA pour une meilleure résilience.

- Export et visualisation des logs : Stockage des logs et graphiques dans un dossier dédié, facilement accessible pour analyses ultérieures.

- Simplicité et modularité : Code Python clair et documenté, facilement extensible pour intégrer d’autres métriques ou services.

Installation:

-Prérequis-
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

Clonez ce dépôt :
git clone https://github.com/ElSerda/DeadBot-Hackathon.git
cd DeadBot-Hackathon

Sur Windows :
.\venv\Scripts\activate

Installez les dépendances :
pip install -r requirements.txt

Lancez l'application :
python GUI.py

Utilisation:

- !diag : Affiche les diagnostics en temps réel du CPU et du GPU.

- !bench : Démarre un benchmark en temps réel, avec export des données et génération d'un graphique.

- !switch : Bascule entre les différents backends LLM disponibles (OpenAI, Ollama).

Démo Vidéo:

[text](https://www.youtube.com/watch?v=n7vQVmsQYU8)