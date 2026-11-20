from population import Population
from interface import draw_solution

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

        # 4. Generate the new population
        population.create_new_generation()

    # 5. Create the user interface to display the solution
    print("Launching interface...")
    draw_solution(bestSolution)

if __name__ == "__main__":
    main()