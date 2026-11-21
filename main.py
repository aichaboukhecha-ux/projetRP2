from population import Population
from interface import KnightTourUI
import time

def main():
    population_size = 50
    population = Population(population_size)
    
    ui = KnightTourUI()
    
    MAX_GENERATIONS = 1000 
    
    # --- HALL OF FAME TRACKING ---
    all_time_best_fit = -1
    all_time_best_knight = None
    
    while population.generation <= MAX_GENERATIONS:
        population.check_population()
        
        # Get the best knight OF THIS SPECIFIC GENERATION
        gen_best_fit, gen_best_knight = population.evaluate()
        
        # Check if this generation produced a new all-time champion
        is_new_record = False
        if gen_best_fit > all_time_best_fit:
            all_time_best_fit = gen_best_fit
            all_time_best_knight = gen_best_knight
            is_new_record = True
        
        # 1. Update the board with the ALL-TIME BEST knight (not just this generation's)
        ui.update_board(all_time_best_knight, population.generation, gen_best_fit, all_time_best_fit)
        
        # 2. Log this generation's score (with a ⭐ marker if it's a new record)
        ui.log_generation(population.generation, gen_best_fit, is_new_record)
        
        time.sleep(0.02) 
        
        if all_time_best_fit == 64:
            ui.header_label.config(text=f"SUCCESS! Perfect Solution Found in Generation {population.generation}!", bg="green")
            break
            
        population.create_new_generation()

    ui.root.mainloop()

if __name__ == "__main__":
    main()