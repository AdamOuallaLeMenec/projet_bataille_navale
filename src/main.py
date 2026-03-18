

from __future__ import annotations

from pathlib import Path
from enum import Enum
import itertools
import random
import sys
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN

BASE_DIR = Path(__file__).resolve().parent

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (60, 145, 235)
RED = (206, 10, 10)
GREY = (115, 108, 108)
DARK_GREY = (41, 41, 46)
GREEN = (36, 180, 78)
YELLOW = (240, 210, 60)
LIGHT_GREY = (200, 200, 200)
MENU_BLUE = (80, 110, 190)

WINDOW_W = 1180
WINDOW_H = 700
GRID_Y = 160
PLAYER_GRID_X = 55
ENEMY_GRID_X = 725
GRID_SIZE = 402
CELL_SIZE = 40

SHIPS = {
    "Porte-avion": [5, "Sprites/Battleship5.png"],
    "Cuirasse": [4, "Sprites/Cruiser4.png"],
    "Sous-marin": [4, "Sprites/Submarine3.png"],
    "Patrouilleur": [3, "Sprites/RescueShip3.png"],
    "Destroyer": [2, "Sprites/Destroyer2.png"],
}


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


class ResultatDeplacement(Enum):
    DEPLACE = "DEPLACE"
    BLOQUE = "BLOQUE"
    INVALIDE = "INVALIDE"


class ActionTour(Enum):
    Tirer = "Tirer"
    Deplacer = "Deplacer"


class DirectionDeplacement(Enum):
    NORD = "NORD"
    SUD = "SUD"
    EST = "EST"
    OUEST = "OUEST"


class Alignement(Enum):
    Horizontal = "Horizontal"
    Vertical = "Vertical"


pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

window_surface = pygame.display.set_mode((WINDOW_W, WINDOW_H), 0, 32)
pygame.display.set_caption("Bataille navale")


def asset_path(relative: str) -> Path:
    return BASE_DIR / relative


def load_font(relative: str, size: int):
    try:
        return pygame.font.Font(asset_path(relative), size)
    except Exception:
        return pygame.font.SysFont(None, size)


title_font = load_font("Fonts/INVASION2000.TTF", 44)
menu_title_font = load_font("Fonts/INVASION2000.TTF", 58)
header_font = load_font("Fonts/ARCADECLASSIC.TTF", 30)
body_font = pygame.font.SysFont(None, 31)
small_font = pygame.font.SysFont(None, 26)
button_font = pygame.font.SysFont(None, 28)
menu_font = pygame.font.SysFont(None, 40)


class Case:
    def __init__(self, ligne: int, colonne: int, x_coord: int, y_coord: int, cell_width: int):
        self.ligne = ligne
        self.colonne = colonne
        self.etat = EtatCase.VIDE
        self.bateau = None
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.cell_width = cell_width
        self.rect = pygame.Rect(x_coord, y_coord, cell_width, cell_width)
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


class Bateau(pygame.sprite.Sprite):
    def __init__(self, nom: str, taille: int, image: Path, x=0, y=0):
        super().__init__()
        self.nom = nom
        self.taille = taille
        self.pointsDeVie = taille
        self.casesOccupees: list[Case] = []
        self.alignement = Alignement.Horizontal
        self.original_image = pygame.image.load(image).convert_alpha()
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


class Plateau:
    NB_LIGNES = 10
    NB_COLONNES = 10

    def __init__(self, x_loc=PLAYER_GRID_X, y_loc=GRID_Y):
        self.x_loc = x_loc
        self.y_loc = y_loc
        self.grid_size = GRID_SIZE
        self.cell_width = CELL_SIZE
        self.rect = pygame.Rect(x_loc, y_loc, GRID_SIZE, GRID_SIZE)
        self.surface = pygame.Surface((GRID_SIZE, GRID_SIZE))
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
                self.cells.append(Case(ligne, colonne, x, y, self.cell_width))
        self.draw_grid()

    def draw_grid(self):
        self.surface.fill(BLUE)
        for i in range(self.NB_COLONNES + 1):
            offset = i * self.cell_width
            pygame.draw.line(self.surface, BLACK, (offset, 0), (offset, self.grid_size), 4)
            pygame.draw.line(self.surface, BLACK, (0, offset), (self.grid_size, offset), 4)

    def estDansGrille(self, ligne: int, colonne: int) -> bool:
        return 0 <= ligne < self.NB_LIGNES and 0 <= colonne < self.NB_COLONNES

    def getCase(self, ligne: int, colonne: int) -> Case | None:
        for cell in self.cells:
            if cell.ligne == ligne and cell.colonne == colonne:
                return cell
        return None

    def get_cell_from_pixel(self, x: int, y: int) -> Case | None:
        for cell in self.cells:
            if cell.rect.collidepoint(x, y):
                return cell
        return None

    def enregistrerCase(self, c: Case) -> None:
        if c not in self.casesImportantes:
            self.casesImportantes.append(c)

    def supprimerCaseSiVide(self, ligne: int, colonne: int) -> None:
        case = self.getCase(ligne, colonne)
        if case and not case.estImportante() and case in self.casesImportantes:
            self.casesImportantes.remove(case)

    def calculer_cases_pour_bateau(self, b: Bateau, start_row: int, start_col: int, alignement: Alignement) -> list[Case] | None:
        cases = []
        for i in range(b.taille):
            row = start_row + (0 if alignement == Alignement.Horizontal else i)
            col = start_col + (i if alignement == Alignement.Horizontal else 0)
            if not self.estDansGrille(row, col):
                return None
            case = self.getCase(row, col)
            if case is None:
                return None
            if case.bateau is not None and case.bateau != b:
                return None
            cases.append(case)
        return cases

    def placementValide(self, b: Bateau, cases: list[Case]) -> bool:
        return cases is not None and len(cases) == b.taille

    def placerBateau(self, b: Bateau, cases: list[Case]) -> None:
        if b not in self.bateaux:
            self.bateaux.append(b)
        for cell in self.cells:
            if cell.bateau == b:
                cell.retirerBateau()
        for c in cases:
            c.placerBateau(b)
            self.enregistrerCase(c)
        b.assignerCases(cases)
        b.row = cases[0].ligne
        b.column = cases[0].colonne
        anchor = cases[0]
        if b.alignement == Alignement.Horizontal:
            b.rect.midleft = anchor.rect.midleft
        else:
            b.rect.midtop = anchor.rect.midtop

    def tirer(self, cible: Case) -> ResultatTir:
        if cible is None:
            return ResultatTir.INVALIDE
        return cible.recevoirTir()

    def deplacementValide(self, b: Bateau, dir: DirectionDeplacement) -> bool:
        nouvelles = b.calculerCasesApresDeplacement(dir, self)
        return nouvelles is not None

    def mettreAJourCasesApresDeplacement(self, anciennes: list[Case], nouvelles: list[Case]) -> None:
        bateau = anciennes[0].bateau if anciennes else None
        for c in anciennes:
            c.retirerBateau()
        if bateau:
            self.placerBateau(bateau, nouvelles)

    def deplacerBateau(self, b: Bateau, dir: DirectionDeplacement) -> ResultatDeplacement:
        if b is None:
            return ResultatDeplacement.INVALIDE
        if any(c.is_clicked for c in b.getCasesOccupees()):
            return ResultatDeplacement.BLOQUE
        nouvelles = b.calculerCasesApresDeplacement(dir, self)
        if nouvelles is None:
            return ResultatDeplacement.INVALIDE
        anciennes = list(b.getCasesOccupees())
        self.mettreAJourCasesApresDeplacement(anciennes, nouvelles)
        return ResultatDeplacement.DEPLACE

    def aUnPorteAvionVivant(self) -> bool:
        return any(b.nom == "Porte-avion" and not b.estCoule() for b in self.bateaux)

    def compterNaviresVivantsHorsPatrouilleurs(self) -> int:
        return sum(1 for b in self.bateaux if b.nom != "Patrouilleur" and not b.estCoule())

    def tousLesBateauxCoules(self) -> bool:
        return all(b.estCoule() for b in self.bateaux) if self.bateaux else False


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


class JoueurVirtuel(Joueur):
    def __init__(self, nom: str, plateau: Plateau, difficulty="medium"):
        super().__init__(nom, plateau)
        self.derniereCaseTouchee: tuple[int, int] | None = None
        self.second_hit: tuple[int, int] | None = None
        self.tested_no_hit = None
        self.tested_no_hit_2 = None
        self.difficulty = difficulty
        self.available_cells = self._populate_available_cells()

    def _populate_available_cells(self):
        return [cell for cell in itertools.product(range(10), range(10))]

    def prendreDecision(self, ennemi: Joueur) -> ActionTour:
        return ActionTour.Tirer

    def choisirCibleIntelligente(self, ennemi: Joueur) -> Case:
        row, col = self.enemy_turn()
        return ennemi.getPlateau().getCase(row, col)

    def trouverCasesAdjacentesValides(self, ennemi: Joueur, centre: Case):
        plateau = ennemi.getPlateau()
        coords = [
            (centre.ligne + 1, centre.colonne),
            (centre.ligne - 1, centre.colonne),
            (centre.ligne, centre.colonne + 1),
            (centre.ligne, centre.colonne - 1),
        ]
        return [plateau.getCase(r, c) for r, c in coords if plateau.estDansGrille(r, c)]

    def choisirDirectionDefensive(self) -> DirectionDeplacement:
        return random.choice(list(DirectionDeplacement))

    def choisirDirectionOffensive(self, ennemi: Joueur) -> DirectionDeplacement:
        return random.choice(list(DirectionDeplacement))

    def randomise_ships(self):
        available_cells = [cell for cell in itertools.product(range(10), range(10))]
        for ship in self.plateau.bateaux:
            while True:
                alignement = random.choice([Alignement.Horizontal, Alignement.Vertical])
                ship.orienter(alignement)
                if alignement == Alignement.Horizontal:
                    row = random.randint(0, 9)
                    col = random.randint(0, 10 - ship.taille)
                else:
                    row = random.randint(0, 10 - ship.taille)
                    col = random.randint(0, 9)
                coords = []
                for i in range(ship.taille):
                    r = row + (0 if alignement == Alignement.Horizontal else i)
                    c = col + (i if alignement == Alignement.Horizontal else 0)
                    coords.append((r, c))
                if all(coord in available_cells for coord in coords):
                    cases = [self.plateau.getCase(r, c) for r, c in coords]
                    self.plateau.placerBateau(ship, cases)
                    available_cells = [cell for cell in available_cells if cell not in coords]
                    break

    def reset_hit_logs(self):
        self.derniereCaseTouchee = None
        self.second_hit = None
        self.tested_no_hit = None
        self.tested_no_hit_2 = None

    def random_pick(self):
        return random.choice(self.available_cells)

    def pick_target_after_first_hit(self):
        next_targets = [
            (self.derniereCaseTouchee[0] + 1, self.derniereCaseTouchee[1]),
            (self.derniereCaseTouchee[0] - 1, self.derniereCaseTouchee[1]),
            (self.derniereCaseTouchee[0], self.derniereCaseTouchee[1] + 1),
            (self.derniereCaseTouchee[0], self.derniereCaseTouchee[1] - 1),
        ]
        verified = [cell for cell in next_targets if cell in self.available_cells]
        if not verified:
            return self.random_pick()
        return verified[0] if self.difficulty == "hard" else random.choice(verified)

    def pick_target_after_second_hit(self, check_distance=1):
        if self.derniereCaseTouchee[0] == self.second_hit[0]:
            next_targets = [
                (self.derniereCaseTouchee[0], max(self.derniereCaseTouchee[1], self.second_hit[1]) + check_distance),
                (self.derniereCaseTouchee[0], min(self.derniereCaseTouchee[1], self.second_hit[1]) - check_distance),
            ]
        else:
            next_targets = [
                (max(self.derniereCaseTouchee[0], self.second_hit[0]) + check_distance, self.derniereCaseTouchee[1]),
                (min(self.derniereCaseTouchee[0], self.second_hit[0]) - check_distance, self.derniereCaseTouchee[1]),
            ]
        verified = [cell for cell in next_targets if cell in self.available_cells]
        if verified:
            return verified[0] if self.difficulty == "hard" else random.choice(verified)
        if self.tested_no_hit_2:
            self.second_hit = None
            return self.enemy_turn()
        return self.pick_target_after_second_hit(check_distance + 1)

    def enemy_turn(self):
        if self.difficulty == "easy":
            pick = self.random_pick()
        elif not self.derniereCaseTouchee:
            pick = self.random_pick()
        elif self.tested_no_hit_2:
            self.second_hit = None
            pick = self.pick_target_after_first_hit()
        elif self.derniereCaseTouchee and not self.second_hit:
            pick = self.pick_target_after_first_hit()
        else:
            pick = self.pick_target_after_second_hit()
        self.available_cells.remove(pick)
        return pick


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


class CellHit(pygame.sprite.Sprite):
    def __init__(self, image: Path, rect_center):
        super().__init__()
        self.image = pygame.image.load(image).convert_alpha()
        self.rect = self.image.get_rect(center=(rect_center[0] + 1, rect_center[1] + 1))


class TextButton:
    def __init__(self, name: str, text: str, x: int, y: int, w: int, h: int, fill=LIGHT_GREY):
        self.name = name
        self.text = text
        self.rect = pygame.Rect(x, y, w, h)
        self.fill = fill

    def draw(self, active=False):
        color = YELLOW if active else self.fill
        pygame.draw.rect(window_surface, color, self.rect, border_radius=12)
        pygame.draw.rect(window_surface, BLACK, self.rect, 3, border_radius=12)
        label = button_font.render(self.text, True, BLACK)
        window_surface.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, pos) -> bool:
        return self.rect.collidepoint(pos)


def draw_centered_text(text, font, y, color=BLACK):
    surface = font.render(text, True, color)
    window_surface.blit(surface, surface.get_rect(center=(WINDOW_W // 2, y)))


def draw_lines():
    pygame.draw.line(window_surface, DARK_GREY, (10, 10), (1170, 10), 3)
    pygame.draw.line(window_surface, DARK_GREY, (1170, 10), (1170, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (1170, 690), (10, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (10, 10), (10, 690), 3)
    pygame.draw.line(window_surface, DARK_GREY, (10, 600), (1170, 600), 3)


def display_headers(turn_mode: ActionTour, alignement: Alignement):
    draw_centered_text("Bataille Navale", title_font, 42)
    player_text = header_font.render("GRILLE JOUEUR", True, BLACK)
    enemy_text = header_font.render("GRILLE ENNEMIE", True, BLACK)
    mode_text = body_font.render(f"Mode actuel : {'TIR' if turn_mode == ActionTour.Tirer else 'DEPLACEMENT'}", True, BLACK)
    axis_text = small_font.render(f"Sens de deplacement : {alignement.value}", True, BLACK)
    window_surface.blit(player_text, player_text.get_rect(center=(255, 132)))
    window_surface.blit(enemy_text, enemy_text.get_rect(center=(925, 132)))
    window_surface.blit(mode_text, mode_text.get_rect(center=(WINDOW_W // 2, 85)))
    window_surface.blit(axis_text, axis_text.get_rect(center=(WINDOW_W // 2, 115)))


def display_instruction(text, color=WHITE):
    panel = pygame.Rect(25, 612, 1130, 65)
    pygame.draw.rect(window_surface, DARK_GREY, panel, border_radius=8)
    label = body_font.render(text, True, color)
    window_surface.blit(label, label.get_rect(center=panel.center))


def create_fleet_sprites() -> pygame.sprite.Group:
    group = pygame.sprite.Group()
    ship_y = 205
    ship_x = 485
    for ship_name, (length, rel_path) in SHIPS.items():
        group.add(Bateau(ship_name, length, asset_path(rel_path), ship_x, ship_y))
        ship_y += 46
    return group


def create_enemy_fleet() -> list[Bateau]:
    lst = []
    for ship_name, (length, rel_path) in SHIPS.items():
        lst.append(Bateau(ship_name, length, asset_path(rel_path)))
    return lst


def get_ship_by_name(ship_group, ship_name: str) -> Bateau | None:
    for ship in ship_group:
        if ship.nom == ship_name:
            return ship
    return None


def refresh_screen(player_plateau, enemy_plateau, ship_list, hit_list, buttons, instruction, turn_mode, alignement, selected=None):
    window_surface.fill(GREY)
    draw_lines()
    player_plateau.draw_grid()
    enemy_plateau.draw_grid()
    window_surface.blit(player_plateau.surface, player_plateau.rect)
    window_surface.blit(enemy_plateau.surface, enemy_plateau.rect)
    display_headers(turn_mode, alignement)

    for btn_name, btn in buttons.items():
        active = False
        if btn_name == "action_tir" and turn_mode == ActionTour.Tirer:
            active = True
        if btn_name == "action_move" and turn_mode == ActionTour.Deplacer:
            active = True
        if btn_name == "axis" and alignement == Alignement.Vertical:
            active = True
        btn.draw(active)

    if "menu" in buttons:
        helper = small_font.render("Retour menu", True, BLACK)
        window_surface.blit(helper, helper.get_rect(center=(buttons["menu"].rect.centerx, buttons["menu"].rect.bottom + 12)))

    hit_list.draw(window_surface)
    ship_list.draw(window_surface)
    if selected is not None:
        pygame.draw.rect(window_surface, YELLOW, selected.rect.inflate(8, 8), 4, border_radius=6)

    display_instruction(instruction)
    pygame.display.update()


def pixel_to_direction(ship: Bateau, target: Case) -> DirectionDeplacement | None:
    dr = target.ligne - ship.row
    dc = target.colonne - ship.column
    if (dr, dc) == (-1, 0):
        return DirectionDeplacement.NORD
    if (dr, dc) == (1, 0):
        return DirectionDeplacement.SUD
    if (dr, dc) == (0, 1):
        return DirectionDeplacement.EST
    if (dr, dc) == (0, -1):
        return DirectionDeplacement.OUEST
    return None


def play_sound(effect_type):
    sound_map = {
        "hit": ["Sounds/boom1.mp3", "Sounds/boom2.mp3", "Sounds/boom3.mp3"],
        "miss": ["Sounds/splash1.mp3", "Sounds/splash2.mp3", "Sounds/splash3.mp3"],
        "sink": "Sounds/sink.mp3",
    }
    try:
        if not pygame.mixer.get_init():
            return
        if effect_type in ("hit", "miss"):
            sound = pygame.mixer.Sound(asset_path(random.choice(sound_map[effect_type])))
        else:
            sound = pygame.mixer.Sound(asset_path(sound_map[effect_type]))
        sound.play()
    except Exception:
        pass


def setup_buttons():
    return {
        "menu": TextButton("menu", "MENU", 22, 22, 100, 42, MENU_BLUE),
        "rotate": TextButton("rotate", "Rotation", 490, 470, 200, 52),
        "action_tir": TextButton("action_tir", "Tir", 430, 535, 100, 46),
        "action_move": TextButton("action_move", "Deplacement", 540, 535, 170, 46),
        "axis": TextButton("axis", "H / V", 720, 535, 90, 46),
        "lock": TextButton("lock", "Valider", 520, 535, 140, 46),
    }


def setup_menu_buttons():
    return {
        "local": TextButton("local", "Jouer localement", 110, 230, 320, 58),
        "lan": TextButton("lan", "Meme reseau local", 110, 305, 320, 58),
        "ia": TextButton("ia", "Jouer contre l'IA", 110, 380, 320, 58),
        "easy": TextButton("easy", "IA facile", 740, 255, 230, 54),
        "medium": TextButton("medium", "IA moyenne", 740, 325, 230, 54),
        "hard": TextButton("hard", "IA difficile", 740, 395, 230, 54),
        "start": TextButton("start", "Lancer la partie", 420, 510, 340, 62, GREEN),
    }


def run_main_menu():
    buttons = setup_menu_buttons()
    mode = "ia"
    difficulty = "medium"
    info = "Choisissez un mode et lancez la partie."
    clock = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos
                if buttons["local"].clicked(pos):
                    mode = "local"
                    info = "Mode local selectionne. L'implementation complete sera la prochaine etape."
                elif buttons["lan"].clicked(pos):
                    mode = "lan"
                    info = "Mode reseau local prepare dans le menu, pas encore implemente."
                elif buttons["ia"].clicked(pos):
                    mode = "ia"
                    info = "Mode contre l'IA selectionne."
                elif buttons["easy"].clicked(pos):
                    difficulty = "easy"
                    info = "Difficulte facile selectionnee."
                elif buttons["medium"].clicked(pos):
                    difficulty = "medium"
                    info = "Difficulte moyenne selectionnee."
                elif buttons["hard"].clicked(pos):
                    difficulty = "hard"
                    info = "Difficulte difficile selectionnee."
                elif buttons["start"].clicked(pos):
                    return {"mode": mode, "difficulty": difficulty}

        window_surface.fill(GREY)
        draw_lines()
        draw_centered_text("Bataille Navale", menu_title_font, 95)
        draw_centered_text("Menu principal", body_font, 155)
        draw_centered_text("Modes", body_font, 195)

        for name, btn in buttons.items():
            active = (name == mode) or (name == difficulty)
            if name == "start":
                active = True
            btn.draw(active)

        info_panel = pygame.Rect(120, 590, 940, 52)
        pygame.draw.rect(window_surface, DARK_GREY, info_panel, border_radius=8)
        surf = small_font.render(info, True, WHITE)
        window_surface.blit(surf, surf.get_rect(center=info_panel.center))
        pygame.display.update()
        clock.tick(30)


def lock_in_ships(player: JoueurHumain, ship_group) -> tuple[bool, str]:
    player.plateau.bateaux.clear()
    for cell in player.plateau.cells:
        cell.bateau = None
        cell.is_clicked = False
        cell.etat = EtatCase.VIDE

    for ship in ship_group:
        if ship.alignement == Alignement.Horizontal:
            anchor = player.plateau.get_cell_from_pixel(ship.rect.left + 2, ship.rect.centery)
        else:
            anchor = player.plateau.get_cell_from_pixel(ship.rect.centerx, ship.rect.top + 2)

        if anchor is None:
            return True, "Tous les navires doivent etre places dans la grille."

        cases = player.plateau.calculer_cases_pour_bateau(ship, anchor.ligne, anchor.colonne, ship.alignement)
        if not player.plateau.placementValide(ship, cases):
            return True, "Placement invalide ou chevauchement de navires."

        player.plateau.placerBateau(ship, cases)

    total_cells = len([c for c in player.plateau.cells if c.bateau is not None])
    expected = sum(v[0] for v in SHIPS.values())
    if total_cells != expected:
        return True, "Tous les navires doivent etre places correctement."

    return False, "Flotte validee. La partie commence."


def set_up_player_ships(player: JoueurHumain, enemy: JoueurVirtuel, ship_group, hit_list):
    buttons = setup_buttons()
    selected = None
    dragging = False
    offset_x = 0
    offset_y = 0
    instruction = "Placez les navires puis cliquez sur Valider. Rotation au milieu."
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos
                if buttons["menu"].clicked(pos):
                    return False
                if buttons["rotate"].clicked(pos) and selected is not None:
                    new_align = Alignement.Vertical if selected.alignement == Alignement.Horizontal else Alignement.Horizontal
                    selected.orienter(new_align)
                    continue
                if buttons["lock"].clicked(pos):
                    still_setup, instruction = lock_in_ships(player, ship_group)
                    if not still_setup:
                        return True
                for ship in reversed(ship_group.sprites()):
                    if ship.rect.collidepoint(pos):
                        selected = ship
                        dragging = True
                        offset_x = ship.rect.x - pos[0]
                        offset_y = ship.rect.y - pos[1]
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging and selected is not None:
                selected.rect.x = event.pos[0] + offset_x
                selected.rect.y = event.pos[1] + offset_y

        refresh_screen(
            player.plateau,
            enemy.plateau,
            ship_group,
            hit_list,
            {k: v for k, v in buttons.items() if k in ["menu", "rotate", "lock"]},
            instruction,
            ActionTour.Tirer,
            Alignement.Horizontal,
            selected,
        )
        clock.tick(30)


def apply_hit_to_enemy(player: JoueurHumain, enemy: JoueurVirtuel, cible: Case, hit_list, ship_group) -> tuple[str, bool, bool]:
    resultat = player.tirer(enemy, cible)
    center = cible.rect.center

    if resultat == ResultatTir.DEJA_TIRE:
        return "Cette case a deja ete visee.", True, False

    if resultat in (ResultatTir.TOUCHE, ResultatTir.COULE):
        hit_list.add(CellHit(asset_path("Sprites/hit.png"), center))
        play_sound("sink" if resultat == ResultatTir.COULE else "hit")
        if enemy.plateau.tousLesBateauxCoules():
            return "Tous les navires ennemis sont coules. Victoire !", True, True
        return ("Touche ! Vous rejouez." if resultat == ResultatTir.TOUCHE else "Coule ! Vous rejouez."), True, False

    hit_list.add(CellHit(asset_path("Sprites/miss.png"), center))
    play_sound("miss")
    return "Rate. L'ennemi joue.", False, False


def enemy_take_turn(enemy: JoueurVirtuel, player: JoueurHumain, hit_list) -> tuple[str, bool]:
    extra_turn = True
    instruction = ""
    while extra_turn:
        cible = enemy.choisirCibleIntelligente(player)
        resultat = enemy.tirer(player, cible)
        center = cible.rect.center

        if resultat in (ResultatTir.TOUCHE, ResultatTir.COULE):
            hit_list.add(CellHit(asset_path("Sprites/hit.png"), center))
            if not enemy.derniereCaseTouchee:
                enemy.derniereCaseTouchee = (cible.ligne, cible.colonne)
            elif enemy.second_hit != (cible.ligne, cible.colonne):
                enemy.second_hit = (cible.ligne, cible.colonne)

            play_sound("sink" if resultat == ResultatTir.COULE else "hit")
            instruction = f"L'ennemi a {'coule' if resultat == ResultatTir.COULE else 'touche'} un de vos navires. Il rejoue."

            if resultat == ResultatTir.COULE:
                enemy.reset_hit_logs()

            if player.plateau.tousLesBateauxCoules():
                return "Tous vos navires sont coules. Defaite !", True

            extra_turn = True
        else:
            hit_list.add(CellHit(asset_path("Sprites/miss.png"), center))
            play_sound("miss")
            if enemy.derniereCaseTouchee and enemy.second_hit:
                if not enemy.tested_no_hit:
                    enemy.tested_no_hit = (cible.ligne, cible.colonne)
                else:
                    enemy.tested_no_hit_2 = (cible.ligne, cible.colonne)
            instruction = "L'ennemi a rate. A vous de jouer."
            extra_turn = False

        refresh_screen(
            player.plateau,
            enemy.plateau,
            pygame.sprite.Group(player.plateau.bateaux),
            hit_list,
            current_buttons,
            instruction,
            current_turn_mode[0],
            current_alignement[0],
        )
        pygame.time.wait(800)

    return instruction, False


def show_game_over(text: str):
    window_surface.fill(GREY)
    draw_lines()
    draw_centered_text(text, menu_title_font, 240, RED if "Victoire" in text else BLACK)
    draw_centered_text("Cliquez pour revenir au menu.", body_font, 340)
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                waiting = False


current_buttons = {}
current_turn_mode = [ActionTour.Tirer]
current_alignement = [Alignement.Horizontal]


def main():
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.load(asset_path("Sounds/valkyries.mid"))
            pygame.mixer.music.play(-1)
    except Exception:
        pass

    while True:
        menu_choice = run_main_menu()

        player_plateau = Plateau(PLAYER_GRID_X, GRID_Y)
        enemy_plateau = Plateau(ENEMY_GRID_X, GRID_Y)

        joueur1 = JoueurHumain("Joueur", player_plateau)
        joueur2 = JoueurVirtuel("IA", enemy_plateau, difficulty=menu_choice["difficulty"])

        partie = Partie(joueur1, joueur2)
        partie.demarrer()

        ship_group = create_fleet_sprites()
        enemy_ships = create_enemy_fleet()
        joueur2.plateau.bateaux = enemy_ships
        joueur2.randomise_ships()

        hit_list = pygame.sprite.Group()

        if not set_up_player_ships(joueur1, joueur2, ship_group, hit_list):
            continue

        joueur1.plateau.bateaux = list(ship_group)
        game_ship_group = pygame.sprite.Group(joueur1.plateau.bateaux)

        buttons = setup_buttons()
        global current_buttons
        current_buttons = {k: v for k, v in buttons.items() if k in ["menu", "rotate", "action_tir", "action_move", "axis"]}

        turn_mode = ActionTour.Tirer
        alignement_move = Alignement.Horizontal
        current_turn_mode[0] = turn_mode
        current_alignement[0] = alignement_move

        selected_ship_name = None
        instruction = "Votre tour : tirez sur la grille ennemie ou choisissez Deplacement."
        clock = pygame.time.Clock()

        playing = True
        while playing:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == MOUSEBUTTONDOWN:
                    pos = event.pos

                    if current_buttons["menu"].clicked(pos):
                        playing = False
                        break

                    elif current_buttons["rotate"].clicked(pos):
                        if turn_mode == ActionTour.Deplacer and selected_ship_name:
                            ship = get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship:
                                new_align = Alignement.Vertical if ship.alignement == Alignement.Horizontal else Alignement.Horizontal
                                ship.orienter(new_align)
                                anchor_case = ship.getCasesOccupees()[0] if ship.getCasesOccupees() else None
                                if anchor_case:
                                    cases = joueur1.plateau.calculer_cases_pour_bateau(ship, anchor_case.ligne, anchor_case.colonne, new_align)
                                    if cases and joueur1.plateau.placementValide(ship, cases):
                                        joueur1.plateau.placerBateau(ship, cases)
                                        instruction = f"{ship.nom} pivote en {new_align.value}."
                                    else:
                                        ship.orienter(Alignement.Horizontal if new_align == Alignement.Vertical else Alignement.Vertical)
                                        instruction = "Rotation impossible ici."

                    elif current_buttons["action_tir"].clicked(pos):
                        turn_mode = ActionTour.Tirer
                        current_turn_mode[0] = turn_mode
                        selected_ship_name = None
                        instruction = "Mode tir actif. Cliquez sur la grille ennemie."

                    elif current_buttons["action_move"].clicked(pos):
                        turn_mode = ActionTour.Deplacer
                        current_turn_mode[0] = turn_mode
                        instruction = "Mode deplacement actif : choisissez un navire puis une case adjacente."

                    elif current_buttons["axis"].clicked(pos):
                        alignement_move = Alignement.Vertical if alignement_move == Alignement.Horizontal else Alignement.Horizontal
                        current_alignement[0] = alignement_move
                        instruction = f"Sens de deplacement : {alignement_move.value}."

                    elif turn_mode == ActionTour.Tirer and enemy_plateau.rect.collidepoint(pos):
                        cell = enemy_plateau.get_cell_from_pixel(*pos)
                        if cell is not None:
                            instruction, extra_turn, finished = apply_hit_to_enemy(joueur1, joueur2, cell, hit_list, game_ship_group)
                            if finished:
                                refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list, current_buttons, instruction, turn_mode, alignement_move)
                                pygame.time.wait(1200)
                                show_game_over("Victoire !")
                                playing = False
                                break

                            if not extra_turn:
                                instruction, defeat = enemy_take_turn(joueur2, joueur1, hit_list)
                                if defeat:
                                    refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list, current_buttons, instruction, turn_mode, alignement_move)
                                    pygame.time.wait(1200)
                                    show_game_over("Defaite !")
                                    playing = False
                                    break

                    elif turn_mode == ActionTour.Deplacer and player_plateau.rect.collidepoint(pos):
                        cell = player_plateau.get_cell_from_pixel(*pos)

                        if cell is None:
                            instruction = "Case invalide."

                        elif selected_ship_name is None:
                            if cell.bateau is None:
                                instruction = "Choisissez d'abord un de vos navires."
                            else:
                                selected_ship_name = cell.bateau.nom
                                instruction = f"{selected_ship_name} selectionne. Cliquez sur une case adjacente."

                        else:
                            ship = get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship is None:
                                selected_ship_name = None
                                instruction = "Navire introuvable."
                            else:
                                if ship.alignement != alignement_move:
                                    old_align = ship.alignement
                                    ship.orienter(alignement_move)
                                    anchor_case = ship.getCasesOccupees()[0]
                                    rotated_cases = joueur1.plateau.calculer_cases_pour_bateau(
                                        ship, anchor_case.ligne, anchor_case.colonne, alignement_move
                                    )
                                    if rotated_cases and joueur1.plateau.placementValide(ship, rotated_cases):
                                        joueur1.plateau.placerBateau(ship, rotated_cases)
                                    else:
                                        ship.orienter(old_align)

                                direction = pixel_to_direction(ship, cell)

                                if direction is None:
                                    instruction = "Le deplacement doit etre d'une seule case adjacente."
                                else:
                                    resultat = joueur1.deplacer(ship, direction)
                                    selected_ship_name = None
                                    if resultat == ResultatDeplacement.DEPLACE:
                                        instruction = f"{ship.nom} deplace. Retour au mode tir."
                                        turn_mode = ActionTour.Tirer
                                        current_turn_mode[0] = turn_mode
                                    elif resultat == ResultatDeplacement.BLOQUE:
                                        instruction = "Deplacement bloque : navire deja touche."
                                    else:
                                        instruction = "Deplacement invalide."

            selected_ship = get_ship_by_name(game_ship_group, selected_ship_name) if selected_ship_name else None
            refresh_screen(
                joueur1.plateau,
                joueur2.plateau,
                game_ship_group,
                hit_list,
                current_buttons,
                instruction,
                turn_mode,
                alignement_move,
                selected_ship,
            )
            clock.tick(30)


if __name__ == "__main__":
    main()

