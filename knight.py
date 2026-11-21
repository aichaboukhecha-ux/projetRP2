import random
from chromosome import Chromosome

class Knight:
    # Direction mapping (dx, dy) where (0,0) is top-left
    DIRECTIONS = {
        1: (-2, 1), 2: (-1, 2), 3: (1, 2), 4: (2, 1),
        5: (2, -1), 6: (1, -2), 7: (-1, -2), 8: (-2, -1)
    }

    def __init__(self, chromosome=None):
        self.chromosome = chromosome if chromosome else Chromosome()
        self.position = (0, 0)
        self.path = [self.position]
        self.fitness = 0

    def move_forward(self, direction, current_pos=None):
        """Calculates the new position based on direction."""
        if current_pos is None:
            current_pos = self.position
        dx, dy = self.DIRECTIONS[direction]
        return (current_pos[0] + dx, current_pos[1] + dy)

    def move_backward(self, direction, current_pos):
        """Reverts the position based on direction."""
        dx, dy = self.DIRECTIONS[direction]
        return (current_pos[0] - dx, current_pos[1] - dy)

    def is_valid(self, pos):
        """Checks if a position is on the board and unvisited."""
        x, y = pos
        if 0 <= x < 8 and 0 <= y < 8:
            if pos not in self.path:
                return True
        return False

    def check_moves(self):
        """Validates and repairs the chromosome, then builds the path."""
        self.path = [(0, 0)]
        self.position = (0, 0)
        
        # Determine cycle direction once for the entire chromosome
        cycle_forward = random.choice([True, False])

        for i in range(63):
            original_move = self.chromosome.genes[i]

            # Try the move, then cancel it with move_backward if it lands
            # off-board or on a square that was already visited.
            trial_position = self.move_forward(original_move)
            if self.is_valid(trial_position):
                self.position = trial_position
                self.path.append(self.position)
                continue

            # Cancel the illegal move: back to the square the knight stood on.
            self.position = self.move_backward(original_move, trial_position)

            # Repair mechanism: cycle through the other directions, starting
            # from the current square. The cycle direction is chosen once for
            # the whole chromosome and stays fixed.
            found_valid = False
            for step in range(1, 8):
                if cycle_forward:
                    new_move = (original_move + step - 1) % 8 + 1
                else:
                    new_move = (original_move - step - 1) % 8 + 1

                candidate = self.move_forward(new_move, self.position)
                if self.is_valid(candidate):
                    # Update the gene (chromosome repair)
                    self.chromosome.genes[i] = new_move
                    self.position = candidate
                    self.path.append(self.position)
                    found_valid = True
                    break

            if not found_valid:
                # No legal move: the gene keeps its original value and the
                # path ends here.
                break

    def evaluate_fitness(self):
        """Fitness is the number of unique squares visited."""
        self.fitness = len(self.path)
        return self.fitness