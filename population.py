import random
from knight import Knight

class Population:
    def __init__(self, population_size):
        self.population_size = population_size
        self.generation = 1
        self.knights = [Knight() for _ in range(population_size)]

    def check_population(self):
        """Checks and repairs moves for all knights."""
        for knight in self.knights:
            knight.check_moves()

    def evaluate(self):
        """Evaluates all knights and returns the best fitness and knight."""
        max_fit = -1
        best_knight = None
        for knight in self.knights:
            fit = knight.evaluate_fitness()
            if fit > max_fit:
                max_fit = fit
                best_knight = knight
        return max_fit, best_knight

    def tournament_selection(self, size=3):
        """Selects two parents using tournament selection."""
        competitors = random.sample(self.knights, size)
        competitors.sort(key=lambda k: k.fitness, reverse=True)
        return competitors[0], competitors[1]

    def create_new_generation(self):
        """Generates the next generation using Crossover and Mutation."""
        new_knights = []

        # Elitism: carry the best knight of this generation forward unchanged
        # so progress can never be lost to random crossover/mutation.
        elite = max(self.knights, key=lambda k: k.fitness)
        new_knights.append(elite)

        while len(new_knights) < self.population_size:
            parent1, parent2 = self.tournament_selection(size=3)
            
            # Crossover
            child1_chrom, child2_chrom = parent1.chromosome.crossover(parent2.chromosome)
            
            # Mutation
            child1_chrom.mutation()
            child2_chrom.mutation()
            
            # Create new knights
            new_knights.append(Knight(child1_chrom))
            if len(new_knights) < self.population_size:
                new_knights.append(Knight(child2_chrom))
                
        self.knights = new_knights
        self.generation += 1