from joueurs.joueur import Joueur
from plateau.case import ResultatTir


class Partie:
    def __init__(self, joueur1: Joueur, joueur2: Joueur):
        self.joueur1 = joueur1
        self.joueur2 = joueur2
        self.joueurCourant = joueur1
        self.ToursResatants = 0
        self.Vainqueur = None

    def initialiser(self):
        self.joueurCourant = self.joueur1
        self.demarrerTour()

    def demarrer(self):
        self.initialiser()

    def demarrerTour(self):
        self.ToursResatants = max(1, self.calculerToursInitials(self.joueurCourant))

    def jouerTour(self, resultat_tir: ResultatTir | None = None) -> bool:
        """Consomme une action et retourne True si le même joueur continue."""
        if self.ToursResatants <= 0:
            self.demarrerTour()

        self.ToursResatants -= 1

        # Variante demandée: toucher ou couler accorde un tour supplémentaire.
        if resultat_tir in (ResultatTir.TOUCHE, ResultatTir.COULE):
            self.accorderTourSupplementaire()

        if self.estTerminee():
            self.determinerVainqueur()
            return False

        if self.ToursResatants > 0:
            return True

        self.passerAuJoueurSuivant()
        self.demarrerTour()
        return False

    def calculerToursInitials(self, j: Joueur) -> int:
        return 1 + self.calculerBonusFlotte(j)

    def calculerBonusFlotte(self, j: Joueur) -> int:
        if not j.getPlateau().aUnPorteAvionVivant():
            return 0
        return j.getPlateau().compterNaviresVivantsHorsPatrouilleurs()

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
