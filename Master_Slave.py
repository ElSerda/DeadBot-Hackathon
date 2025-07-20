from pathlib import Path

# Recréer les fichiers après reset
server_code = """
# deadbot_server.py
# Mode : Master - Reçoit les diagnostics des clients DeadBot en mode slave

import socket
import threading
import json

HOST = '0.0.0.0'  # écoute toutes les IP
PORT = 8765       # port de réception

def handle_client(conn, addr):
    print(f"[+] Connexion de {addr}")
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            try:
                payload = json.loads(data.decode())
                print(f"[DIAG] {addr} => {payload['level']} - {payload['summary']}")
            except Exception as e:
                print(f"[ERROR] Erreur de parsing: {e}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[SERVER] DeadBot Master en écoute sur {HOST}:{PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == '__main__':
    start_server()
"""

client_code = """
# deadbot_client.py
# Mode : Slave - Envoie les diagnostics vers un DeadBot Master

import socket
import time
import json
import random  # à remplacer par les vraies métriques plus tard

MASTER_IP = '127.0.0.1'  # à modifier
MASTER_PORT = 8765
INTERVAL = 5  # en secondes

def collect_metrics():
    # Ici on simule des métriques ; à remplacer par le perfscan réel
    cpu = random.uniform(30, 100)
    gpu = random.uniform(20, 90)
    alert_level = "INFO"
    if cpu > 90 or gpu > 90:
        alert_level = "CRITICAL"
    elif cpu > 75 or gpu > 75:
        alert_level = "WARNING"
    return {
        "cpu": round(cpu, 1),
        "gpu": round(gpu, 1),
        "level": alert_level,
        "summary": f"CPU {cpu:.1f}%, GPU {gpu:.1f}%"
    }

def send_diagnostics():
    while True:
        metrics = collect_metrics()
        if metrics["level"] != "INFO":
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((MASTER_IP, MASTER_PORT))
                    s.sendall(json.dumps(metrics).encode())
                    print(f"[PUSH] {metrics}")
            except Exception as e:
                print(f"[ERROR] Envoi échoué: {e}")
        time.sleep(INTERVAL)

if __name__ == '__main__':
    send_diagnostics()
"""

Path("deadbot_server.py").write_text(server_code, encoding="utf-8")
Path("deadbot_client.py").write_text(client_code, encoding="utf-8")
