def jouer_tour(self):
    joueur = self.joueur_courant
    adversaire = self.joueurs[1] if joueur == self.joueurs[0] else self.joueurs[0]

    print(f"\nTour de {joueur}")
    if joueur.est_ia:
        choix = "1"
        print("IA choisit de tirer")
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