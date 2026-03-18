from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from navires.bateau import Bateau


class EtatCase(Enum):
    VIDE = "VIDE"
    OCCUPEE = "OCCUPEE"
    TOUCHEE = "TOUCHEE"
    RATEE = "RATEE"


class ResultatTir(Enum):
    RATE = "RATE"
    TOUCHE = "TOUCHE"
    COULE = "COULE"
    DEJA_TIRE = "DEJA_TIRE"
    INVALIDE = "INVALIDE"


class Case:
    def __init__(self, ligne: int, colonne: int, x_coord: int, y_coord: int, cell_width: int):
        self.ligne = ligne
        self.colonne = colonne
        self.etat = EtatCase.VIDE
        self.bateau = None
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.cell_width = cell_width
        self.rect = None
        self.is_clicked = False

    def estTouchee(self) -> bool:
        return self.etat == EtatCase.TOUCHEE

    def estOccupee(self) -> bool:
        return self.bateau is not None

    def estImportante(self) -> bool:
        return self.estOccupee() or self.is_clicked

    def placerBateau(self, b: "Bateau") -> None:
        self.bateau = b
        self.etat = EtatCase.OCCUPEE

    def retirerBateau(self) -> None:
        self.bateau = None
        self.etat = EtatCase.VIDE if not self.is_clicked else self.etat

    def recevoirTir(self) -> ResultatTir:
        if self.is_clicked:
            return ResultatTir.DEJA_TIRE

        self.is_clicked = True
        if self.bateau is None:
            self.etat = EtatCase.RATEE
            return ResultatTir.RATE

        self.etat = EtatCase.TOUCHEE
        self.bateau.encaisserTir()
        if self.bateau.estCoule():
            for c in self.bateau.getCasesOccupees():
                c.etat = EtatCase.TOUCHEE
            return ResultatTir.COULE
        return ResultatTir.TOUCHE
