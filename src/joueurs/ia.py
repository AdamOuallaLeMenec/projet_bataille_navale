from __future__ import annotations
import itertools
import random
from joueurs.joueur import Joueur, ActionTour
from plateau.plateau import Plateau
from plateau.case import Case
from navires.bateau import Bateau, Alignement, DirectionDeplacement


class JoueurVirtuel(Joueur):
    def __init__(self, nom: str, plateau: Plateau, difficulty="medium"):
        super().__init__(nom, plateau)
        self.difficulty = difficulty
        self.available_cells = [c for c in itertools.product(range(10), range(10))]
        self.reset_hit_logs()

    def reset_hit_logs(self):
        self.derniereCaseTouchee = None
        self.second_hit = None
        self.tested_no_hit = None
        self.tested_no_hit_2 = None

    def enemy_turn(self):
        # STRATÉGIE DE TRAQUE (Si un bateau est touché mais pas coulé)
        if self.derniereCaseTouchee:
            if self.tested_no_hit_2:
                self.second_hit = None
                pick = self.pick_target_after_first_hit()
            elif not self.second_hit:
                pick = self.pick_target_after_first_hit()
            else:
                pick = self.pick_target_after_second_hit()

        # STRATÉGIE DE RECHERCHE (Si aucun bateau n'est en cours de traque)
        else:
            if self.difficulty == "hard":
                pick = self.get_best_statistical_move()
            else:
                pick = random.choice(self.available_cells)

        if pick in self.available_cells:
            self.available_cells.remove(pick)
        return pick

    def get_best_statistical_move(self) -> tuple[int, int]:
        """IA HARD: Calcule la case avec la probabilité la plus élevée."""
        heatmap = [[0 for _ in range(10)] for _ in range(10)]
        bateaux_restants = [5, 4, 3, 3, 2]  # Tailles standards

        for r, c in self.available_cells:
            for taille in bateaux_restants:
                for is_horiz in [True, False]:
                    tient = True
                    for i in range(taille):
                        nr, nc = (r, c + i) if is_horiz else (r + i, c)
                        if (nr, nc) not in self.available_cells:
                            tient = False
                            break
                    if tient:
                        for i in range(taille):
                            nr, nc = (r, c + i) if is_horiz else (r + i, c)
                            heatmap[nr][nc] += 1

        max_val = -1
        best_coords = self.available_cells[0]
        for r, c in self.available_cells:
            if heatmap[r][c] > max_val:
                max_val = heatmap[r][c]
                best_coords = (r, c)
        return best_coords

    def pick_target_after_first_hit(self):
        r, c = self.derniereCaseTouchee
        targets = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        valid = [t for t in targets if t in self.available_cells]
        return random.choice(valid) if valid else random.choice(self.available_cells)

    def pick_target_after_second_hit(self, dist=1):
        r1, c1 = self.derniereCaseTouchee
        r2, c2 = self.second_hit
        if r1 == r2:  # Horizontal
            targets = [(r1, max(c1, c2) + dist), (r1, min(c1, c2) - dist)]
        else:  # Vertical
            targets = [(max(r1, r2) + dist, c1), (min(r1, r2) - dist, c1)]

        valid = [t for t in targets if t in self.available_cells]
        if valid: return random.choice(valid)
        return random.choice(self.available_cells)

    def choisirCibleIntelligente(self, ennemi: Joueur) -> Case:
        row, col = self.enemy_turn()
        return ennemi.getPlateau().getCase(row, col)

    def randomise_ships(self):
        """Place les bateaux aléatoirement en respectant le voisinage."""
        for ship in self.plateau.bateaux:
            place = False
            while not place:
                align = random.choice([Alignement.Horizontal, Alignement.Vertical])
                ship.orienter(align)
                r = random.randint(0, 9 - (ship.taille if align == Alignement.Vertical else 0))
                c = random.randint(0, 9 - (ship.taille if align == Alignement.Horizontal else 0))
                cases = self.plateau.calculer_cases_pour_bateau(ship, r, c, align)
                if self.plateau.placementValide(ship, cases):
                    self.plateau.placerBateau(ship, cases)
                    place = True