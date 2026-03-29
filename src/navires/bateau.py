from __future__ import annotations
import pygame
from enum import Enum
from pathlib import Path
from plateau.case import Case


class Alignement(Enum):
    Horizontal = "Horizontal"
    Vertical = "Vertical"


class DirectionDeplacement(Enum):
    NORD = "NORD"
    SUD = "SUD"
    EST = "EST"
    OUEST = "OUEST"


class Bateau(pygame.sprite.Sprite):
    def __init__(self, nom: str, taille: int, image: Path, x=0, y=0, cell_size: int = 16):
        super().__init__()
        self.nom = nom
        self.taille = taille
        self.pointsDeVie = taille
        self.casesOccupees: list[Case] = []
        self.alignement = Alignement.Horizontal
        raw_image = pygame.image.load(image).convert_alpha()
        target_w = max(cell_size * taille, 1)
        target_h = max(cell_size - 2, 1)
        self.original_image = pygame.transform.smoothscale(raw_image, (target_w, target_h))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.centery = y
        self.row = 0
        self.column = 0

    def getNom(self) -> str:
        return self.nom

    def getTaille(self) -> int:
        return self.taille

    def getCasesOccupees(self) -> list[Case]:
        return self.casesOccupees

    def assignerCases(self, cases: list[Case]) -> None:
        self.casesOccupees = cases

    def encaisserTir(self) -> None:
        self.pointsDeVie -= 1

    def estCoule(self) -> bool:
        return self.pointsDeVie <= 0

    def orienter(self, alignement: Alignement) -> None:
        self.alignement = alignement
        angle = 0 if alignement == Alignement.Horizontal else 90
        center = self.rect.center
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=center)

    def calculerCasesApresDeplacement(self, dir: DirectionDeplacement, plateau: "Plateau") -> list[Case] | None:
        delta_row, delta_col = {
            DirectionDeplacement.NORD: (-1, 0),
            DirectionDeplacement.SUD: (1, 0),
            DirectionDeplacement.EST: (0, 1),
            DirectionDeplacement.OUEST: (0, -1),
        }[dir]
        new_row = self.row + delta_row
        new_col = self.column + delta_col
        return plateau.calculer_cases_pour_bateau(self, new_row, new_col, self.alignement)
