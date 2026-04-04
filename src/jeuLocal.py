import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN

from reseauLocal import ReseauLocal


def parse_response_result(result: str):
    import main as main_module
    ResultatTir = main_module.ResultatTir
    if result == "TOUCHE":
        return ResultatTir.TOUCHE
    if result == "RATE":
        return ResultatTir.RATE
    if result == "COULE":
        return ResultatTir.COULE
    if result == "DEJA":
        return ResultatTir.DEJA_TIRE
    return ResultatTir.INVALIDE


def format_result_string(result):
    import main as main_module
    ResultatTir = main_module.ResultatTir
    if result == ResultatTir.TOUCHE:
        return "TOUCHE"
    if result == ResultatTir.RATE:
        return "RATE"
    if result == ResultatTir.COULE:
        return "COULE"
    if result == ResultatTir.DEJA_TIRE:
        return "DEJA"
    return "INVALIDE"


def run_network_game(reseau: ReseauLocal, mode: str, difficulty: str):
    # Import ici pour éviter les imports circulaires pendant l'initialisation
    import main as main_module

    Plateau = main_module.Plateau
    JoueurHumain = main_module.JoueurHumain
    create_fleet_sprites = main_module.create_fleet_sprites
    set_up_player_ships = main_module.set_up_player_ships
    show_game_over = main_module.show_game_over
    get_ship_by_name = main_module.get_ship_by_name
    CellHit = main_module.CellHit
    asset_path = main_module.asset_path
    draw_centered_text = main_module.draw_centered_text
    ActionTour = main_module.ActionTour
    Alignement = main_module.Alignement
    ResultatTir = main_module.ResultatTir
    ResultatDeplacement = main_module.ResultatDeplacement
    EtatCase = main_module.EtatCase
    setup_buttons = main_module.setup_buttons
    player_plateau = Plateau(main_module.PLAYER_GRID_X, main_module.GRID_Y)
    enemy_plateau = Plateau(main_module.ENEMY_GRID_X, main_module.GRID_Y)

    joueur1 = JoueurHumain("Joueur", player_plateau)
    partie = main_module.Partie(joueur1, JoueurHumain("Adversaire", enemy_plateau))
    partie.demarrer()

    ship_group = create_fleet_sprites()
    hit_list = pygame.sprite.Group()

    instruction = "Placez vos navires puis cliquez Valider."
    adversary = JoueurHumain("Adversaire", enemy_plateau)
    if not set_up_player_ships(joueur1, adversary, ship_group, hit_list):
        return

    joueur1.plateau.bateaux = list(ship_group)
    game_ship_group = pygame.sprite.Group(joueur1.plateau.bateaux)

    reseau.envoyer("READY")
    start_time = pygame.time.get_ticks()
    ready = False
    while not ready:
        msg = reseau.recevoir()
        if msg.strip() == "READY":
            ready = True
            break
        if pygame.time.get_ticks() - start_time > 15000:
            show_game_over("Connexion perdue. Retour au menu.")
            return
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); main_module.sys.exit()
        main_module.window_surface.fill(main_module.GREY)
        draw_centered_text("En attente de l'adversaire...", main_module.body_font, main_module.WINDOW_H // 2)
        pygame.display.update()
        pygame.time.wait(100)

    my_turn = mode == "create"
    instruction = "Votre tour." if my_turn else "Tour de l'adversaire."
    clock = pygame.time.Clock()
    net_buttons = setup_buttons()
    net_buttons = {k: v for k, v in net_buttons.items() if k in ["menu", "action_tir", "action_move", "north", "south", "east", "west"]}
    turn_mode = ActionTour.Tirer

    selected_ship_name = None
    deplacement_alignement = Alignement.Horizontal
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit(); main_module.sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos
                if net_buttons["menu"].clicked(pos):
                    return
                if my_turn and turn_mode == ActionTour.Tirer and enemy_plateau.rect.collidepoint(pos):
                    cell = enemy_plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Cliquez sur la grille ennemie."
                    elif cell.is_clicked:
                        instruction = "Case deja ciblee."
                    else:
                        reseau.envoyer(f"TIR {cell.ligne} {cell.colonne}")
                        instruction = "Tir envoye, attente resultat."
                        my_turn = False
                elif net_buttons["action_tir"].clicked(pos):
                    turn_mode = ActionTour.Tirer
                    instruction = "Mode tir."
                    selected_ship_name = None
                elif net_buttons["action_move"].clicked(pos):
                    turn_mode = ActionTour.Deplacer
                    instruction = "Mode deplacement en reseau : choisissez un navire puis cliquez sur N, S, E ou O."
                elif turn_mode == ActionTour.Deplacer and player_plateau.rect.collidepoint(pos):
                    cell = player_plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Case invalide."
                    elif cell.bateau is None:
                        instruction = "Choisissez d'abord un navire sur votre grille."
                    else:
                        selected_ship_name = cell.bateau.nom
                        instruction = f"{selected_ship_name} selectionne. Cliquez sur N, S, E ou O."
                elif turn_mode == ActionTour.Deplacer:
                    direction = None
                    for button_name in ("north", "south", "east", "west"):
                        if net_buttons[button_name].clicked(pos):
                            direction = main_module.direction_from_button(button_name)
                            break
                    if direction is not None:
                        if selected_ship_name is None:
                            instruction = "Selectionnez d'abord un navire a deplacer."
                        else:
                            ship = main_module.get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship is None:
                                selected_ship_name = None
                                instruction = "Navire introuvable."
                            else:
                                resultat = joueur1.deplacer(ship, direction)
                                selected_ship_name = None
                                turn_mode = ActionTour.Tirer
                                if resultat == ResultatDeplacement.DEPLACE:
                                    instruction = f"{ship.nom} deplace d'une case. Tour adverse."
                                    my_turn = False
                                elif resultat == ResultatDeplacement.BLOQUE:
                                    instruction = "Deplacement bloque : navire deja touche."
                                else:
                                    instruction = "Deplacement invalide : collision, superposition ou sortie de grille."

        incoming = reseau.recevoir()
        if incoming:
            for line in incoming.strip().splitlines():
                if not line:
                    continue
                parts = line.strip().split()
                if parts[0] == "TIR" and len(parts) == 3:
                    r, c = int(parts[1]), int(parts[2])
                    cible = joueur1.plateau.getCase(r, c)
                    if cible is None:
                        reseau.envoyer(f"RESULT INVALIDE {r} {c}")
                    else:
                        resultat = joueur1.plateau.tirer(cible)
                        if resultat in (ResultatTir.TOUCHE, ResultatTir.COULE):
                            hit_list.add(CellHit(asset_path("Sprites/hit.png"), cible.rect.center))
                        else:
                            hit_list.add(CellHit(asset_path("Sprites/miss.png"), cible.rect.center))
                        reseau.envoyer(f"RESULT {format_result_string(resultat)} {r} {c}")
                        if joueur1.plateau.tousLesBateauxCoules():
                            reseau.envoyer("GAME_OVER WIN")
                            show_game_over("Defaite !")
                            return
                        my_turn = True
                        instruction = "L'adversaire a joue. Votre tour."
                elif parts[0] == "RESULT" and len(parts) == 4:
                    status = parse_response_result(parts[1])
                    r, c = int(parts[2]), int(parts[3])
                    target = enemy_plateau.getCase(r, c)
                    if target:
                        target.is_clicked = True
                        if status in (ResultatTir.TOUCHE, ResultatTir.COULE):
                            target.etat = EtatCase.TOUCHEE
                            hit_list.add(CellHit(asset_path("Sprites/hit.png"), target.rect.center))
                        else:
                            target.etat = EtatCase.RATEE
                            hit_list.add(CellHit(asset_path("Sprites/miss.png"), target.rect.center))
                    my_turn = False
                    if status == ResultatTir.RATE:
                        instruction = "Rate. Tour adverse."
                    elif status == ResultatTir.TOUCHE:
                        instruction = "Touche ! Tour adverse."
                    elif status == ResultatTir.COULE:
                        instruction = "Coule ! Tour adverse."
                    else:
                        instruction = "Resultat invalide."
                elif parts[0] == "GAME_OVER" and len(parts) > 1:
                    if parts[1] == "WIN":
                        show_game_over("Victoire !")
                    else:
                        show_game_over("Defaite !")
                    return

        main_module.refresh_screen(
            joueur1.plateau,
            enemy_plateau,
            game_ship_group,
            hit_list,
            net_buttons,
            instruction,
            turn_mode,
            deplacement_alignement,
            main_module.get_ship_by_name(game_ship_group, selected_ship_name) if selected_ship_name else None,
        )
        clock.tick(30)
