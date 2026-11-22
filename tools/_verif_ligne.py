"""Vérifie la ligne tracée le long du chemin dans l'interface.

Méthode : on rend le plateau deux fois au même instant, une fois avec la
ligne et une fois avec la ligne désactivée, puis on compare les images.
"""
import random
import tkinter as tk

from PIL import ImageDraw

from population import Population
from interface import _TourPlayer

ok = 0
fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("  [OK]     " + label)
    else:
        fail += 1
        print("  [MANQUE] " + label + ("  -> " + str(extra) if extra else ""))


def rendu_sans_ligne(p, w, h):
    """Rend le plateau en neutralisant le tracé de la ligne."""
    original = ImageDraw.ImageDraw.line
    ImageDraw.ImageDraw.line = lambda self, xy, fill=None, width=1, joint=None, **kw: None
    try:
        return p._compose_board(w, h)
    finally:
        ImageDraw.ImageDraw.line = original


def pixels_differents(a, b, pas=2):
    """Nombre de pixels différents entre deux images (échantillonnés)."""
    pa, pb = a.load(), b.load()
    largeur, hauteur = a.size
    n = 0
    for y in range(0, hauteur, pas):
        for x in range(0, largeur, pas):
            if pa[x, y][:3] != pb[x, y][:3]:
                n += 1
    return n


# --- Résout une solution ---
random.seed(7)
pop = Population(50)
for gen in range(1, 801):
    pop.check_population()
    mf, best = pop.evaluate()
    if mf == 64:
        break
    pop.create_new_generation()
print(f"Solution gen {gen}, fitness {mf}\n")

root = tk.Tk()
p = _TourPlayer(root, best.path, gen, [(gen, 64)])
W = H = 640

# ============ 1. AUCUNE LIGNE AU DÉBUT ============
print("=== Début de lecture ===")
for step in (0, 1):
    p.step = step
    avec, geom = p._compose_board(W, H)
    sans, _ = rendu_sans_ligne(p, W, H)
    diff = pixels_differents(avec, sans)
    check(f"step={step} : la ligne n'est pas encore tracée", diff == 0, diff)

# ============ 2. LA LIGNE APPARAÎT ET GRANDIT ============
print("\n=== Tracé progressif ===")
comptages = {}
for step in (2, 5, 20, 64):
    p.step = step
    avec, geom = p._compose_board(W, H)
    sans, _ = rendu_sans_ligne(p, W, H)
    comptages[step] = pixels_differents(avec, sans)
    print(f"    step={step:2d} -> {comptages[step]:5d} pixels de trait")

check("step=2 : la ligne est tracée", comptages[2] > 0, comptages[2])
check("la longueur du trait croît avec l'avancement",
      comptages[2] < comptages[5] < comptages[20] < comptages[64],
      comptages)

# ============ 3. LA LIGNE PASSE PAR LES CASES DU CHEMIN ============
print("\n=== Position du trait ===")
p.step = 64
avec, (x0, y0, x1, y1) = p._compose_board(W, H)
sans, _ = rendu_sans_ligne(p, W, H)
cw, ch = (x1 - x0) / 8, (y1 - y0) / 8
pa, ps = avec.load(), sans.load()

traces = 0
for i in range(63):
    # Plusieurs points le long du segment : certains tombent sous un numéro
    a, b = best.path[i], best.path[i + 1]
    ax, ay = x0 + (a[1] + 0.5) * cw, y0 + (a[0] + 0.5) * ch
    bx, by = x0 + (b[1] + 0.5) * cw, y0 + (b[0] + 0.5) * ch
    trouve = False
    for t in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        mx = round(ax + (bx - ax) * t)
        my = round(ay + (by - ay) * t)
        if pa[mx, my][:3] != ps[mx, my][:3]:
            trouve = True
            break
    if trouve:
        traces += 1
check("les 63 segments portent le trait", traces == 63, traces)

# ============ 4. LE TRAIT RESTE DANS LE PLATEAU ============
print("\n=== Bornes ===")
x0, y0, x1, y1 = geom
zone = avec.crop((0, 0, x0, H))
hors1 = pixels_differents(zone, rendu_sans_ligne(p, W, H)[0].crop((0, 0, x0, H)))
zone2 = avec.crop((x1, 0, W, H))
hors2 = pixels_differents(zone2, rendu_sans_ligne(p, W, H)[0].crop((x1, 0, W, H)))
check("pas de trait à gauche du plateau", hors1 == 0, hors1)
check("pas de trait à droite du plateau", hors2 == 0, hors2)

p.close()

print("\n" + "=" * 46)
print("RESULTAT : %d conformes, %d manquants" % (ok, fail))
print("=" * 46)
