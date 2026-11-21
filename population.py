import random
from knight import Knight


class Population:
    def __init__(self, population_size):
        # Taille de la population
        self.population_size = population_size
        # Génération initiale
        self.generation = 1
        # Liste des cavaliers de la population
        self.knights = [Knight() for _ in range(population_size)]

    def check_population(self):
        """Vérifie les déplacements de chaque cavalier."""
        for knight in self.knights:
            knight.check_moves()

    def evaluate(self):
        """Évalue les cavaliers et renvoie le meilleur avec sa fitness."""
        max_fit = -1
        best_knight = None
        for knight in self.knights:
            fit = knight.evaluate_fitness()
            # Garde le cavalier ayant la plus grande fitness
            if fit > max_fit:
                max_fit = fit
                best_knight = knight
        return max_fit, best_knight

    def tournament_selection(self, size=3):
        """Sélection par tournoi : renvoie les 2 meilleurs parmi `size`."""
        # Tire `size` cavaliers au hasard
        competitors = random.sample(self.knights, size)
        # Les trie du meilleur au moins bon
        competitors.sort(key=lambda k: k.fitness, reverse=True)
        # Les deux premiers deviennent les parents
        return competitors[0], competitors[1]

    def create_new_generation(self):
        """Crée la génération suivante par croisement et mutation."""
        new_knights = []

        # Élitisme : garde le meilleur cavalier de la génération
        elite = max(self.knights, key=lambda k: k.fitness)
        new_knights.append(elite)

        while len(new_knights) < self.population_size:
            # Sélectionne deux parents par tournoi
            parent1, parent2 = self.tournament_selection(size=3)

            # Croisement à un point unique
            child1_chrom, child2_chrom = parent1.chromosome.crossover(parent2.chromosome)

            # Mutation de chaque enfant
            child1_chrom.mutation()
            child2_chrom.mutation()

            # Ajoute les enfants à la nouvelle population
            new_knights.append(Knight(child1_chrom))
            if len(new_knights) < self.population_size:
                new_knights.append(Knight(child2_chrom))

        self.knights = new_knights
        # Passe à la génération suivante
        self.generation += 1
