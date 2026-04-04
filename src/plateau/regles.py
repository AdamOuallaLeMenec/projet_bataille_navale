from navires.bateau import Alignement
from plateau.plateau import Plateau
from plateau.case import Case

################ 
def placement_valide(plateau: Plateau, bateau, start_row: int, start_col: int, alignement: Alignement) -> bool:
    cases = plateau.calculer_cases_pour_bateau(bateau, start_row, start_col, alignement)
    return cases is not None and len(cases) == bateau.taille


def deplacement_valide(plateau: Plateau, bateau, direction) -> bool:
    return plateau.deplacementValide(bateau, direction)
