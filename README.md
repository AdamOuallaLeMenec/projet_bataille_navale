# Bataille Navale

Version modifiée du jeu de société Bataille Navale, développée en Python avec Pygame. Le jeu propose plusieurs modes de jeu, une IA avec deux niveaux de difficulté, et un mode réseau en local.

---

## Modes de jeu

- **Joueur vs IA** — difficulté facile ou difficile
- **2 joueurs local** — sur le même écran, à tour de rôle
- **2 joueurs réseau (LAN)** — via le réseau local, hôte ou client

---

## Règles

Chaque joueur dispose d'un plateau de 22×22 cases. Les navires sont placés secrètement avant la partie et doivent respecter des contraintes d'espacement. À chaque tour, le joueur peut :
- **Tirer** sur une case adverse (un tir par tour minimum)
- **Déplacer** l'un de ses navires d'une case (une seule fois par tour)

La partie se termine quand tous les navires d'un camp sont coulés.

**Tours supplémentaires** : si le joueur possède un porte-avions vivant, il reçoit des tours bonus selon le nombre de navires restants. Couler un navire ennemi accorde également un tour supplémentaire.

---

## Navires disponibles

| Navire | Taille |
|---|---|
| Porte-avion | 5 |
| Cuirassé | 4 |
| Sous-marin | 3 |
| Destroyer | 3 |
| Patrouilleur | 2 |

La composition de la flotte est générée aléatoirement et est identique pour les deux joueurs.

---

## Lancer le jeu

```bash
cd src
python main.py
```

**Prérequis** : Python 3.10+ et Pygame (`pip install pygame`)

---

## Mode réseau

1. Le joueur hôte clique sur **Créer une partie** — son IP locale est affichée à l'écran
2. Le joueur client clique sur **Rejoindre une partie**, saisit l'IP de l'hôte et appuie sur Entrée
3. Une fois la connexion établie, cliquer sur **Lancer la partie**

Les deux joueurs doivent être sur le même réseau local. Port utilisé : **5000**.

---

## Structure du projet

```
src/
├── main.py              # Point d'entrée, UI, menus
├── jeuLocal.py          # Boucle de jeu réseau LAN
├── reseauLocal.py       # Couche socket TCP
├── jeu/
│   ├── jeuIA.py         # Boucle de jeu joueur vs IA
│   └── fin_partie.py    # Gestion des tours et victoire
├── joueurs/
│   ├── joueur.py        # Classes Joueur et JoueurHumain
│   └── ia.py            # IA (JoueurVirtuel)
├── navires/
│   └── bateau.py        # Classe Bateau
├── plateau/
│   ├── plateau.py       # Grille, placement, déplacement
│   └── case.py          # Case individuelle
├── Sprites/             # Images des navires et marqueurs
├── Sounds/              # Musiques
└── Fonts/               # Polices
Diagrammes/              # Diagrammes UML
```

---

## Diagrammes UML

- Diagramme de cas d'utilisation
- Diagramme de classes
- Diagrammes de séquence : tir, réception d'un tir, validité du plateau, parcours IA
- Diagrammes d'activité : déroulement d'une partie, configuration

---

## Outils utilisés

- **Python + Pygame** — implémentation et interface graphique
- **Git & GitHub** — gestion de versions et collaboration
- **Visual Studio Code** — environnement de développement
- **Draw.io & LucidChart** — création des diagrammes UML