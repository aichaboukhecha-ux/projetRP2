import random
from chromosome import Chromosome


class Knight:
    # Les 8 déplacements possibles du cavalier sous la forme (dx, dy)
    # 1: haut-droite, 2: droite-haut, 3: droite-bas, 4: bas-droite
    # 5: bas-gauche, 6: gauche-bas, 7: gauche-haut, 8: haut-gauche
    DIRECTIONS = {
        1: (-2, 1), 2: (-1, 2), 3: (1, 2), 4: (2, 1),
        5: (2, -1), 6: (1, -2), 7: (-1, -2), 8: (-2, -1)
    }

    def __init__(self, chromosome=None):
        # Génère un chromosome aléatoire si aucun n'est donné
        self.chromosome = chromosome if chromosome else Chromosome()
        # Position de départ du cavalier
        self.position = (0, 0)
        # Liste des cases déjà visitées
        self.path = [self.position]
        # Nombre de cases visitées (64 au maximum)
        self.fitness = 0

    def move_forward(self, direction):
        """Renvoie la nouvelle position après le déplacement."""
        dx, dy = self.DIRECTIONS[direction]
        return (self.position[0] + dx, self.position[1] + dy)

    def move_backward(self, direction):
        """Annule le déplacement et revient à la case précédente."""
        dx, dy = self.DIRECTIONS[direction]
        return (self.position[0] - dx, self.position[1] - dy)

    def is_valid(self, pos):
        """Vérifie que la case est sur l'échiquier et non visitée."""
        x, y = pos
        # La case doit être comprise entre 0 et 7
        if 0 <= x < 8 and 0 <= y < 8:
            # La case ne doit pas déjà être dans le chemin
            if pos not in self.path:
                return True
        return False

    def check_moves(self):
        """Valide et répare les gènes, puis construit le chemin."""
        # On repart de la case de départ
        self.path = [(0, 0)]
        self.position = (0, 0)

        # Sens du cycle choisi une seule fois pour tout le chromosome
        cycle_forward = random.choice([True, False])

        for i in range(63):
            # Déplacement indiqué par le gène
            original_move = self.chromosome.genes[i]

            # Applique le déplacement
            self.position = self.move_forward(original_move)

            # Si la case est valide, on la garde
            if self.is_valid(self.position):
                self.path.append(self.position)
                continue

            # Sinon on annule le déplacement illégal
            self.position = self.move_backward(original_move)

            # Teste les 7 autres déplacements dans le bon sens du cycle
            found_valid = False
            for step in range(1, 8):
                if cycle_forward:
                    new_move = (original_move + step - 1) % 8 + 1
                else:
                    new_move = (original_move - step - 1) % 8 + 1

                # Vérifie si ce déplacement est possible
                candidate = self.move_forward(new_move)
                if self.is_valid(candidate):
                    # Répare le gène et avance le cavalier
                    self.chromosome.genes[i] = new_move
                    self.position = candidate
                    self.path.append(self.position)
                    found_valid = True
                    break

            # Aucun déplacement valide : on garde le gène et on arrête
            if not found_valid:
                break

    def evaluate_fitness(self):
        """Compte les cases valides jusqu'au premier déplacement invalide."""
        self.fitness = 0
        for i in range(len(self.path)):
            x, y = self.path[i]
            # Case hors de l'échiquier : on s'arrête
            if not (0 <= x < 8 and 0 <= y < 8):
                break
            # Case déjà visitée : on s'arrête
            if self.path[i] in self.path[:i]:
                break
            # Saut qui n'est pas un déplacement de cavalier : on s'arrête
            if i > 0:
                dx = self.path[i][0] - self.path[i - 1][0]
                dy = self.path[i][1] - self.path[i - 1][1]
                if (dx, dy) not in self.DIRECTIONS.values():
                    break
            # Case valide : on incrémente la fitness
            self.fitness += 1
        return self.fitness
