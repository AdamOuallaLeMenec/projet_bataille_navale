from joueurs.joueur import Joueur
from plateau.case import ResultatTir


class Partie:
    def __init__(self, joueur1: Joueur, joueur2: Joueur):
        self.joueur1 = joueur1
        self.joueur2 = joueur2
        self.joueurCourant = joueur1
        self.ToursRestants = 1
        self.Vainqueur = None

    def initialiser(self):
        self.joueurCourant = self.joueur1
        self.demarrerTour()

    def demarrer(self):
        self.initialiser()

    def demarrerTour(self):
        self.ToursRestants = self.calculerToursInitials(self.joueurCourant)

    def jouerTour(self, resultat_tir: ResultatTir | None = None) -> bool:
        """
        Une action valide consomme 1 tour.
        Si le joueur a encore des tours, il rejoue.
        Sinon on passe à l'adversaire.
        Si un navire ennemi est coulé, on ajoute 1 tour supplémentaire.
        """
        if resultat_tir == ResultatTir.COULE:
            self.accorderTourSupplementaire()

        self.ToursRestants -= 1

        if self.estTerminee():
            self.determinerVainqueur()
            return False

        if self.ToursRestants > 0:
            return True

        self.passerAuJoueurSuivant()
        self.demarrerTour()
        return False

    def calculerToursInitials(self, j: Joueur) -> int:
        return 1 + self.calculerBonusFlotte(j)

    def calculerBonusFlotte(self, j: Joueur) -> int:
        plateau = j.getPlateau()

        # Pas de bonus si aucun porte-avions vivant
        if not plateau.aUnPorteAvionVivant():
            return 0

        # Chaque navire vivant sauf patrouilleur donne +1
        return plateau.compterNaviresVivantsHorsPatrouilleurs()

    def accorderTourSupplementaire(self) -> None:
        self.ToursRestants += 1

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
