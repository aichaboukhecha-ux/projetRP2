import random

class Chromosome:
    def __init__(self, genes=None):
        # 63 moves for an 8x8 board (visiting 64 squares)
        if genes is None:
            self.genes = [random.randint(1, 8) for _ in range(63)]
        else:
            self.genes = genes

    def crossover(self, partner):
        """Single-point crossover to generate two offspring."""
        point = random.randint(1, 62)
        child1_genes = self.genes[:point] + partner.genes[point:]
        child2_genes = partner.genes[:point] + self.genes[point:]
        return Chromosome(child1_genes), Chromosome(child2_genes)

    def mutation(self, mutation_rate=0.05):
        """Mutates a gene with a given probability."""
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                self.genes[i] = random.randint(1, 8)