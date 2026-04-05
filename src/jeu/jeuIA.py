import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN


def run_ia_game(difficulty: str):
    """Boucle principale du mode joueur contre IA."""
    import main as m

    player_plateau = m.Plateau(m.PLAYER_GRID_X, m.GRID_Y)
    enemy_plateau = m.Plateau(m.ENEMY_GRID_X, m.GRID_Y)

    joueur1 = m.JoueurHumain("Joueur", player_plateau)
    joueur2 = m.JoueurVirtuel("IA", enemy_plateau, difficulty=difficulty)

    fleet_counts_player, fleet_counts_enemy = m.generate_balanced_fleet_pair()
    fleet_spec_player = m.build_fleet_spec(fleet_counts_player)
    fleet_spec_enemy = m.build_fleet_spec(fleet_counts_enemy)

    partie = m.Partie(joueur1, joueur2)
    partie.demarrer()

    ship_group = m.create_fleet_sprites(fleet_spec_player)
    enemy_ships = m.create_enemy_fleet(fleet_spec_enemy)
    joueur2.plateau.bateaux = enemy_ships
    try:
        joueur2.randomise_ships()
    except RuntimeError:
        return False   # signal à main() pour relancer

    hit_list = pygame.sprite.Group()

    if not m.set_up_player_ships(joueur1, joueur2, ship_group, hit_list):
        return True

    joueur1.plateau.bateaux = list(ship_group)
    partie.demarrerTour()
    game_ship_group = pygame.sprite.Group(joueur1.plateau.bateaux)

    buttons = m.setup_buttons()
    m.current_buttons = {k: v for k, v in buttons.items() if
                         k in ["menu", "action_tir", "action_move", "north", "south", "east", "west"]}

    turn_mode = m.ActionTour.Tirer
    alignement_move = m.Alignement.Horizontal
    m.current_turn_mode[0] = turn_mode
    m.current_alignement[0] = alignement_move

    selected_ship_name = None
    move_used_this_turn = False
    instruction = "Votre tour : tirez sur la grille ennemie ou choisissez Deplacement."
    clock = pygame.time.Clock()

    playing = True
    while playing:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                m.sys.exit()

            if event.type == MOUSEBUTTONDOWN:
                pos = event.pos

                if m.current_buttons["menu"].clicked(pos):
                    playing = False
                    break

                elif m.current_buttons["action_tir"].clicked(pos):
                    turn_mode = m.ActionTour.Tirer
                    m.current_turn_mode[0] = turn_mode
                    selected_ship_name = None
                    instruction = "Mode tir actif. Cliquez sur la grille ennemie."

                elif m.current_buttons["action_move"].clicked(pos):
                    if move_used_this_turn:
                        turn_mode = m.ActionTour.Tirer
                        m.current_turn_mode[0] = turn_mode
                        selected_ship_name = None
                        instruction = "Deplacement deja utilise pour ce tour. Il vous reste seulement des tirs."
                    else:
                        turn_mode = m.ActionTour.Deplacer
                        m.current_turn_mode[0] = turn_mode
                        instruction = "Mode deplacement actif : choisissez un navire puis cliquez sur N, S, E ou O."

                elif turn_mode == m.ActionTour.Tirer and enemy_plateau.rect.collidepoint(pos):
                    cell = enemy_plateau.get_cell_from_pixel(*pos)
                    if cell is not None:
                        instruction, consumed_action, finished, tir_result = _apply_hit_to_enemy(
                            joueur1, joueur2, cell, hit_list, m
                        )
                        if finished:
                            m.refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                             m.current_buttons, instruction, turn_mode, alignement_move)
                            pygame.time.wait(1200)
                            partie.determinerVainqueur()
                            winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur1.nom
                            m.show_game_over(f"Vainqueur : {winner_name}")
                            playing = False
                            break

                        if consumed_action:
                            defeat = False
                            same_player = partie.jouerTour(tir_result)
                            if same_player:
                                instruction = f"{instruction} Tours restants: {partie.ToursResatants}."
                            else:
                                move_used_this_turn = False
                                instruction, defeat = _enemy_take_turn(partie, joueur2, joueur1, hit_list, m)
                            if defeat:
                                m.refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                                 m.current_buttons, instruction, turn_mode, alignement_move)
                                pygame.time.wait(1200)
                                partie.determinerVainqueur()
                                winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur2.nom
                                m.show_game_over(f"Vainqueur : {winner_name}")
                                playing = False
                                break

                elif turn_mode == m.ActionTour.Deplacer and player_plateau.rect.collidepoint(pos):
                    cell = player_plateau.get_cell_from_pixel(*pos)
                    if cell is None:
                        instruction = "Case invalide."
                    elif cell.bateau is None:
                        instruction = "Choisissez d'abord un de vos navires."
                    else:
                        selected_ship_name = cell.bateau.nom
                        instruction = f"{selected_ship_name} selectionne. Cliquez sur N, S, E ou O."

                elif turn_mode == m.ActionTour.Deplacer:
                    direction = None
                    for button_name in ("north", "south", "east", "west"):
                        if m.current_buttons[button_name].clicked(pos):
                            direction = m.direction_from_button(button_name)
                            break
                    if direction is not None:
                        if selected_ship_name is None:
                            instruction = "Selectionnez d'abord un navire a deplacer."
                        else:
                            ship = m.get_ship_by_name(game_ship_group, selected_ship_name)
                            if ship is None:
                                selected_ship_name = None
                                instruction = "Navire introuvable."
                            else:
                                resultat, move_error = m.safe_move_ship(joueur1, ship, direction)
                                selected_ship_name = None
                                turn_mode = m.ActionTour.Tirer
                                m.current_turn_mode[0] = turn_mode
                                if resultat == m.ResultatDeplacement.DEPLACE:
                                    move_used_this_turn = True
                                    defeat = False
                                    same_player = partie.jouerTour(None)
                                    if same_player:
                                        instruction = f"{ship.nom} deplace d'une case. Vous pouvez encore tirer. Tours restants: {partie.ToursResatants}."
                                    else:
                                        move_used_this_turn = False
                                        instruction, defeat = _enemy_take_turn(partie, joueur2, joueur1, hit_list, m)
                                    if defeat:
                                        m.refresh_screen(joueur1.plateau, joueur2.plateau, game_ship_group, hit_list,
                                                         m.current_buttons, instruction, turn_mode, alignement_move)
                                        pygame.time.wait(1200)
                                        partie.determinerVainqueur()
                                        winner_name = partie.Vainqueur.nom if partie.Vainqueur else joueur2.nom
                                        m.show_game_over(f"Vainqueur : {winner_name}")
                                        playing = False
                                        break
                                elif resultat == m.ResultatDeplacement.BLOQUE:
                                    instruction = "Deplacement bloque : navire deja touche."
                                else:
                                    instruction = move_error or "Deplacement invalide : collision, superposition ou sortie de grille."

        selected_ship = m.get_ship_by_name(game_ship_group, selected_ship_name) if selected_ship_name else None
        m.refresh_screen(
            joueur1.plateau,
            joueur2.plateau,
            game_ship_group,
            hit_list,
            m.current_buttons,
            instruction,
            turn_mode,
            alignement_move,
            selected_ship,
        )
        clock.tick(30)

    return True


def _apply_hit_to_enemy(player, enemy, cible, hit_list, m):
    resultat = player.tirer(enemy, cible)
    center = cible.rect.center

    if resultat == m.ResultatTir.DEJA_TIRE:
        return "Cette case a deja ete visee.", False, False, None

    if resultat in (m.ResultatTir.TOUCHE, m.ResultatTir.COULE):
        hit_list.add(m.CellHit(m.asset_path("Sprites/hit.png"), center))
        m.play_sound("sink" if resultat == m.ResultatTir.COULE else "hit")
        if enemy.plateau.tousLesBateauxCoules():
            return "Tous les navires ennemis sont coules. Victoire !", True, True, resultat
        return ("Touche !" if resultat == m.ResultatTir.TOUCHE else "Coule !"), True, False, resultat

    hit_list.add(m.CellHit(m.asset_path("Sprites/miss.png"), center))
    m.play_sound("miss")
    return "Rate.", True, False, resultat


def _enemy_take_turn(partie, enemy, player, hit_list, m):
    instruction = ""
    while partie.joueurCourant == enemy:
        cible = enemy.choisirCibleIntelligente(player)
        resultat = enemy.tirer(player, cible)
        center = cible.rect.center

        if resultat in (m.ResultatTir.TOUCHE, m.ResultatTir.COULE):
            hit_list.add(m.CellHit(m.asset_path("Sprites/hit.png"), center))
            if not enemy.derniereCaseTouchee:
                enemy.derniereCaseTouchee = (cible.ligne, cible.colonne)
            elif enemy.second_hit != (cible.ligne, cible.colonne):
                enemy.second_hit = (cible.ligne, cible.colonne)
            m.play_sound("sink" if resultat == m.ResultatTir.COULE else "hit")
            instruction = f"L'ennemi a {'coule' if resultat == m.ResultatTir.COULE else 'touche'} un de vos navires. Il rejoue."
            if resultat == m.ResultatTir.COULE:
                enemy.reset_hit_logs()
            if player.plateau.tousLesBateauxCoules():
                return "Tous vos navires sont coules. Defaite !", True
        else:
            hit_list.add(m.CellHit(m.asset_path("Sprites/miss.png"), center))
            m.play_sound("miss")
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

        m.refresh_screen(
            player.plateau,
            enemy.plateau,
            pygame.sprite.Group(player.plateau.bateaux),
            hit_list,
            m.current_buttons,
            instruction,
            m.current_turn_mode[0],
            m.current_alignement[0],
        )
        pygame.time.wait(800)

    return instruction, False
