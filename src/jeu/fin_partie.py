# juste pour le test, a supprimer
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
        résultat = "coulé"  # pour le test, on suppose que chaque tir coule un navire
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

        # choix fictif (tir par défaut)
        resultat = self.plateaux[adversaire].tirer()
        print(f"Résultat du tir : {resultat}")

        if resultat == "coulé":
            print("Navire coulé → tour supplémentaire")
            joueur.tours_supplementaires += 1

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
                    print(f"\n🎉 {self.joueur_courant} a gagné la partie !")
                    return
