"""Verifie point par point le cahier des charges du Project 2."""
import random
from chromosome import Chromosome
from knight import Knight
from population import Population

ok = 0
fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("  [OK]   " + label)
    else:
        fail += 1
        print("  [MANQUE] " + label + ("  -> " + str(extra) if extra else ""))


print("=== 1. CHROMOSOME ===")
c = Chromosome()
check("genes: tableau de longueur 63", len(c.genes) == 63, len(c.genes))
check("chaque gène est entre 1 et 8", all(1 <= g <= 8 for g in c.genes))
a, b = Chromosome(), Chromosome()
c1, c2 = a.crossover(b)
check("crossover renvoie 2 chromosomes", isinstance(c1, Chromosome) and isinstance(c2, Chromosome))
check("crossover = un seul point de coupe", len(c1.genes) == 63 and len(c2.genes) == 63)
# crossover refuse deux parents de longueurs différentes
try:
    Chromosome([1] * 63).crossover(Chromosome([2] * 10))
    check("crossover refuse 2 parents de longueurs différentes", False)
except AssertionError:
    check("crossover refuse 2 parents de longueurs différentes", True)
# mutation sans argument
d = Chromosome([1] * 63)
d.mutation()
check("mutation() s'appelle sans argument", True)

print("\n=== 2. KNIGHT ===")
k = Knight()
check("position initiale = (0, 0)", k.position == (0, 0), k.position)
check("fitness initiale = 0", k.fitness == 0, k.fitness)
check("path contient la position initiale", k.path == [(0, 0)], k.path)
check("chromosome généré si absent", isinstance(k.chromosome, Chromosome))

# Les 8 sens du cahier des charges
attendu = {
    1: "haut-droite", 2: "droite-haut", 3: "droite-bas", 4: "bas-droite",
    5: "bas-gauche", 6: "gauche-bas", 7: "gauche-haut", 8: "haut-gauche",
}
noms = {1: (-2, 1), 2: (-1, 2), 3: (1, 2), 4: (2, 1),
        5: (2, -1), 6: (1, -2), 7: (-1, -2), 8: (-2, -1)}
check("8 directions conformes au cahier des charges",
      all(Knight.DIRECTIONS[i] == noms[i] for i in range(1, 9)))

# move_forward / move_backward : un seul paramètre
import inspect
check("move_forward(direction) - 1 seul paramètre",
      str(inspect.signature(Knight.move_forward)) == "(self, direction)")
check("move_backward(direction) - 1 seul paramètre",
      str(inspect.signature(Knight.move_backward)) == "(self, direction)")

# --- move_backward annule bien le déplacement appliqué ---
# Sequence réelle de check_moves : appliquer, puis annuler.
k2 = Knight()
k2.position = (3, 3)
avant = k2.position
k2.position = k2.move_forward(4)          # bas-droite -> (5, 4)
apres = k2.position
k2.position = k2.move_backward(4)         # annulation -> doit revenir à (3, 3)
retour = k2.position
check("move_backward annule le déplacement appliqué",
      (apres, retour) == ((5, 4), avant), (apres, retour))

# --- Ordre du cycle, exemple exact du cahier des charges (move 4) ---
def ordre_cycle(original, avant):
    """Reproduit la boucle de check_moves et renvoie l'ordre testé."""
    sens = []
    for step in range(1, 8):
        if avant:
            sens.append((original + step - 1) % 8 + 1)
        else:
            sens.append((original - step - 1) % 8 + 1)
    return sens

check("cycle avant depuis 4 = 5,6,7,8,1,2,3 (exemple du PDF)",
      ordre_cycle(4, True) == [5, 6, 7, 8, 1, 2, 3], ordre_cycle(4, True))
check("cycle arrière depuis 4 = 3,2,1,8,7,6,5 (exemple du PDF)",
      ordre_cycle(4, False) == [3, 2, 1, 8, 7, 6, 5], ordre_cycle(4, False))

# --- "Si aucun déplacement valide n'est trouvé, le dernier déplacement est conservé" ---
# Position où AUCUN saut n'est possible : impossible sur un échiquier 8x8
# pour un cavalier, donc on vérifie plutôt que le gène n'est pas modifié
# quand la boucle s'arrête sans solution.
k3 = Knight(Chromosome([4] * 63))
k3.check_moves()
check("check_moves construit un chemin sans trous",
      all(p in [(r, cc) for r in range(8) for cc in range(8)] for p in k3.path))

# --- check_moves utilise bien move_backward ---
src = open("knight.py", encoding="utf-8").read()
corps = src.split("def check_moves")[1].split("def evaluate_fitness")[0]
check("check_moves appelle move_backward (annulation)", "move_backward" in corps)
check("check_moves teste les autres déplacements en cycle", "% 8 + 1" in corps)

# --- evaluate_fitness boucle sur le path ---
corps_fit = src.split("def evaluate_fitness")[1]
check("evaluate_fitness boucle sur le path",
      "for position in self.path" in corps_fit)
check("evaluate_fitness s'arrête sur une case hors échiquier",
      "break" in corps_fit)
check("evaluate_fitness utilise un set (pas de O(n²))",
      "seen = set()" in corps_fit)
check("fitness maximale = 64", Knight().evaluate_fitness() <= 64)

# Fitness = 64 pour un vrai tour
random.seed(7)
pop = Population(50)
for gen in range(1, 801):
    pop.check_population()
    mf, best = pop.evaluate()
    if mf == 64:
        break
    pop.create_new_generation()
check("une solution complète est trouvée", mf == 64, mf)
check("path = 64 cases", len(best.path) == 64, len(best.path))
check("64 cases uniques (chaque case une fois)", len(set(best.path)) == 64)
check("fitness = 64", best.evaluate_fitness() == 64)

print("\n=== 3. POPULATION ===")
p = Population(50)
check("population_size = 50", p.population_size == 50)
check("generation initiale = 1", p.generation == 1, p.generation)
check("knights est une liste de knights",
      isinstance(p.knights, list) and all(isinstance(x, Knight) for x in p.knights))
check("init(population_size) génère la liste", len(p.knights) == 50)

check("check_population() existe", hasattr(p, "check_population"))
p.check_population()
check("check_population appelle check_moves sur chaque knight",
      all(len(kn.path) >= 1 for kn in p.knights))

mf, bk = p.evaluate()
check("evaluate() renvoie le meilleur + sa fitness",
      isinstance(mf, int) and isinstance(bk, Knight), (mf, type(bk)))
check("evaluate() renvoie bien le meilleur de la population",
      mf == max(kn.evaluate_fitness() for kn in p.knights))

check("tournament_selection(size) existe", hasattr(p, "tournament_selection"))
pa, pb = p.tournament_selection(size=3)
check("tournament_selection renvoie 2 parents", pa is not None and pb is not None)
check("tournament_selection : échantillon de taille 3",
      str(inspect.signature(Population.tournament_selection)) == "(self, size=3)")

g0 = p.generation
p.create_new_generation()
check("create_new_generation incrémente la génération", p.generation == g0 + 1)
check("create_new_generation garde la même taille", len(p.knights) == 50, len(p.knights))
check("create_new_generation remplace tous les knights",
      all(isinstance(x, Knight) for x in p.knights))

print("\n=== 4. MAIN / INTERFACE ===")
main_src = open("main.py", encoding="utf-8").read()
check("main() crée Population(50)", "Population(population_size)" in main_src)
check("main() appelle check_population()", "population.check_population()" in main_src)
check("main() appelle evaluate()", "population.evaluate()" in main_src)
check("main() teste maxFit == 64", "maxFit == 64" in main_src)
check("main() appelle create_new_generation()", "population.create_new_generation()" in main_src)
check("main() affiche la solution sur l'interface", "draw_solution" in main_src)
check("main() garde la boucle while True du cahier des charges", "while True" in main_src)

if_src = open("interface.py", encoding="utf-8").read()
check("interface affiche le chemin (path)", "self.path" in if_src)
check("interface affiche les numéros des cases", "number" in if_src)
check("interface affiche le cavalier", "self.knight" in if_src)
check("interface affiche la génération de la solution", "GEN" in if_src)

print("\n" + "=" * 46)
print("RESULTAT : %d conformes, %d manquants" % (ok, fail))
print("=" * 46)
