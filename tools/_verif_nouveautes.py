"""Teste les 3 nouveautés : coordonnées, historique, export."""
import json
import random
import tkinter as tk

from population import Population
from interface import _TourPlayer
from export import export_solution

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
print(f"Solution gen {gen}, fitness {mf}, historique {len(history)} points\n")

# ============ 1. COORDONNÉES 1-8 ============
print("=== 1. COORDONNÉES (Figure 2) ===")
root = tk.Tk()
p = _TourPlayer(root, best.path, gen, history)

# Liste tous les textes du canvas
texts = []
for item in p.canvas.find_all():
    if p.canvas.type(item) == "text":
        texts.append(p.canvas.itemcget(item, "text"))

# Les 8 chiffres doivent apparaître 4 fois (haut, bas, gauche, droite)
for n in range(1, 9):
    count = texts.count(str(n))
    check(f"chiffre {n} présent 4 fois (haut/bas/gauche/droite)", count == 4, count)

# Vérifie qu'il y a bien 32 étiquettes au total
check("32 étiquettes au total (8 x 4 côtés)", len(texts) == 32, len(texts))
p.close()

# ============ 11. HISTORIQUE ============
print("\n=== 11. HISTORIQUE (courbe fitness/génération) ===")
root2 = tk.Tk()
p2 = _TourPlayer(root2, best.path, gen, history)
check("l'historique est stocké", len(p2.history) == len(history), len(p2.history))
check("fenêtre d'historique fermée au départ", p2.history_window is None)

# Ouvre la courbe
p2.toggle_history()
check("la fenêtre s'ouvre", p2.history_window is not None)
check("titre = Historique des générations",
      p2.history_window.title() == "Historique des générations",
      p2.history_window.title())

# Compte les éléments dessinés sur le canvas de la courbe
hist_canvas = None
for child in p2.history_window.winfo_children():
    if str(child.winfo_class()) == "Canvas":
        hist_canvas = child
check("canvas de la courbe présent", hist_canvas is not None)
if hist_canvas is not None:
    items = hist_canvas.find_all()
    # 2 axes + 5 lignes grille + 5 étiquettes fitness
    #   + 3 étiquettes génération + 1 courbe + 2 titres = 18
    check("courbe et axes dessinés (18 éléments)", len(items) == 18, len(items))
    # La courbe doit être une polyligne avec un point par génération
    lignes = [hist_canvas.type(i) for i in items if hist_canvas.type(i) == "line"]
    longueurs = []
    for i in items:
        if hist_canvas.type(i) == "line":
            coords = hist_canvas.coords(i)
            longueurs.append(len(coords) // 2)
    check("la courbe relie tous les points d'historique",
          max(longueurs) == len(history), (max(longueurs), len(history)))
    # Cherche le texte du titre
    titres = [hist_canvas.itemcget(i, "text") for i in items
              if hist_canvas.type(i) == "text"]
    check("titre FITNESS / GENERATION affiché",
          any("FITNESS" in t for t in titres), titres[:3])

# Referme
p2.toggle_history()
check("la fenêtre se ferme", p2.history_window is None)

# Sans historique : ne doit pas planter
root2.destroy()
root3 = tk.Tk()
p3 = _TourPlayer(root3, best.path, gen, None)
p3.toggle_history()
check("pas de plantage sans historique", True)
p3.close()

# ============ 12. EXPORT ============
print("\n=== 12. EXPORT (texte + JSON) ===")
txt, js = export_solution(best, gen, history, directory=".")

check("solution.txt créé", txt.exists())
check("solution.json créé", js.exists())

contenu = txt.read_text(encoding="utf-8")
check("txt contient la génération", f"Génération : {gen}" in contenu)
check("txt contient la fitness 64", "Fitness    : 64 / 64" in contenu)
check("txt liste les 64 cases", contenu.count(". (") == 64, contenu.count(". ("))

donnees = json.loads(js.read_text(encoding="utf-8"))
check("json contient generation", donnees.get("generation") == gen)
check("json contient fitness 64", donnees.get("fitness") == 64)
check("json contient 64 positions", len(donnees.get("path", [])) == 64)
check("json path[0] = [0,0]", donnees.get("path", [[None]])[0] == [0, 0])
check("json contient l'historique", len(donnees.get("history", [])) == len(history))
check("json historique[0] a generation+fitness",
      set(donnees["history"][0].keys()) == {"generation", "fitness"})

# Le chemin JSON correspond bien au path du knight
check("chemin JSON identique au path du knight",
      [tuple(x) for x in donnees["path"]] == list(best.path))

print("\n" + "=" * 46)
print("RESULTAT : %d conformes, %d manquants" % (ok, fail))
print("=" * 46)
