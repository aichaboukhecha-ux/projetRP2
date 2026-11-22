import random


# Probabilité qu'un gène mute
TAUX_MUTATION = 0.05


class Chromosome:
    def __init__(self, genes=None):
        # 63 gènes pour parcourir les 64 cases de l'échiquier
        if genes is None:
            # Génère des gènes aléatoires entre 1 et 8
            self.genes = [random.randint(1, 8) for _ in range(63)]
        else:
            self.genes = genes

    def crossover(self, partner):
        """Croisement à un point unique entre deux chromosomes."""
        # Les deux parents doivent avoir le même nombre de gènes
        assert len(self.genes) == len(partner.genes), \
            "crossover : les deux parents doivent avoir la même longueur"
        # Choisis un point de coupe aléatoire
        point = random.randint(1, len(self.genes) - 1)
        # Chaque enfant prend une partie des gènes de chaque parent
        child1_genes = self.genes[:point] + partner.genes[point:]
        child2_genes = partner.genes[:point] + self.genes[point:]
        return Chromosome(child1_genes), Chromosome(child2_genes)

    def mutation(self):
        """Chaque gène a une chance de devenir un déplacement aléatoire."""
        for i in range(len(self.genes)):
            # Avec une probabilité de 5%, le gène est remplacé au hasard
            if random.random() < TAUX_MUTATION:
                self.genes[i] = random.randint(1, 8)
