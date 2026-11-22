"""Teste la fenêtre du chemin de la solution (et la courbe conservée)."""
import random
import tkinter as tk

from population import Population
from interface import _TourPlayer, DIRECTION_NUM, DIRECTION_NOMS

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


# --- Résout une solution ---
random.seed(7)
pop = Population(50)
history = []
for gen in range(1, 801):
    pop.check_population()
    mf, best = pop.evaluate()
    history.append((gen, mf))
    if mf == 64:
        break
    pop.create_new_generation()
print(f"Solution gen {gen}, fitness {mf}\n")

# ============ COHERENCE DES Noms DE DIRECTIONS ============
print("=== Cohérence des noms de déplacements ===")
noms_inverse = {}
for num, nom in DIRECTION_NOMS.items():
    noms_inverse[nom] = num
check("8 noms de déplacements", len(DIRECTION_NOMS) == 8)
check("numéros 1 à 8 présents", sorted(DIRECTION_NOMS) == list(range(1, 9)))
# Vérifie que (dx,dy) -> numéro correspond aux directions du cavalier
check("DIRECTION_NUM inverse de Knight.DIRECTIONS",
      all(DIRECTION_NUM[v] == k for k, v in __import__("knight").Knight.DIRECTIONS.items()))

# ============ FENÊTRE CHEMIN ============
print("\n=== Fenêtre « Chemin de la solution » ===")
root = tk.Tk()
p = _TourPlayer(root, best.path, gen, history)

check("fenêtre fermée au départ", p.path_window is None)

p.toggle_path()
check("la fenêtre s'ouvre", p.path_window is not None)
check("titre = Chemin de la solution",
      p.path_window.title() == "Chemin de la solution",
      p.path_window.title())

# Récupère le widget Text
texte = None
for w in p.path_window.winfo_children():
    for c in w.winfo_children():
        if str(c.winfo_class()) == "Text":
            texte = c
        for cc in c.winfo_children():
            if str(cc.winfo_class()) == "Text":
                texte = cc
check("widget Text présent", texte is not None)

if texte is not None:
    contenu = texte.get("1.0", "end")
    lignes = [l for l in contenu.splitlines() if l.strip().startswith(tuple("0123456789"))]
    check("64 lignes de chemin", len(lignes) == 64, len(lignes))
    check("1re ligne = départ (0, 0)", "(0, 0)" in lignes[0], lignes[0])
    check("dernière ligne = case 64", lignes[-1].strip().startswith("64."), lignes[-1])

    # En-tête : génération + fitness
    entete_txt = ""
    for w in p.path_window.winfo_children():
        for c in w.winfo_children():
            if str(c.winfo_class()) == "Label":
                entete_txt = c.cget("text")
    check("en-tête affiche la génération", str(gen) in entete_txt, entete_txt)
    check("en-tête affiche la fitness 64", "64 / 64" in entete_txt, entete_txt)

    # Vérifie que chaque déplacement affiché est le BON
    mauvais = []
    for i in range(1, len(best.path)):
        pr = best.path[i - 1]
        cur = best.path[i]
        dx, dy = cur[0] - pr[0], cur[1] - pr[1]
        attendu = DIRECTION_NOMS[DIRECTION_NUM[(dx, dy)]]
        # La ligne i+1 du tableau (après l'entête et le séparateur)
        ligne = lignes[i]
        if attendu.split()[1] not in ligne:   # nom sans le numéro
            mauvais.append((i + 1, attendu, ligne.strip()))
    check("tous les déplacements affichés sont corrects",
          not mauvais, mauvais[:3])

# Referme
p.toggle_path()
check("la fenêtre se ferme", p.path_window is None)

# ============ LA COURBE EST TOUJOURS LÀ ============
print("\n=== Courbe conservée (HISTO) ===")
p.toggle_history()
check("fenêtre historique toujours disponible", p.history_window is not None)
p.toggle_history()
check("fermeture historique OK", p.history_window is None)

p.close()

# Deux fenêtres peuvent coexister
root2 = tk.Tk()
p2 = _TourPlayer(root2, best.path, gen, history)
p2.toggle_path()
p2.toggle_history()
check("chemin + historique ouverts en même temps",
      p2.path_window is not None and p2.history_window is not None)
p2.close()

print("\n" + "=" * 46)
print("RESULTAT : %d conformes, %d manquants" % (ok, fail))
print("=" * 46)
