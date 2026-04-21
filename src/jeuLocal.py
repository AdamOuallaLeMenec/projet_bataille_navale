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


def serialize_fleet(fleet_counts: dict) -> str:
    """Sérialise les comptages de flotte pour envoi réseau."""
    return ",".join(f"{name}:{count}" for name, count in fleet_counts.items())


def deserialize_fleet(data: str) -> dict:
    """Désérialise les comptages de flotte reçus du réseau."""
    result = {}
    for part in data.split(","):
        if ":" in part:
            name, count = part.rsplit(":", 1)
            result[name] = int(count)
    return result


def run_network_game(reseau: ReseauLocal, mode: str, difficulty: str):
    # Import ici pour éviter les imports circulaires pendant l'initialisation
    import main as main_module

    Plateau = main_module.Plateau
    JoueurHumain = main_module.JoueurHumain
    create_fleet_sprites = main_module.create_fleet_sprites
    build_fleet_spec = main_module.build_fleet_spec
    generate_balanced_fleet_pair = main_module.generate_balanced_fleet_pair
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
    safe_move_ship = main_module.safe_move_ship
    direction_from_button = main_module.direction_from_button
    Partie = main_module.Partie

    player_plateau = Plateau(main_module.PLAYER_GRID_X, main_module.GRID_Y)
    enemy_plateau = Plateau(main_module.ENEMY_GRID_X, main_module.GRID_Y)

    joueur1 = JoueurHumain("Joueur", player_plateau)
    joueur_ennemi = JoueurHumain("Adversaire", enemy_plateau)
    partie = Partie(joueur1, joueur_ennemi)
    partie.demarrer()

    # --- SYNCHRONISATION DES FLOTTES ---
    # L'hôte génère la spec de flotte et l'envoie au client avant le placement.
    if mode == "create":
        fleet_counts, _ = generate_balanced_fleet_pair()
        reseau.envoyer(f"FLEET {serialize_fleet(fleet_counts)}")
        fleet_spec = build_fleet_spec(fleet_counts)
    else:
        fleet_spec = None
        start_time = pygame.time.get_ticks()
        while fleet_spec is None:
            msg = reseau.recevoir()
            if msg is None:
                show_game_over("Adversaire déconnecté. Retour au menu.")
                return
            if msg:
                for line in msg.strip().splitlines():
                    parts = line.strip().split(" ", 1)
                    if parts[0] == "FLEET" and len(parts) == 2:
                        fleet_counts = deserialize_fleet(parts[1])
                        fleet_spec = build_fleet_spec(fleet_counts)
                        break
            if pygame.time.get_ticks() - start_time > 60000:
                show_game_over("Connexion perdue. Retour au menu.")
                return
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    main_module.sys.exit()
            main_module.window_surface.fill(main_module.GREY)
            draw_centered_text("Synchronisation des flottes...", main_module.body_font, main_module.WINDOW_H // 2)
            pygame.display.update()
            pygame.time.wait(100)

    # --- PLACEMENT DES NAVIRES ---
    ship_group = create_fleet_sprites(fleet_spec)
    hit_list = pygame.sprite.Group()

    if not set_up_player_ships(joueur1, joueur_ennemi, ship_group, hit_list):
        return

    joueur1.plateau.bateaux = list(ship_group)
    game_ship_group = pygame.sprite.Group(joueur1.plateau.bateaux)
    partie.demarrerTour()

    # --- SYNCHRONISATION READY ---
    reseau.envoyer("READY")
    start_time = pygame.time.get_ticks()
    ready = False
    while not ready:
        msg = reseau.recevoir()
        if msg is None:
            show_game_over("Adversaire déconnecté. Retour au menu.")
            return
        if msg and "READY" in msg:
            ready = True
            break
        if pygame.time.get_ticks() - start_time > 120000:
            show_game_over("Connexion perdue. Retour au menu.")
            return
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                main_module.sys.exit()
        main_module.window_surface.fill(main_module.GREY)
        draw_centered_text("En attente de l'adversaire...", main_module.body_font, main_module.WINDOW_H // 2)
        pygame.display.update()
        pygame.time.wait(100)

    my_turn = mode == "create"
    instruction = f"Votre tour ! Tours : {partie.ToursRestants}." if my_turn else "Tour de l'adversaire."
    clock = pygame.time.Clock()
    net_buttons = setup_buttons()
    net_buttons = {k: v for k, v in net_buttons.items() if k in ["menu", "action_tir", "action_move", "north", "south", "east", "west"]}
    turn_mode = ActionTour.Tirer
    selected_ship_name = None
    move_used_this_turn = False

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                main_module.sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos

                if net_buttons["menu"].clicked(pos):
                    return

                elif net_buttons["action_tir"].clicked(pos):
                    turn_mode = ActionTour.Tirer
                    selected_ship_name = None
                    instruction = "Mode tir actif."

                elif net_buttons["action_move"].clicked(pos):
                    if not my_turn:
                        instruction = "Ce n'est pas votre tour."
                    elif move_used_this_turn:
                        instruction = "Deplacement deja utilise ce tour."
                    else:
                        turn_mode = ActionTour.Deplacer
                        instruction = "Mode deplacement : choisissez un navire puis N, S, E ou O."

                elif my_turn and turn_mode == ActionTour.Tirer and enemy_plateau.rect.collidepoint(pos):
                    cell = enemy_plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Cliquez sur la grille ennemie."
                    elif cell.is_clicked:
                        instruction = "Case deja ciblee."
                    else:
                        reseau.envoyer(f"TIR {cell.ligne} {cell.colonne}")
                        instruction = "Tir envoye, attente du resultat..."

                elif my_turn and turn_mode == ActionTour.Deplacer and player_plateau.rect.collidepoint(pos):
                    cell = player_plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Case invalide."
                    elif cell.bateau is None:
                        instruction = "Choisissez d'abord un de vos navires."
                    else:
                        selected_ship_name = cell.bateau.nom
                        instruction = f"{selected_ship_name} selectionne. Cliquez sur N, S, E ou O."

                elif my_turn and turn_mode == ActionTour.Deplacer:
                    direction = None
                    for button_name in ("north", "south", "east", "west"):
                        if net_buttons[button_name].clicked(pos):
                            direction = direction_from_button(button_name)
                            break
                    if direction is not None:
                        if selected_ship_name is None:
                            instruction = "Selectionnez d'abord un navire."
                        else:
                            ship = get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship is None:
                                selected_ship_name = None
                                instruction = "Navire introuvable."
                            else:
                                resultat, move_error = safe_move_ship(joueur1, ship, direction)
                                selected_ship_name = None
                                turn_mode = ActionTour.Tirer
                                if resultat == ResultatDeplacement.DEPLACE:
                                    move_used_this_turn = True
                                    same_player = partie.jouerTour(None)
                                    if same_player:
                                        instruction = f"{ship.nom} deplace. Vous pouvez encore tirer. Tours : {partie.ToursRestants}."
                                    else:
                                        move_used_this_turn = False
                                        reseau.envoyer("PASS")
                                        my_turn = False
                                        instruction = "Navire deplace. Tour adverse."
                                elif resultat == ResultatDeplacement.BLOQUE:
                                    instruction = "Deplacement bloque : navire deja touche."
                                else:
                                    instruction = move_error or "Deplacement invalide."

        # --- TRAITEMENT DES MESSAGES RÉSEAU ---
        incoming = reseau.recevoir()
        if incoming is None:
            show_game_over("Adversaire déconnecté. Retour au menu.")
            return
        if incoming:
            for line in incoming.strip().splitlines():
                if not line.strip():
                    continue
                parts = line.strip().split()

                if parts[0] == "TIR" and len(parts) == 3:
                    # L'adversaire tire sur notre plateau
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
                        instruction = "L'adversaire a joue. En attente..."
                        # Ne pas changer my_turn ici : on attend PASS ou REPLAY

                elif parts[0] == "RESULT" and len(parts) == 4:
                    # Résultat de notre tir sur l'adversaire
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

                    if status in (ResultatTir.INVALIDE, ResultatTir.DEJA_TIRE):
                        instruction = "Erreur de tir. Reessayez."
                        # my_turn reste True, le joueur peut retirer
                    else:
                        # Règle de tours identique aux modes locaux
                        same_player = partie.jouerTour(status)
                        msg_tir = {
                            ResultatTir.RATE: "Rate.",
                            ResultatTir.TOUCHE: "Touche !",
                            ResultatTir.COULE: "Coule !",
                        }.get(status, ".")
                        if same_player:
                            reseau.envoyer("REPLAY")
                            my_turn = True
                            instruction = f"{msg_tir} Vous rejouez. Tours restants : {partie.ToursRestants}."
                        else:
                            reseau.envoyer("PASS")
                            my_turn = False
                            move_used_this_turn = False
                            instruction = f"{msg_tir} Tour adverse."

                elif parts[0] == "REPLAY":
                    # L'adversaire a des tours bonus et continue
                    instruction = "L'adversaire rejoue !"

                elif parts[0] == "PASS":
                    # L'adversaire a terminé son tour — c'est notre tour
                    partie.joueurCourant = joueur1
                    partie.demarrerTour()
                    my_turn = True
                    move_used_this_turn = False
                    instruction = f"Votre tour ! Tours disponibles : {partie.ToursRestants}."

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
            Alignement.Horizontal,
            get_ship_by_name(game_ship_group, selected_ship_name) if selected_ship_name else None,
            left_label="VOTRE GRILLE",
            right_label="GRILLE ENNEMIE",
        )
        clock.tick(30)
