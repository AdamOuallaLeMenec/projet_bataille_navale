from __future__ import annotations

import itertools
import random
from joueurs.joueur import Joueur, ActionTour
from plateau.plateau import Plateau
from plateau.case import Case
from navires.bateau import Alignement, DirectionDeplacement


class JoueurVirtuel(Joueur):
    def __init__(self, nom: str, plateau: Plateau, difficulty="easy"):
        super().__init__(nom, plateau)
        self.derniereCaseTouchee: tuple[int, int] | None = None
        self.second_hit: tuple[int, int] | None = None
        self.tested_no_hit = None
        self.tested_no_hit_2 = None
        self.difficulty = difficulty
        self.available_cells = self._populate_available_cells()

    def _populate_available_cells(self):
        return list(itertools.product(range(self.plateau.NB_LIGNES), range(self.plateau.NB_COLONNES)))

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
        nb_lignes = self.plateau.NB_LIGNES
        nb_colonnes = self.plateau.NB_COLONNES
        available_cells = [cell for cell in itertools.product(range(nb_lignes), range(nb_colonnes))]

        for ship in self.plateau.bateaux:
            attempts = 0
            max_attempts = 3000
            while True:
                attempts += 1
                if attempts > max_attempts:
                    raise RuntimeError(f"Placement IA impossible pour {ship.nom} après {max_attempts} essais")

                alignement = random.choice([Alignement.Horizontal, Alignement.Vertical])
                ship.orienter(alignement)

                if alignement == Alignement.Horizontal:
                    row = random.randint(0, nb_lignes - 1)
                    col = random.randint(0, nb_colonnes - ship.taille)
                else:
                    row = random.randint(0, nb_lignes - ship.taille)
                    col = random.randint(0, nb_colonnes - 1)

                coords = []
                for i in range(ship.taille):
                    r = row + (0 if alignement == Alignement.Horizontal else i)
                    c = col + (i if alignement == Alignement.Horizontal else 0)
                    coords.append((r, c))

                if all(coord in available_cells for coord in coords):
                    cases = [self.plateau.getCase(r, c) for r, c in coords]
                    if self.plateau.placementValide(ship, cases):
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
