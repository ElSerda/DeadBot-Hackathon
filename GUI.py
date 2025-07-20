import tkinter as tk
from tkinter.scrolledtext import ScrolledText
import threading
import time
import plugin
import csv
import datetime
import os
import json
from llm_backend import LLMBackend
import pandas as pd
import matplotlib.pyplot as plt
from llm_status import llm_status_command

llm_backend = LLMBackend()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🧠 DeadBot - G-Assist Diagnostic Tool")
        self.geometry("600x450")  # Augmentation de la hauteur pour accommoder les nouveaux boutons
        
        # Cadre principal pour la zone d'affichage
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        
        # Communication avec LLM

        # Zone d'affichage avec barre de défilement
        self.affichage = ScrolledText(
            main_frame, 
            state='disabled',
            wrap='word',
            bg="white",
            font=("Consolas", 10)
        )
        self.affichage.pack(fill=tk.BOTH, expand=True)
        
        # Cadre pour les boutons de test
        test_buttons_frame = tk.Frame(self)
        test_buttons_frame.pack(padx=10, pady=(5, 0), fill=tk.X)

        # Nouveau bouton !diag
        self.btn_diag = tk.Button(
            test_buttons_frame,
            text="diag",
            command=self.run_diag
        )
        self.btn_diag.pack(side=tk.LEFT, padx=(10, 5))
        
        # Nouveau bouton !bench
        self.btn_bench = tk.Button(
            test_buttons_frame,
            text="bench start",
            command=self.toggle_bench
        )
        self.btn_bench.pack(side=tk.LEFT)

        # Cadre pour les contrôles (bas)
        frame_bas = tk.Frame(self)
        frame_bas.pack(padx=10, pady=5, fill=tk.X)
        
        # Champ d'entrée
        self.entree = tk.Entry(
            frame_bas,
            font=("Arial", 12)
        )
        self.entree.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entree.focus()
        self.entree.bind("<Return>", self.envoyer_commande)
        
        # Bouton Envoyer
        self.bouton = tk.Button(
            frame_bas,
            text="Envoyer",
            command=self.envoyer_commande,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.bouton.pack(side=tk.RIGHT)

        # Variables bench
        self.bench_running = False
        self.bench_data = []
    
    def run_diag(self):
        """Commande !diag : appel réel au plugin"""
        self.log_msg("Système", "Commande !diag déclenchée")
        try:
            cpu_res = plugin.execute_cpu_diag_command()
            gpu_res = plugin.execute_gpu_diag_command()
            self.log_msg("CPU Diagnostic", cpu_res.get("diagnostic", "Pas de diagnostic"))
            self.log_msg("GPU Diagnostic", gpu_res.get("diagnostic", "Pas de diagnostic"))
        except Exception as e:
            self.log_msg("Erreur", f"Erreur lors du diag : {e}")
    
    def export_bench_log(self):
        if not self.bench_data:
            self.log_msg("Export", "Pas de données à exporter.")
            return None  # bien retourner None explicitement

        logs_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(logs_dir, exist_ok=True)

        filename = f"bench_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(logs_dir, filename)

        keys = self.bench_data[0].keys()
        try:
            with open(filepath, 'w', newline='') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(self.bench_data)
            self.log_msg("Export", f"Log benchmark exporté dans {filepath}")
            return filepath  # retourne le chemin créé ici
        except Exception as e:
            self.log_msg("Export", f"Erreur export benchmark : {e}")
            return None


    def toggle_bench(self):
        """Commande !bench : démarre / arrête le benchmark"""
        if not self.bench_running:
            self.bench_running = True
            self.btn_bench.config(text="bench stop")
            self.bench_data = []
            self.log_msg("Système", "Benchmark démarré...")

            def collect_bench():
                while self.bench_running:
                    try:
                        cpu_res = plugin.execute_cpu_diag_command()
                        gpu_res = plugin.execute_gpu_diag_command()
                        self.bench_data.append({
                            "cpu_usage_percent": cpu_res.get("cpu_usage_percent", 0),
                            "gpu_usage_percent": gpu_res.get("gpu_usage_percent", 0),
                            "timestamp": time.time()
                        })
                        time.sleep(1)
                    except Exception as e:
                        self.log_msg("Erreur", f"Erreur collecte bench : {e}")
                        break

            threading.Thread(target=collect_bench, daemon=True).start()
        else:
            self.bench_running = False
            self.btn_bench.config(text="bench start")
            self.log_msg("Système", "Benchmark arrêté. Analyse en cours...")

            if self.bench_data:
                max_cpu = max(d["cpu_usage_percent"] for d in self.bench_data)
                max_gpu = max(d["gpu_usage_percent"] for d in self.bench_data)
                self.log_msg("Résumé bench", f"CPU max {max_cpu:.1f}%, GPU max {max_gpu:.1f}%")

            # Export CSV
            csv_path = self.export_bench_log()

            # Génération graphique
            if csv_path:
                try:
                    df = pd.read_csv(csv_path)
                    plt.figure(figsize=(10,6))
                    plt.plot(df['timestamp'], df['cpu_usage_percent'], label='CPU Usage %')
                    plt.plot(df['timestamp'], df['gpu_usage_percent'], label='GPU Usage %')
                    plt.xlabel('Timestamp')
                    plt.ylabel('Usage %')
                    plt.title('Benchmark CPU & GPU Usage')
                    plt.legend()
                    graph_path = os.path.splitext(csv_path)[0] + ".png"
                    plt.savefig(graph_path)
                    plt.close()
                    self.log_msg("Export", f"Graphique benchmark généré : {graph_path}")
                except Exception as e:
                    self.log_msg("Erreur", f"Erreur génération graphique : {e}")
            else:
                self.log_msg("Résumé bench", "Aucune donnée collectée durant le benchmark.")

    def send_llm_query(self, user_message):
        try:
            cpu_status = plugin.execute_cpu_diag_command().get("diagnostic", "Aucun diagnostic CPU disponible")
            gpu_status = plugin.execute_gpu_diag_command().get("diagnostic", "Aucun diagnostic GPU disponible")
            prompt = (
                f"Voici l’état actuel du système :\n"
                f"CPU : {cpu_status}\n"
                f"GPU : {gpu_status}\n\n"
                f"Question de l’utilisateur : {user_message}\n"
                "Réponds en t’appuyant sur ces informations."
            )
            response = llm_backend.generate(prompt)
            self.log_msg("DeadBot", response)
        except Exception as e:
            self.log_msg("DeadBot", f"Erreur LLM : {e}")

    def simulate_gassist_plugin_call(self, command):
        """Simule un appel plugin G-Assist crowd-style (commande unique JSON)"""
        import plugin

        if not isinstance(command, str):
            print(f"[WARN] Command crowd must be a str, got {type(command)} → fallback to str(command)")
            command = str(command)

        tool_calls = [{"func": command}]
        input_json = {"tool_calls": tool_calls}

        # Simulation crowd: log l'entrée
        print(f"\n[SIMU G-ASSIST] Input JSON: {json.dumps(input_json)}")

        # Appelle la commande via le plugin crowd
        commands = {
            "cpu_diag": plugin.execute_cpu_diag_command,
            "gpu_diag": plugin.execute_gpu_diag_command,
            "perf_diag": plugin.execute_perf_diag_command if hasattr(plugin, "execute_perf_diag_command") else None,
            "initialize": lambda: {"success": True, "message": "DeadBot initialized."},
            "shutdown": lambda: {"success": True, "message": "DeadBot shutdown."}
        }
        handler = commands.get(command)
        if handler:
            response = handler()
        else:
            response = {"success": False, "message": f"Unknown command: {command}"}

        # Print crowd-style
        print(f"[SIMU G-ASSIST] WriteResponse (stdout crowd):\n{json.dumps(response, indent=2)}\n")
        self.log_msg("Simu G-Assist", f"Réponse crowd: {response}")
        return response


    def envoyer_commande(self, event=None):
        commande = self.entree.get().strip()
        if not commande:
            return
        
        self.log_msg(">>>", commande)
        self.entree.delete(0, tk.END)
        
        # Gestion commandes connues
        if commande.lower() == "!diag":
            self.run_diag()
        elif commande.lower() == "!bench":
            self.toggle_bench()
        elif commande.lower() == "!switch":
            if llm_backend.switch_model():
                self.log_msg("Système", f"Backend IA changé en {llm_backend.current_model}")
            else:
                self.log_msg("Système", "Impossible de changer de backend IA")
        elif commande.lower() == "!llm_status":
            response = llm_status_command()
            self.log_msg("LLM Status",{response})
        if commande.lower().startswith("/deadbot "):
            cmd = commande.split(" ", 1)[1].strip().lower()
            self.simulate_gassist_plugin_call(cmd)
            self.log_msg("Simu G-Assist", f"Appel simulé /deadbot {cmd} crowd")
            return
        else:
            # Toutes autres commandes passent par le LLM
            self.send_llm_query(commande)

    
    def log_msg(self, sender, message):
        """Affiche un message formaté dans la zone d'affichage"""
        self.affichage.configure(state='normal')
        self.affichage.insert(tk.END, f"{sender}: {message}\n")
        self.affichage.configure(state='disabled')
        self.affichage.see(tk.END)  # Défilement automatique

if __name__ == "__main__":
    app = Application()
    app.log_msg("Système", "Interface initialisée. Prêt à recevoir des commandes.")
    app.log_msg("Système", "Utilisez les boutons !diag et !bench.")
    app.mainloop()
