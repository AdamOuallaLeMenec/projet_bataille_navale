import socket
import threading

class ReseauLocal:

    def __init__(self):
        self.connexion = None
        self.est_serveur = False
        self.serveur = None

    # ------------------------
    # CREER UNE PARTIE
    # ------------------------
    def creer_partie(self, host="0.0.0.0", port=5000):
        try:
            self.serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.serveur.bind((host, port))
            self.serveur.listen(1)
            print("Partie créée. En attente d'un joueur...")
            connexion, adresse = self.serveur.accept()
            connexion.setblocking(False)
            print("Joueur connecté :", adresse)
            self.connexion = connexion
            self.est_serveur = True
            return True
        except Exception as e:
            print("Erreur lors de la création de partie :", e)
            return False

    # ------------------------
    # REJOINDRE UNE PARTIE
    # ------------------------
    def rejoindre_partie(self, ip="127.0.0.1", port=5000):
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            print("Tentative de connexion au serveur...")
            client.connect((ip, port))
            client.setblocking(False)
            print("Connecté au serveur.")
            self.connexion = client
            self.est_serveur = False
            return True
        except Exception as e:
            print("Erreur lors de la connexion au serveur :", e)
            return False

    # ------------------------
    # ENVOYER MESSAGE
    # ------------------------
    def envoyer(self, message):
        if self.connexion:
            try:
                self.connexion.send((message + "\n").encode())
                return True
            except Exception:
                return False
        return False

    # ------------------------
    # RECEVOIR MESSAGE
    # ------------------------
    def recevoir(self):
        if self.connexion:
            try:
                message = self.connexion.recv(1024).decode()
                return message
            except BlockingIOError:
                return ""
            except Exception:
                return ""
        return ""

    # ------------------------
    # ECOUTE CONTINUE
    # ------------------------
    def ecouter(self, callback):
        def boucle():
            while True:
                try:
                    if self.connexion is None:
                        continue
                    message = self.connexion.recv(1024).decode()
                    if message:
                        callback(message)
                except Exception:
                    break

        thread = threading.Thread(target=boucle, daemon=True)
        thread.start()