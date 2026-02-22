from jeu.fin_partie import Joueur
from jeu.fin_partie import Partie

joueur1 = Joueur("Aïcha")
joueur2 = Joueur("IA", est_ia=True)

partie = Partie(joueur1, joueur2)
partie.lancer_partie()
