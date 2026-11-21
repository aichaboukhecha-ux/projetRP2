from population import Population
from interface import draw_solution

# Nombre maximal de générations (évite une boucle infinie)
MAX_GENERATIONS = 5000


def main():
    # Taille de la population
    population_size = 50
    # Crée la population initiale
    population = Population(population_size)

    print("Starting Genetic Algorithm for Knight's Tour...")

    while True:
        # 1. Vérifie les déplacements de chaque cavalier
        population.check_population()

        # 2. Évalue la génération et récupère le meilleur cavalier
        maxFit, bestSolution = population.evaluate()

        # Affiche la progression toutes les 50 générations
        if population.generation % 50 == 0:
            print(f"Generation {population.generation}: Best Fitness = {maxFit} / 64")

        # 3. S'arrête si la solution optimale est trouvée
        if maxFit == 64:
            print(f"\nSolution found in generation {population.generation}!")
            break

        # 4. S'arrête si le maximum de générations est atteint
        if population.generation >= MAX_GENERATIONS:
            print(f"\nStopped at generation cap {MAX_GENERATIONS} "
                  f"(best fitness {maxFit}/64).")
            break

        # 5. Génère la génération suivante
        population.create_new_generation()

    # 6. Affiche la solution sur l'interface
    print("Launching interface...")
    draw_solution(bestSolution, population.generation)


if __name__ == "__main__":
    main()
