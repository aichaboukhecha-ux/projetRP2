from population import Population
from interface import draw_solution

# Safety net: a full tour normally appears within a few hundred generations,
# but the cap guarantees the program always terminates if the GA stalls.
MAX_GENERATIONS = 5000


def main():
    population_size = 50
    population = Population(population_size)

    print("Starting Genetic Algorithm for Knight's Tour...")

    while True:
        # 1. Check the validity of the current population
        population.check_population()

        # 2. Evaluate the current generation and get the best knight
        maxFit, bestSolution = population.evaluate()

        # Optional: Print progress every 50 generations
        if population.generation % 50 == 0:
            print(f"Generation {population.generation}: Best Fitness = {maxFit} / 64")

        # 3. Break if optimal solution is found
        if maxFit == 64:
            print(f"\nSolution found in generation {population.generation}!")
            break

        # 4. Break if the generation cap is reached (never loop forever)
        if population.generation >= MAX_GENERATIONS:
            print(f"\nStopped at generation cap {MAX_GENERATIONS} "
                  f"(best fitness {maxFit}/64).")
            break

        # 5. Generate the new population
        population.create_new_generation()

    # 6. Create the user interface to display the solution
    print("Launching interface...")
    draw_solution(bestSolution, population.generation)


if __name__ == "__main__":
    main()
