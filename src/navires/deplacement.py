from plateau.case import Case
from navires.bateau import Bateau, DirectionDeplacement


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
