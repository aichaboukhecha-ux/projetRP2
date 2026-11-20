import tkinter as tk

def draw_solution(best_knight):
    root = tk.Tk()
    root.title("Knight's Tour - Genetic Algorithm")
    
    cell_size = 60
    canvas = tk.Canvas(root, width=8*cell_size, height=8*cell_size)
    canvas.pack()

    # Draw the board
    for i in range(8):
        for j in range(8):
            color = "#a0c865" if (i + j) % 2 == 0 else "#7eb356"
            canvas.create_rectangle(j*cell_size, i*cell_size, (j+1)*cell_size, (i+1)*cell_size, fill=color, outline="white")

    # Draw the path numbers
    for step, (x, y) in enumerate(best_knight.path):
        canvas.create_text(y*cell_size + cell_size/2, x*cell_size + cell_size/2, 
                           text=str(step + 1), font=("Arial", 16, "bold"), fill="#333")

    # Draw the Knight at the final position
    fx, fy = best_knight.path[-1]
    canvas.create_text(fy*cell_size + cell_size/2, fx*cell_size + cell_size/2, 
                       text="♞", font=("Arial", 30), fill="black")

    root.mainloop()