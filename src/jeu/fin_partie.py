from joueurs.joueur import Joueur


class Partie:
    def __init__(self, joueur1: Joueur, joueur2: Joueur):
        self.joueur1 = joueur1
        self.joueur2 = joueur2
        self.joueurCourant = joueur1
        self.ToursResatants = 0
        self.Vainqueur = None

    def initialiser(self):
        self.ToursResatants = self.calculerToursInitials(self.joueur1)

    def demarrer(self):
        self.initialiser()

    def demarrerTour(self):
        pass

    def jouerTour(self):
        pass

    def calculerToursInitials(self, j: Joueur) -> int:
        return 1 + self.calculerBonusFlotte(j)

    def calculerBonusFlotte(self, j: Joueur) -> int:
        return 1 if j.getPlateau().aUnPorteAvionVivant() else 0

    def accorderTourSupplementaire(self) -> None:
        self.ToursResatants += 1

    def passerAuJoueurSuivant(self):
        self.joueurCourant = self.joueur2 if self.joueurCourant == self.joueur1 else self.joueur1

    def estTerminee(self) -> bool:
        return self.joueur1.getPlateau().tousLesBateauxCoules() or self.joueur2.getPlateau().tousLesBateauxCoules()

    def determinerVainqueur(self) -> Joueur | None:
        if self.joueur1.getPlateau().tousLesBateauxCoules():
            self.Vainqueur = self.joueur2
        elif self.joueur2.getPlateau().tousLesBateauxCoules():
            self.Vainqueur = self.joueur1
        return self.Vainqueur
