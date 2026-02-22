# juste pour le test, a supprimer
import random
import time


class Joueur:
    def __init__(self, nom, est_ia=False):
        self.nom = nom
        self.est_ia = est_ia
        self.tours_supplementaires = 0
        self.a_porte_avions = True

    def __str__(self):
        return self.nom

# juste pour le teste a supprimer
class Plateau:
    def __init__(self):
        self.navires_restants = 5 

    def tirer(self):
        résultat = random.choice(["raté", "touché", "coulé"])
        if résultat == "coulé":
            self.navires_restants -= 1
        return résultat
    def partie_terminee(self): #return true ou false
        return self.navires_restants <= 0


# ########  ########  ########  ########  ########  ########  ########  ########  ########
class Partie:
    def __init__(self, joueur1, joueur2): # initialise joueurs et crée plateau pour chacun 
        self.joueurs = [joueur1, joueur2]
        self.plateaux = {
            joueur1: Plateau(),
            joueur2: Plateau()
        }
        self.joueur_courant = joueur1

    def changer_joueur(self):   # gere les tour, alterne entre joueur 1 et 2
        self.joueur_courant = (
            self.joueurs[1] if self.joueur_courant == self.joueurs[0]
            else self.joueurs[0]
        )

    def jouer_tour(self):
        joueur = self.joueur_courant
        adversaire = self.joueurs[1] if joueur == self.joueurs[0] else self.joueurs[0]

        print(f"\nTour de {joueur}")
        if joueur.est_ia:
            choix = "1"
            print("IA choisit de tirer")
            time.sleep(2) #trop rapide sinon 
        else:
            choix = input("Choisir action (1 = Tirer, 2 = Déplacer) : ")

        if choix == "1":
            resultat = self.plateaux[adversaire].tirer()
            print(f"Résultat du tir : {resultat}")

            if resultat == "coulé":
                joueur.tours_supplementaires += 1
                print("Tour supplémentaire gagné !")

        elif choix == "2":
            print("Déplacement effectué (simulation)")
        else:
            print("Choix invalide")
            return  # on redemande le tour

        if joueur.tours_supplementaires > 0:
            joueur.tours_supplementaires -= 1
            print("Tour supplémentaire utilisé")
        else:
            self.changer_joueur()

    def lancer_partie(self):
        while True:
            self.jouer_tour()

            #fin de partie
            for joueur, plateau in self.plateaux.items():
                if plateau.partie_terminee():
                    perdant = joueur
                    gagnant = self.joueurs[1] if joueur == self.joueurs[0] else self.joueurs[0]
                    print(f"\n🎉 {gagnant} a gagné la partie !")
                    return


       
                