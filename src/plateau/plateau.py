from __future__ import annotations
import pygame
from enum import Enum
from plateau.case import Case, EtatCase, ResultatTir
from navires.bateau import Bateau, Alignement, DirectionDeplacement


class ResultatDeplacement(Enum):
    DEPLACE = "DEPLACE"
    BLOQUE = "BLOQUE"
    INVALIDE = "INVALIDE"


class Plateau:
    NB_LIGNES = 10
    NB_COLONNES = 10

    def __init__(self, x_loc=55, y_loc=160, grid_size=402, cell_width=40):
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.grid_size = grid_size
        self.cell_width = cell_width
        self.rect = pygame.Rect(x_loc, y_loc, grid_size, grid_size)
        self.surface = pygame.Surface((grid_size, grid_size))
        self.casesImportantes: list[Case] = []
        self.bateaux: list[Bateau] = []
        self.cells: list[Case] = []
        self.initialiserGrille()

    def initialiserGrille(self) -> None:
        self.cells = []
        for ligne in range(self.NB_LIGNES):
            for colonne in range(self.NB_COLONNES):
                x = self.x_loc + colonne * self.cell_width
                y = self.y_loc + ligne * self.cell_width
                case = Case(ligne, colonne, x, y, self.cell_width)
                case.rect = pygame.Rect(x, y, self.cell_width, self.cell_width)
                self.cells.append(case)

    def draw_grid(self):
        self.surface.fill((60, 145, 235))
        for i in range(self.NB_COLONNES + 1):
            offset = i * self.cell_width
            pygame.draw.line(self.surface, (0, 0, 0), (offset, 0), (offset, self.grid_size), 4)
            pygame.draw.line(self.surface, (0, 0, 0), (0, offset), (self.grid_size, offset), 4)

    def estDansGrille(self, ligne: int, colonne: int) -> bool:
        return 0 <= ligne < self.NB_LIGNES and 0 <= colonne < self.NB_COLONNES

    def getCase(self, ligne: int, colonne: int) -> Case | None:
        for cell in self.cells:
            if cell.ligne == ligne and cell.colonne == colonne:
                return cell
        return None

    def respecte_voisinage(self, cases_proposees: list[Case], bateau_actuel: Bateau) -> bool:
        """Vérifie qu'aucun autre bateau n'est à moins d'une case (8 directions)."""
        for case in cases_proposees:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    r, c = case.ligne + dr, case.colonne + dc
                    if self.estDansGrille(r, c):
                        voisine = self.getCase(r, c)
                        if voisine and voisine.bateau and voisine.bateau != bateau_actuel:
                            return False
        return True

    def calculer_cases_pour_bateau(self, b: Bateau, start_row: int, start_col: int, alignement: Alignement) -> list[
                                                                                                                   Case] | None:
        cases = []
        for i in range(b.taille):
            row = start_row + (0 if alignement == Alignement.Horizontal else i)
            col = start_col + (i if alignement == Alignement.Horizontal else 0)
            if not self.estDansGrille(row, col): return None
            case = self.getCase(row, col)
            if case is None or (case.bateau is not None and case.bateau != b): return None
            cases.append(case)
        return cases

    def placementValide(self, b: Bateau, cases: list[Case]) -> bool:
        """Validation finale incluant la règle de voisinage."""
        if cases is None or len(cases) != b.taille:
            return False
        return self.respecte_voisinage(cases, b)

    def placerBateau(self, b: Bateau, cases: list[Case]) -> None:
        if b not in self.bateaux: self.bateaux.append(b)
        for cell in self.cells:
            if cell.bateau == b: cell.retirerBateau()
        for c in cases:
            c.placerBateau(b)
            if c not in self.casesImportantes: self.casesImportantes.append(c)
        b.assignerCases(cases)
        b.row, b.column = cases[0].ligne, cases[0].colonne

    def tirer(self, cible: Case) -> ResultatTir:
        return cible.recevoirTir() if cible else ResultatTir.INVALIDE

    def deplacerBateau(self, b: Bateau, dir: DirectionDeplacement) -> ResultatDeplacement:
        if b is None: return ResultatDeplacement.INVALIDE
        if any(c.is_clicked for c in b.getCasesOccupees()): return ResultatDeplacement.BLOQUE
        nouvelles = b.calculerCasesApresDeplacement(dir, self)
        if nouvelles is None or not self.respecte_voisinage(nouvelles, b):
            return ResultatDeplacement.INVALIDE

        anciennes = list(b.getCasesOccupees())
        for c in anciennes: c.retirerBateau()
        self.placerBateau(b, nouvelles)
        return ResultatDeplacement.DEPLACE

    def tousLesBateauxCoules(self) -> bool:
        return all(b.estCoule() for b in self.bateaux) if self.bateaux else False