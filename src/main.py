from __future__ import annotations

from pathlib import Path
from enum import Enum
import itertools
import random
import sys
import threading
import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN
#
from jeu.fin_partie import Partie
from joueurs.ia import JoueurVirtuel
from joueurs.joueur import ActionTour, Joueur, JoueurHumain
from navires.bateau import Alignement, Bateau, DirectionDeplacement
from plateau.case import Case, EtatCase, ResultatTir
from plateau.plateau import Plateau, ResultatDeplacement
from reseauLocal import ReseauLocal
from jeuLocal import run_network_game

reseau = ReseauLocal()

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

SOUND_ENABLED = True
MUSIC_ENABLED = True
VOLUME_LEVEL = 0.4

WINDOW_W = 1200
WINDOW_H = 720
NB_LIGNES = 22
NB_COLONNES = 22
CELL_SIZE = 18
GRID_W = NB_COLONNES * CELL_SIZE
GRID_H = NB_LIGNES * CELL_SIZE
GRID_Y = 160
GRID_GAP = 220
PLAYER_GRID_X = (WINDOW_W - (GRID_W * 2 + GRID_GAP)) // 2
ENEMY_GRID_X = PLAYER_GRID_X + GRID_W + GRID_GAP

SHIPS = {
    "Porte-avion": [5, "Sprites/Battleship5.png"],
    "Cuirasse": [4, "Sprites/Cruiser4.png"],
    "Sous-marin": [3, "Sprites/Submarine3.png"],
    "Destroyer": [3, "Sprites/Destroyer2.png"],
    "Patrouilleur": [2, "Sprites/RescueShip3.png"],
}


def generate_random_fleet_counts() -> dict[str, int]:
    return {
        "Porte-avion": random.randint(1, 2),
        "Cuirasse": random.randint(0, 3),
        "Sous-marin": random.randint(0, 3),
        "Destroyer": random.randint(0, 3),
        "Patrouilleur": random.randint(0, 3),
    }


def fleet_total_cells(fleet_counts: dict[str, int]) -> int:
    total = 0
    for ship_type, qty in fleet_counts.items():
        total += SHIPS[ship_type][0] * qty
    return total


def generate_balanced_fleet_pair(max_delta=3, max_attempts=600) -> tuple[dict[str, int], dict[str, int]]:
    """
    Chaque joueur reçoit exactement la meme composition de flotte.
    La flotte reste aleatoire, mais le nombre de navires est strictement
    equilibre entre les deux camps.
    """
    flotte = generate_random_fleet_counts()
    return dict(flotte), dict(flotte)


def build_fleet_spec(fleet_counts: dict[str, int]) -> list[tuple[str, int, str]]:
    spec: list[tuple[str, int, str]] = []
    for ship_type, (size, rel_path) in SHIPS.items():
        qty = fleet_counts.get(ship_type, 0)
        for i in range(1, qty + 1):
            name = ship_type if qty == 1 else f"{ship_type} {i}"
            spec.append((name, size, rel_path))
    return spec


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
header_font = load_font("Fonts/ARCADECLASSIC.TTF", 22)
body_font = pygame.font.SysFont(None, 26)
small_font = pygame.font.SysFont(None, 20)
button_font = pygame.font.SysFont(None, 24)
menu_font = pygame.font.SysFont(None, 36)
label_font = pygame.font.SysFont(None, 14)





class CellHit(pygame.sprite.Sprite):
    def __init__(self, image: Path, rect_center):
        super().__init__()
        raw = pygame.image.load(image).convert_alpha()
        marker_size = max(CELL_SIZE - 2, 8)
        self.image = pygame.transform.smoothscale(raw, (marker_size, marker_size))
        self.rect = self.image.get_rect(center=rect_center)


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


# NOUVELLE CLASSE : Bouton Logo pour le Son
class AudioToggleButton:
    def __init__(self, x: int, y: int, size=40):
        # x et y représentent le coin supérieur droit
        self.rect = pygame.Rect(x - size, y, size, size)

    def draw(self, surface):
        global SOUND_ENABLED
        color = GREEN if SOUND_ENABLED else RED
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=8)

        texte = "SON" if SOUND_ENABLED else "MUT"
        label = small_font.render(texte, True, WHITE)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, pos) -> bool:
        return self.rect.collidepoint(pos)


def draw_centered_text(text, font, y, color=BLACK):
    surface = font.render(text, True, color)
    window_surface.blit(surface, surface.get_rect(center=(WINDOW_W // 2, y)))


def draw_lines():
    left = 20
    top = 12
    right = WINDOW_W - 20
    bottom = WINDOW_H - 12
    action_sep_y = WINDOW_H - 110
    pygame.draw.line(window_surface, DARK_GREY, (left, top), (right, top), 3)
    pygame.draw.line(window_surface, DARK_GREY, (right, top), (right, bottom), 3)
    pygame.draw.line(window_surface, DARK_GREY, (right, bottom), (left, bottom), 3)
    pygame.draw.line(window_surface, DARK_GREY, (left, top), (left, bottom), 3)
    pygame.draw.line(window_surface, DARK_GREY, (left, action_sep_y), (right, action_sep_y), 3)


def display_headers(turn_mode: ActionTour, alignement: Alignement, left_label="GRILLE JOUEUR", right_label="GRILLE ENNEMIE"):
    draw_centered_text("Bataille Navale", title_font, 40)
    player_text = header_font.render(left_label, True, BLACK)
    enemy_text = header_font.render(right_label, True, BLACK)
    mode_text = body_font.render(f"Mode actuel : {'TIR' if turn_mode == ActionTour.Tirer else 'DEPLACEMENT'}", True, BLACK)
    player_center_x = PLAYER_GRID_X + GRID_W // 2
    enemy_center_x = ENEMY_GRID_X + GRID_W // 2
    window_surface.blit(player_text, player_text.get_rect(center=(player_center_x, 132)))
    window_surface.blit(enemy_text, enemy_text.get_rect(center=(enemy_center_x, 132)))
    window_surface.blit(mode_text, mode_text.get_rect(center=(WINDOW_W // 2, 100)))


def display_grid_footers(player_remaining: int | None = None, enemy_remaining: int | None = None):
    return


def display_instruction(text, color=WHITE):
    panel_width = WINDOW_W - 80
    panel = pygame.Rect((WINDOW_W - panel_width) // 2, WINDOW_H - 72, panel_width, 48)
    pygame.draw.rect(window_surface, DARK_GREY, panel, border_radius=8)
    label = small_font.render(text, True, color)
    window_surface.blit(label, label.get_rect(center=panel.center))


def create_fleet_sprites(fleet_spec: list[tuple[str, int, str]] | None = None) -> pygame.sprite.Group:
    if fleet_spec is None:
        default_counts = {name: 1 for name in SHIPS}
        fleet_spec = build_fleet_spec(default_counts)

    group = pygame.sprite.Group()
    center_lane = (PLAYER_GRID_X + GRID_W + ENEMY_GRID_X) // 2
    y_start = GRID_Y + 20
    y_step = 30

    for idx, (ship_name, length, rel_path) in enumerate(fleet_spec):
        ship_x = center_lane - 40
        ship_y = y_start + idx * y_step
        group.add(Bateau(ship_name, length, asset_path(rel_path), ship_x, ship_y, cell_size=CELL_SIZE))
    return group


def create_enemy_fleet(fleet_spec: list[tuple[str, int, str]] | None = None) -> list[Bateau]:
    if fleet_spec is None:
        default_counts = {name: 1 for name in SHIPS}
        fleet_spec = build_fleet_spec(default_counts)

    lst = []
    for ship_name, length, rel_path in fleet_spec:
        lst.append(Bateau(ship_name, length, asset_path(rel_path), cell_size=CELL_SIZE))
    return lst


def get_ship_by_name(ship_group, ship_name: str) -> Bateau | None:
    for ship in ship_group:
        if ship.nom == ship_name:
            return ship
    return None


def fleet_summary_from_group(ship_group) -> str:
    order = ["Porte-avion", "Cuirasse", "Sous-marin", "Destroyer", "Patrouilleur"]
    counts = {name: 0 for name in order}

    for ship in ship_group:
        base_name = ship.nom.rsplit(" ", 1)[0] if ship.nom.rsplit(" ", 1)[-1].isdigit() else ship.nom
        if base_name in counts:
            counts[base_name] += 1

    parts = []
    for name in order:
        qty = counts[name]
        if qty > 0:
            parts.append(f"{name} x{qty}")

    return ", ".join(parts) if parts else "Aucun navire"


def count_alive_ships(plateau: Plateau) -> int:
    return sum(1 for b in plateau.bateaux if not b.estCoule())


def refresh_screen(player_plateau, enemy_plateau, ship_list, hit_list, buttons, instruction, turn_mode, alignement,
                   selected=None, left_label="GRILLE JOUEUR", right_label="GRILLE ENNEMIE", mask_enemy=False):
    window_surface.fill(GREY)
    draw_lines()
    player_plateau.draw_grid(window_surface, font=small_font)
    enemy_plateau.draw_grid(window_surface, font=small_font)
    window_surface.blit(player_plateau.surface, player_plateau.rect)
    window_surface.blit(enemy_plateau.surface, enemy_plateau.rect)
    display_headers(turn_mode, alignement, left_label, right_label)

    for btn_name, btn in buttons.items():
        active = False
        if btn_name == "action_tir" and turn_mode == ActionTour.Tirer:
            active = True
        if btn_name == "action_move" and turn_mode == ActionTour.Deplacer:
            active = True
        if btn_name in {"north", "south", "east", "west"} and turn_mode == ActionTour.Deplacer:
            active = True
        btn.draw(active)

    if "menu" in buttons:
        helper = small_font.render("Retour menu", True, BLACK)
        window_surface.blit(helper,
                            helper.get_rect(center=(buttons["menu"].rect.centerx, buttons["menu"].rect.bottom + 12)))

    ship_list.draw(window_surface)
    hit_list.draw(window_surface)
    if selected is not None:
        pygame.draw.rect(window_surface, YELLOW, selected.rect.inflate(8, 8), 4, border_radius=6)

    if mask_enemy:
        overlay = pygame.Surface((enemy_plateau.rect.w, enemy_plateau.rect.h), pygame.SRCALPHA)
        overlay.fill((15, 15, 15, 120))
        window_surface.blit(overlay, enemy_plateau.rect.topleft)

    display_grid_footers()
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
    if not SOUND_ENABLED:
        return

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

        sound.set_volume(VOLUME_LEVEL)
        sound.play()
    except Exception:
        pass


def setup_buttons():
    center_x = WINDOW_W // 2
    row_y = WINDOW_H - 145
    gap = 14

    tir_w = 100
    move_w = 170
    action_total_w = tir_w + gap + move_w
    action_start_x = center_x - action_total_w // 2

    rotate_w = 180
    lock_w = 140
    setup_total_w = rotate_w + gap + lock_w
    setup_start_x = center_x - setup_total_w // 2

    # Boutons directionnels au milieu, en vertical, en lettres seules.
    dir_w = 60
    dir_h = 42
    dir_gap = 12
    dir_x = ((PLAYER_GRID_X + GRID_W + ENEMY_GRID_X) // 2) - (dir_w // 2)
    dir_y = GRID_Y + 90

    return {
        "menu": TextButton("menu", "MENU", 22, 22, 100, 42, MENU_BLUE),
        "rotate": TextButton("rotate", "Rotation", setup_start_x, row_y, rotate_w, 46),
        "action_tir": TextButton("action_tir", "Tir", action_start_x, row_y, tir_w, 46),
        "action_move": TextButton("action_move", "Deplacement", action_start_x + tir_w + gap, row_y, move_w, 46),
        "north": TextButton("north", "N", dir_x, dir_y, dir_w, dir_h),
        "south": TextButton("south", "S", dir_x, dir_y + (dir_h + dir_gap), dir_w, dir_h),
        "east": TextButton("east", "E", dir_x, dir_y + (dir_h + dir_gap) * 2, dir_w, dir_h),
        "west": TextButton("west", "O", dir_x, dir_y + (dir_h + dir_gap) * 3, dir_w, dir_h),
        "lock": TextButton("lock", "Valider", setup_start_x + rotate_w + gap, row_y, lock_w, 46),
    }


def setup_menu_buttons():
    center_x = WINDOW_W // 2
    return {
        "create": TextButton("create", "Créer une partie", center_x - 360, 230, 320, 58),
        "join": TextButton("join", "Rejoindre une partie", center_x - 360, 305, 320, 58),
        "ia": TextButton("ia", "Jouer contre l'IA", center_x - 360, 380, 320, 58),
        "local2": TextButton("local2", "Jouer à 2 (local)", center_x - 360, 455, 320, 58),

      #  "random": TextButton("random", "IA aléatoire", 740, 255, 230, 54),
        "easy": TextButton("easy", "IA facile", center_x + 60, 305, 230, 54),
        "hard": TextButton("hard", "IA difficile", center_x + 60, 375, 230, 54),

        "start": TextButton("start", "Lancer la partie", center_x - 170, 525, 340, 62, GREEN),
    }


def run_main_menu():
    buttons = setup_menu_buttons()
    audio_logo = AudioToggleButton(WINDOW_W - 20, 20)

    # REINITIALISATION DU RESEAU EN ARRIVANT SUR LE MENU
    global reseau
    if reseau.connexion is not None:
        try:
            reseau.connexion.close()
        except:
            pass
        reseau.connexion = None

    mode = "ia"
    difficulty = "easy"
    info = "Choisissez un mode et lancez la partie."
    clock = pygame.time.Clock()
    connection_thread = None

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos

                # Gestion Audio
                if audio_logo.clicked(pos):
                    global SOUND_ENABLED, MUSIC_ENABLED
                    SOUND_ENABLED = not SOUND_ENABLED
                    MUSIC_ENABLED = SOUND_ENABLED
                    if MUSIC_ENABLED:
                        pygame.mixer.music.unpause()
                    else:
                        pygame.mixer.music.pause()

                # Choix des modes
                elif buttons["create"].clicked(pos):
                    mode = "create"
                    info = "Création de partie... En attente d'un joueur."
                    if reseau.connexion is None:
                        connection_thread = threading.Thread(target=reseau.creer_partie, kwargs={"port": 5000},
                                                             daemon=True)
                        connection_thread.start()

                elif buttons["join"].clicked(pos):
                    mode = "join"
                    info = "Recherche de la partie hôte..."
                    if reseau.connexion is None:
                        connection_thread = threading.Thread(target=reseau.rejoindre_partie, args=("127.0.0.1", 5000),
                                                             daemon=True)
                        connection_thread.start()

                elif buttons["ia"].clicked(pos):
                    mode = "ia"
                    info = "Mode contre l'IA sélectionné."
                elif buttons["local2"].clicked(pos):
                    mode = "local2"
                    info = "Mode local à 2 joueurs sélectionné."
                elif buttons["easy"].clicked(pos):
                    difficulty = "easy"
               # elif buttons["random"].clicked(pos):
                  #  difficulty = "random"
                elif buttons["hard"].clicked(pos):
                    difficulty = "hard"

                # Bouton START
                elif buttons["start"].clicked(pos):
                    if mode in ("create", "join") and reseau.connexion is None:
                        info = "Patience... La connexion réseau n'est pas encore établie."
                    else:
                        return {"mode": mode, "difficulty": difficulty}

        # --- MISE A JOUR VISUELLE DU BOUTON START ---
        if reseau.connexion is not None:
            info = "Connexion établie ! Cliquez sur Lancer."
            buttons["start"].text = "Lancer la partie"
            buttons["start"].fill = GREEN
        elif mode == "create":
            buttons["start"].text = "En attente..."
            buttons["start"].fill = GREY
        elif mode == "join":
            buttons["start"].text = "Recherche..."
            buttons["start"].fill = GREY
        else:
            buttons["start"].text = "Lancer la partie"
            buttons["start"].fill = GREEN

        # Dessin de l'interface
        window_surface.fill(GREY)
        draw_lines()
        draw_centered_text("Bataille Navale", menu_title_font, 95)
        draw_centered_text("Menu principal", body_font, 155)
        draw_centered_text("Modes", body_font, 195)

        for name, btn in buttons.items():
            active = (name == mode) or (name == difficulty)
            if name == "start": active = True
            btn.draw(active)

        audio_logo.draw(window_surface)

        info_panel = pygame.Rect((WINDOW_W - 940) // 2, WINDOW_H - 95, 940, 52)
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

    def find_anchor(ship: Bateau) -> Case | None:
        # Priorité à l'ancre géométrique attendue selon l'orientation du navire.
        anchor_probe = ship.rect.midleft if ship.alignement == Alignement.Horizontal else ship.rect.midtop
        anchor_case = player.plateau.get_cell_from_pixel(anchor_probe[0], anchor_probe[1])
        if anchor_case is not None:
            return anchor_case

        overlapping = [c for c in player.plateau.cells if ship.rect.colliderect(c.rect)]
        if not overlapping:
            return None

        # On choisit l'ancre la plus à gauche (horizontal) ou la plus haute (vertical),
        # ce qui correspond à la logique de placement utilisée par le plateau.
        if ship.alignement == Alignement.Horizontal:
            return min(overlapping, key=lambda c: (c.colonne, c.ligne))
        return min(overlapping, key=lambda c: (c.ligne, c.colonne))

    for ship in ship_group:
        anchor = find_anchor(ship)

        if anchor is None:
            return True, f"{ship.nom} n'est pas entièrement dans la grille."

        cases = player.plateau.calculer_cases_pour_bateau(ship, anchor.ligne, anchor.colonne, ship.alignement)
        if not player.plateau.placementValide(ship, cases):
            return True, "Placement invalide ou chevauchement de navires."

        player.plateau.placerBateau(ship, cases)

    total_cells = len([c for c in player.plateau.cells if c.bateau is not None])
    expected = sum(ship.taille for ship in ship_group)
    if total_cells != expected:
        return True, "Tous les navires doivent etre places correctement."

    return False, "Flotte validee. La partie commence."


def snap_ship_to_grid(plateau: Plateau, ship: Bateau, probe_pos: tuple[int, int] | None = None) -> bool:
    probe_case = None
    if probe_pos is not None:
        probe_case = plateau.get_cell_from_pixel(probe_pos[0], probe_pos[1])

    if probe_case is None:
        ref_point = ship.rect.center
        probe_case = plateau.get_cell_from_pixel(ref_point[0], ref_point[1])

    if probe_case is None:
        return False

    if ship.alignement == Alignement.Horizontal:
        ship.rect.midleft = probe_case.rect.midleft
    else:
        ship.rect.midtop = probe_case.rect.midtop
    return True


def get_ship_anchor_case(plateau: Plateau, ship: Bateau) -> Case | None:
    probe = ship.rect.midleft if ship.alignement == Alignement.Horizontal else ship.rect.midtop
    anchor = plateau.get_cell_from_pixel(probe[0], probe[1])
    if anchor is not None:
        return anchor

    overlapping = [c for c in plateau.cells if ship.rect.colliderect(c.rect)]
    if not overlapping:
        return None

    if ship.alignement == Alignement.Horizontal:
        return min(overlapping, key=lambda c: (c.colonne, c.ligne))
    return min(overlapping, key=lambda c: (c.ligne, c.colonne))


def detect_ship_drop_issue(plateau: Plateau, ship: Bateau, ship_group=None):
    anchor = get_ship_anchor_case(plateau, ship)
    if anchor is None:
        return "Ce navire doit etre place entierement dans la grille."

    cases = plateau.calculer_cases_pour_bateau(ship, anchor.ligne, anchor.colonne, ship.alignement)
    if cases is None:
        return "Placement invalide : navire hors grille."

    current_positions = {(case.ligne, case.colonne) for case in cases}

    # Verification immediate contre les autres sprites deja poses,
    # sans attendre la validation finale.
    if ship_group is not None:
        other_positions = set()
        for other_ship in ship_group:
            if other_ship == ship:
                continue
            other_anchor = get_ship_anchor_case(plateau, other_ship)
            if other_anchor is None:
                continue
            other_cases = plateau.calculer_cases_pour_bateau(
                other_ship,
                other_anchor.ligne,
                other_anchor.colonne,
                other_ship.alignement,
            )
            if other_cases is None:
                continue
            for other_case in other_cases:
                other_positions.add((other_case.ligne, other_case.colonne))

        if current_positions & other_positions:
            return "Superposition interdite : ce navire est deja occupe par un autre."

        for ligne, colonne in current_positions:
            for dr in range(-1, 2):
                for dc in range(-1, 2):
                    if (ligne + dr, colonne + dc) in other_positions:
                        return "Placement invalide : laissez une case d'espace entre les navires."

    for case in cases:
        if case.bateau is not None and case.bateau != ship:
            return "Superposition interdite : un navire ne peut pas etre pose sur un autre."

    if not plateau.respecte_voisinage(cases, ship):
        return "Placement invalide : laissez une case d'espace entre les navires."

    return None


def direction_from_button(button_name: str) -> DirectionDeplacement | None:
    mapping = {
        "north": DirectionDeplacement.NORD,
        "south": DirectionDeplacement.SUD,
        "east": DirectionDeplacement.EST,
        "west": DirectionDeplacement.OUEST,
    }
    return mapping.get(button_name)


def set_up_player_ships(
    player: JoueurHumain,
    enemy: Joueur,
    ship_group,
    hit_list,
    left_label="GRILLE JOUEUR",
    right_label="GRILLE ENNEMIE",
):
    buttons = setup_buttons()
    selected = None
    dragging = False
    offset_x = 0
    offset_y = 0
    previous_rect = None
    previous_alignement = None
    fleet_summary = fleet_summary_from_group(ship_group)
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
                    old_rect = selected.rect.copy()
                    old_align = selected.alignement
                    new_align = Alignement.Vertical if selected.alignement == Alignement.Horizontal else Alignement.Horizontal
                    selected.orienter(new_align)
                    snap_ship_to_grid(player.plateau, selected)
                    issue = detect_ship_drop_issue(player.plateau, selected, ship_group)
                    if issue is not None:
                        selected.orienter(old_align)
                        selected.rect = old_rect
                        instruction = issue
                    else:
                        instruction = f"{selected.nom} tourne en {selected.alignement.value}."
                    continue
                if buttons["lock"].clicked(pos):
                    still_setup, instruction = lock_in_ships(player, ship_group)
                    if not still_setup:
                        return True
                for ship in reversed(ship_group.sprites()):
                    if ship.rect.collidepoint(pos):
                        selected = ship
                        dragging = True
                        previous_rect = ship.rect.copy()
                        previous_alignement = ship.alignement
                        offset_x = ship.rect.x - pos[0]
                        offset_y = ship.rect.y - pos[1]
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                if dragging and selected is not None:
                    snapped = snap_ship_to_grid(player.plateau, selected, event.pos)
                    issue = None if snapped else "Ce navire doit etre place dans la grille."
                    if issue is None:
                        issue = detect_ship_drop_issue(player.plateau, selected, ship_group)
                    if issue is not None:
                        if previous_alignement is not None:
                            selected.orienter(previous_alignement)
                        if previous_rect is not None:
                            selected.rect = previous_rect
                        instruction = issue
                    else:
                        instruction = f"{selected.nom} place correctement."
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging and selected is not None:
                selected.rect.x = event.pos[0] + offset_x
                selected.rect.y = event.pos[1] + offset_y
                live_issue = detect_ship_drop_issue(player.plateau, selected, ship_group)
                if live_issue is not None:
                    instruction = live_issue
                else:
                    instruction = f"{selected.nom} peut etre place ici."

        setup_instruction = f"Flotte: {fleet_summary} | {instruction}"

        refresh_screen(
            player.plateau,
            enemy.plateau,
            ship_group,
            hit_list,
            {k: v for k, v in buttons.items() if k in ["menu", "rotate", "lock"]},
            setup_instruction,
            ActionTour.Tirer,
            Alignement.Horizontal,
            selected,
            left_label=left_label,
            right_label=right_label,
        )
        clock.tick(30)


def show_turn_transition(player_name: str):
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                waiting = False

        window_surface.fill(DARK_GREY)
        draw_centered_text("Passez l'ordinateur", menu_title_font, 230, WHITE)
        draw_centered_text(f"C'est au tour de {player_name}", body_font, 305, WHITE)
        draw_centered_text("Cliquez pour commencer le tour", small_font, 350, WHITE)
        pygame.display.update()


def apply_hit_local(attacker: JoueurHumain, defender: JoueurHumain, cible: Case, hit_list) -> tuple[str, bool, bool, ResultatTir | None]:
    resultat = attacker.tirer(defender, cible)
    center = cible.rect.center

    if resultat == ResultatTir.DEJA_TIRE:
        return "Cette case a deja ete visee.", False, False, None

    if resultat in (ResultatTir.TOUCHE, ResultatTir.COULE):
        hit_list.add(CellHit(asset_path("Sprites/hit.png"), center))
        play_sound("sink" if resultat == ResultatTir.COULE else "hit")
        if defender.plateau.tousLesBateauxCoules():
            return f"Tous les navires de {defender.nom} sont coules.", True, True, resultat
        return ("Touche !" if resultat == ResultatTir.TOUCHE else "Coule !"), True, False, resultat

    hit_list.add(CellHit(asset_path("Sprites/miss.png"), center))
    play_sound("miss")
    return "Rate.", True, False, resultat


def run_local_two_players():
    fleet_counts_1, fleet_counts_2 = generate_balanced_fleet_pair()
    fleet_spec_1 = build_fleet_spec(fleet_counts_1)
    fleet_spec_2 = build_fleet_spec(fleet_counts_2)

    player1_plateau = Plateau(PLAYER_GRID_X, GRID_Y)
    player2_plateau = Plateau(ENEMY_GRID_X, GRID_Y)

    joueur1 = JoueurHumain("Joueur 1", player1_plateau)
    joueur2 = JoueurHumain("Joueur 2", player2_plateau)

    partie = Partie(joueur1, joueur2)
    partie.demarrer()

    hit_list = pygame.sprite.Group()

    show_turn_transition(joueur1.nom)
    ship_group_1 = create_fleet_sprites(fleet_spec_1)
    if not set_up_player_ships(joueur1, joueur2, ship_group_1, hit_list, left_label="JOUEUR 1", right_label="JOUEUR 2"):
        return
    joueur1.plateau.bateaux = list(ship_group_1)

    show_turn_transition(joueur2.nom)
    ship_group_2 = create_fleet_sprites(fleet_spec_2)
    if not set_up_player_ships(joueur2, joueur1, ship_group_2, hit_list, left_label="JOUEUR 1", right_label="JOUEUR 2"):
        return
    joueur2.plateau.bateaux = list(ship_group_2)

    # Confidentialité: après validation de Joueur 2, on masque avant de rendre la main à Joueur 1.
    show_turn_transition(joueur1.nom)

    # Les bonus de tours dépendent de la flotte effectivement placée.
    partie.demarrerTour()

    ship_groups = {
        joueur1: pygame.sprite.Group(joueur1.plateau.bateaux),
        joueur2: pygame.sprite.Group(joueur2.plateau.bateaux),
    }

    buttons = setup_buttons()
    global current_buttons
    current_buttons = {k: v for k, v in buttons.items() if k in ["menu", "action_tir", "action_move", "north", "south", "east", "west"]}

    current_player = joueur1
    enemy_player = joueur2

    turn_mode = ActionTour.Tirer
    alignement_move = Alignement.Horizontal
    current_turn_mode[0] = turn_mode
    current_alignement[0] = alignement_move

    selected_ship_name = None
    move_used_this_turn = False
    instruction = f"Tour de {current_player.nom} : tirez ou deplacez un navire."
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos

                if current_buttons["menu"].clicked(pos):
                    return

                elif "rotate" in current_buttons and current_buttons["rotate"].clicked(pos):
                    if turn_mode == ActionTour.Deplacer and selected_ship_name:
                        ship = get_ship_by_name(ship_groups[current_player], selected_ship_name)
                        if ship:
                            new_align = Alignement.Vertical if ship.alignement == Alignement.Horizontal else Alignement.Horizontal
                            ship.orienter(new_align)
                            anchor_case = ship.getCasesOccupees()[0] if ship.getCasesOccupees() else None
                            if anchor_case:
                                cases = current_player.plateau.calculer_cases_pour_bateau(
                                    ship, anchor_case.ligne, anchor_case.colonne, new_align
                                )
                                if cases and current_player.plateau.placementValide(ship, cases):
                                    current_player.plateau.placerBateau(ship, cases)
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
                    if move_used_this_turn:
                        turn_mode = ActionTour.Tirer
                        current_turn_mode[0] = turn_mode
                        selected_ship_name = None
                        instruction = "Deplacement deja utilise pour ce tour. Il vous reste seulement des tirs."
                    else:
                        turn_mode = ActionTour.Deplacer
                        current_turn_mode[0] = turn_mode
                        instruction = "Mode deplacement actif : choisissez un navire puis cliquez sur N, S, E ou O."

                elif turn_mode == ActionTour.Tirer and enemy_player.plateau.rect.collidepoint(pos):
                    cell = enemy_player.plateau.get_cell_from_pixel(*pos)
                    if cell is not None:
                        instruction, consumed_action, finished, tir_result = apply_hit_local(
                            current_player, enemy_player, cell, hit_list
                        )

                        if finished:
                            refresh_screen(
                                current_player.plateau,
                                enemy_player.plateau,
                                ship_groups[current_player],
                                hit_list,
                                current_buttons,
                                instruction,
                                turn_mode,
                                alignement_move,
                                left_label="JOUEUR 1",
                                right_label="JOUEUR 2",
                                mask_enemy=True,
                            )
                            pygame.time.wait(1200)
                            partie.determinerVainqueur()
                            winner_name = partie.Vainqueur.nom if partie.Vainqueur else current_player.nom
                            show_game_over(f"Vainqueur : {winner_name}")
                            return

                        if consumed_action:
                            same_player = partie.jouerTour(tir_result)
                            if same_player:
                                instruction = f"{instruction} Tours restants: {partie.ToursResatants}."
                            else:
                                current_player = partie.joueurCourant
                                enemy_player = joueur2 if current_player == joueur1 else joueur1
                                selected_ship_name = None
                                turn_mode = ActionTour.Tirer
                                current_turn_mode[0] = turn_mode
                                alignement_move = Alignement.Horizontal
                                current_alignement[0] = alignement_move
                                move_used_this_turn = False
                                show_turn_transition(current_player.nom)
                                instruction = f"Tour de {current_player.nom}. Tours: {partie.ToursResatants}."

                elif turn_mode == ActionTour.Deplacer and current_player.plateau.rect.collidepoint(pos):
                    cell = current_player.plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Case invalide."
                    elif cell.bateau is None:
                        instruction = "Choisissez d'abord un de vos navires."
                    else:
                        selected_ship_name = cell.bateau.nom
                        instruction = f"{selected_ship_name} selectionne. Cliquez sur N, S, E ou O."

                elif turn_mode == ActionTour.Deplacer:
                    direction = None
                    for button_name in ("north", "south", "east", "west"):
                        if current_buttons[button_name].clicked(pos):
                            direction = direction_from_button(button_name)
                            break
                    if direction is not None:
                        if selected_ship_name is None:
                            instruction = "Selectionnez d'abord un navire a deplacer."
                        else:
                            ship = get_ship_by_name(ship_groups[current_player], selected_ship_name)
                            if ship is None:
                                selected_ship_name = None
                                instruction = "Navire introuvable."
                            else:
                                resultat = current_player.deplacer(ship, direction)
                                selected_ship_name = None
                                turn_mode = ActionTour.Tirer
                                current_turn_mode[0] = turn_mode
                                if resultat == ResultatDeplacement.DEPLACE:
                                    move_used_this_turn = True
                                    same_player = partie.jouerTour(None)
                                    alignement_move = Alignement.Horizontal
                                    current_alignement[0] = alignement_move
                                    if same_player:
                                        instruction = f"{ship.nom} deplace d'une case. Vous pouvez encore tirer. Tours restants: {partie.ToursResatants}."
                                    else:
                                        current_player = partie.joueurCourant
                                        enemy_player = joueur2 if current_player == joueur1 else joueur1
                                        move_used_this_turn = False
                                        show_turn_transition(current_player.nom)
                                        instruction = f"Tour de {current_player.nom}. Tours: {partie.ToursResatants}."
                                elif resultat == ResultatDeplacement.BLOQUE:
                                    instruction = "Deplacement bloque : navire deja touche."
                                else:
                                    instruction = "Deplacement invalide : collision, superposition ou sortie de grille."

        selected_ship = get_ship_by_name(ship_groups[current_player], selected_ship_name) if selected_ship_name else None
        refresh_screen(
            current_player.plateau,
            enemy_player.plateau,
            ship_groups[current_player],
            hit_list,
            current_buttons,
            instruction,
            turn_mode,
            alignement_move,
            selected_ship,
            left_label="JOUEUR 1",
            right_label="JOUEUR 2",
            mask_enemy=True,
        )
        clock.tick(30)


def apply_hit_to_enemy(player: JoueurHumain, enemy: JoueurVirtuel, cible: Case, hit_list, ship_group) -> tuple[
    str, bool, bool, ResultatTir | None]:
    resultat = player.tirer(enemy, cible)
    center = cible.rect.center

    if resultat == ResultatTir.DEJA_TIRE:
        return "Cette case a deja ete visee.", False, False, None

    if resultat in (ResultatTir.TOUCHE, ResultatTir.COULE):
        hit_list.add(CellHit(asset_path("Sprites/hit.png"), center))
        play_sound("sink" if resultat == ResultatTir.COULE else "hit")
        if enemy.plateau.tousLesBateauxCoules():
            return "Tous les navires ennemis sont coules. Victoire !", True, True, resultat
        return ("Touche !" if resultat == ResultatTir.TOUCHE else "Coule !"), True, False, resultat

    hit_list.add(CellHit(asset_path("Sprites/miss.png"), center))
    play_sound("miss")
    return "Rate.", True, False, resultat


def enemy_take_turn(partie: Partie, enemy: JoueurVirtuel, player: JoueurHumain, hit_list) -> tuple[str, bool]:
    instruction = ""
    while partie.joueurCourant == enemy:
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

        else:
            hit_list.add(CellHit(asset_path("Sprites/miss.png"), center))
            play_sound("miss")
            if enemy.derniereCaseTouchee and enemy.second_hit:
                if not enemy.tested_no_hit:
                    enemy.tested_no_hit = (cible.ligne, cible.colonne)
                else:
                    enemy.tested_no_hit_2 = (cible.ligne, cible.colonne)

        same_player = partie.jouerTour(resultat)
        if same_player:
            instruction = f"L'ennemi continue. Tours restants IA: {partie.ToursResatants}."
        else:
            instruction = f"L'ennemi termine. A vous de jouer ({partie.ToursResatants} tours)."

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
    color = RED if ("Victoire" in text or "Vainqueur" in text or "gagne" in text) else BLACK
    draw_centered_text("FIN DE PARTIE", menu_title_font, 200, color)
    draw_centered_text(text, body_font, 275, color)
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

        if menu_choice["mode"] in ("create", "join"):
            run_network_game(reseau, menu_choice["mode"], menu_choice["difficulty"])
            continue

        if menu_choice["mode"] == "local2":
            run_local_two_players()
            continue

        player_plateau = Plateau(PLAYER_GRID_X, GRID_Y)
        enemy_plateau = Plateau(ENEMY_GRID_X, GRID_Y)

        joueur1 = JoueurHumain("Joueur", player_plateau)
        joueur2 = JoueurVirtuel("IA", enemy_plateau, difficulty=menu_choice["difficulty"])

        fleet_counts_player, fleet_counts_enemy = generate_balanced_fleet_pair()
        fleet_spec_player = build_fleet_spec(fleet_counts_player)
        fleet_spec_enemy = build_fleet_spec(fleet_counts_enemy)

        partie = Partie(joueur1, joueur2)
        partie.demarrer()

        ship_group = create_fleet_sprites(fleet_spec_player)
        enemy_ships = create_enemy_fleet(fleet_spec_enemy)
        joueur2.plateau.bateaux = enemy_ships
        try:
            joueur2.randomise_ships()
        except RuntimeError:
            # Cas rare de saturation d'essais: on relance la configuration de partie.
            continue

        hit_list = pygame.sprite.Group()

        if not set_up_player_ships(joueur1, joueur2, ship_group, hit_list):
            continue

        joueur1.plateau.bateaux = list(ship_group)
        partie.demarrerTour()
        game_ship_group = pygame.sprite.Group(joueur1.plateau.bateaux)

        buttons = setup_buttons()
        global current_buttons
        current_buttons = {k: v for k, v in buttons.items() if
               k in ["menu", "action_tir", "action_move", "north", "south", "east", "west"]}

        turn_mode = ActionTour.Tirer
        alignement_move = Alignement.Horizontal
        current_turn_mode[0] = turn_mode
        current_alignement[0] = alignement_move

        selected_ship_name = None
        move_used_this_turn = False
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

                    elif "rotate" in current_buttons and current_buttons["rotate"].clicked(pos):
                        if turn_mode == ActionTour.Deplacer and selected_ship_name:
                            ship = get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship:
                                new_align = Alignement.Vertical if ship.alignement == Alignement.Horizontal else Alignement.Horizontal
                                ship.orienter(new_align)
                                anchor_case = ship.getCasesOccupees()[0] if ship.getCasesOccupees() else None
                                if anchor_case:
                                    cases = joueur1.plateau.calculer_cases_pour_bateau(ship, anchor_case.ligne,
                                                                                       anchor_case.colonne, new_align)
                                    if cases and joueur1.plateau.placementValide(ship, cases):
                                        joueur1.plateau.placerBateau(ship, cases)
                                        instruction = f"{ship.nom} pivote en {new_align.value}."
                                    else:
                                        ship.orienter(
                                            Alignement.Horizontal if new_align == Alignement.Vertical else Alignement.Vertical)
                                        instruction = "Rotation impossible ici."

                    elif current_buttons["action_tir"].clicked(pos):
                        turn_mode = ActionTour.Tirer
                        current_turn_mode[0] = turn_mode
                        selected_ship_name = None
                        instruction = "Mode tir actif. Cliquez sur la grille ennemie."

                    elif current_buttons["action_move"].clicked(pos):
                        if move_used_this_turn:
                            turn_mode = ActionTour.Tirer
                            current_turn_mode[0] = turn_mode
                            selected_ship_name = None
                            instruction = "Deplacement deja utilise pour ce tour. Il vous reste seulement des tirs."
                        else:
                            turn_mode = ActionTour.Deplacer
                            current_turn_mode[0] = turn_mode
                            instruction = "Mode deplacement actif : choisissez un navire puis cliquez sur N, S, E ou O."

                    elif turn_mode == ActionTour.Tirer and enemy_plateau.rect.collidepoint(pos):
                        cell = enemy_plateau.get_cell_from_pixel(*pos)
                        if cell is not None:
                            instruction, consumed_action, finished, tir_result = apply_hit_to_enemy(
                                joueur1, joueur2, cell, hit_list, game_ship_group
                            )
                            if finished:
                                refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                               current_buttons, instruction, turn_mode, alignement_move)
                                pygame.time.wait(1200)
                                partie.determinerVainqueur()
                                winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur1.nom
                                show_game_over(f"Vainqueur : {winner_name}")
                                playing = False
                                break

                            if consumed_action:
                                defeat = False
                                same_player = partie.jouerTour(tir_result)
                                if same_player:
                                    instruction = f"{instruction} Tours restants: {partie.ToursResatants}."
                                else:
                                    move_used_this_turn = False
                                    instruction, defeat = enemy_take_turn(partie, joueur2, joueur1, hit_list)
                                if defeat:
                                    refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                                   current_buttons, instruction, turn_mode, alignement_move)
                                    pygame.time.wait(1200)
                                    partie.determinerVainqueur()
                                    winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur2.nom
                                    show_game_over(f"Vainqueur : {winner_name}")
                                    playing = False
                                    break

                    elif turn_mode == ActionTour.Deplacer and player_plateau.rect.collidepoint(pos):
                        cell = player_plateau.get_cell_from_pixel(*pos)
                        if cell is None:
                            instruction = "Case invalide."
                        elif cell.bateau is None:
                            instruction = "Choisissez d'abord un de vos navires."
                        else:
                            selected_ship_name = cell.bateau.nom
                            instruction = f"{selected_ship_name} selectionne. Cliquez sur N, S, E ou O."

                    elif turn_mode == ActionTour.Deplacer:
                        direction = None
                        for button_name in ("north", "south", "east", "west"):
                            if current_buttons[button_name].clicked(pos):
                                direction = direction_from_button(button_name)
                                break
                        if direction is not None:
                            if selected_ship_name is None:
                                instruction = "Selectionnez d'abord un navire a deplacer."
                            else:
                                ship = get_ship_by_name(game_ship_group, selected_ship_name)
                                if ship is None:
                                    selected_ship_name = None
                                    instruction = "Navire introuvable."
                                else:
                                    resultat = joueur1.deplacer(ship, direction)
                                    selected_ship_name = None
                                    turn_mode = ActionTour.Tirer
                                    current_turn_mode[0] = turn_mode
                                    if resultat == ResultatDeplacement.DEPLACE:
                                        move_used_this_turn = True
                                        same_player = partie.jouerTour(None)
                                        if same_player:
                                            instruction = f"{ship.nom} deplace d'une case. Vous pouvez encore tirer. Tours restants: {partie.ToursResatants}."
                                        else:
                                            move_used_this_turn = False
                                            instruction, defeat = enemy_take_turn(partie, joueur2, joueur1, hit_list)
                                        if defeat:
                                            refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                                           current_buttons, instruction, turn_mode, alignement_move)
                                            pygame.time.wait(1200)
                                            partie.determinerVainqueur()
                                            winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur2.nom
                                            show_game_over(f"Vainqueur : {winner_name}")
                                            playing = False
                                            break
                                    elif resultat == ResultatDeplacement.BLOQUE:
                                        instruction = "Deplacement bloque : navire deja touche."
                                    else:
                                        instruction = "Deplacement invalide : collision, superposition ou sortie de grille."

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