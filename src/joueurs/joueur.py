from __future__ import annotations
from enum import Enum
from plateau.plateau import Plateau
from plateau.plateau import ResultatDeplacement
from plateau.case import Case, ResultatTir
from navires.bateau import Bateau, DirectionDeplacement


class ActionTour(Enum):
    Tirer = "Tirer"
    Deplacer = "Deplacer"


class Joueur:
    def __init__(self, nom: str, plateau: Plateau):
        self.nom = nom
        self.plateau = plateau

    def getNom(self) -> str:
        return self.nom

    def getPlateau(self) -> Plateau:
        return self.plateau

    def choisirAction(self) -> ActionTour:
        return ActionTour.Tirer

    def choisirCible(self, ennemi: "Joueur") -> Case | None:
        return None

    def choisirDeplacement(self) -> DirectionDeplacement:
        return DirectionDeplacement.EST

    def tirer(self, ennemi: "Joueur", cible: Case) -> ResultatTir:
        return ennemi.getPlateau().tirer(cible)

    def deplacer(self, bateau: Bateau, direction: DirectionDeplacement) -> ResultatDeplacement:
        return self.plateau.deplacerBateau(bateau, direction)

    def placerFlotte(self) -> None:
        pass


class JoueurHumain(Joueur):
    pass
