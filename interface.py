import tkinter as tk

class KnightTourUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Knight's Tour - Genetic Algorithm")
        
        # Force the window to pop up in front of other apps (Mac fix)
        self.root.lift()
        self.root.attributes('-topmost', True)
        
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # LEFT SIDE: The Chessboard
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Header showing current gen, current score, and ALL-TIME best
        self.header_label = tk.Label(self.left_frame, text="Starting...", font=("Arial", 12, "bold"), bg="#333", fg="white", pady=5)
        self.header_label.pack(fill=tk.X)
        
        self.cell_size = 55 
        self.canvas = tk.Canvas(self.left_frame, width=8*self.cell_size, height=8*self.cell_size)
        self.canvas.pack()

        # Draw the static chessboard background
        for i in range(8):
            for j in range(8):
                color = "#a0c865" if (i + j) % 2 == 0 else "#7eb356"
                self.canvas.create_rectangle(j*self.cell_size, i*self.cell_size, (j+1)*self.cell_size, (i+1)*self.cell_size, fill=color, outline="white")

        # RIGHT SIDE: The Visual Console Log
        self.right_frame = tk.Frame(self.main_frame, width=200, padx=10, pady=10)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(self.right_frame, text="Generation History:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.log_text = tk.Text(self.right_frame, width=25, font=("Courier", 10), bg="#f4f4f4")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def update_board(self, all_time_best_knight, generation, gen_fit, all_time_best_fit):
        # 1. Update the header with both scores
        self.header_label.config(text=f"Gen: {generation} | This Gen: {gen_fit}/64 | ALL-TIME BEST: {all_time_best_fit}/64")
        
        # 2. Clear only the dynamic parts (numbers and knight), keep the board
        self.canvas.delete("dynamic")
        
        # 3. Draw the ALL-TIME BEST path
        for step, (x, y) in enumerate(all_time_best_knight.path):
            self.canvas.create_text(y*self.cell_size + self.cell_size/2, x*self.cell_size + self.cell_size/2, 
                                    text=str(step + 1), font=("Arial", 11, "bold"), fill="#333", tags="dynamic")

        # 4. Draw the Knight at the end of the all-time best path
        fx, fy = all_time_best_knight.path[-1]
        self.canvas.create_text(fy*self.cell_size + self.cell_size/2, fx*self.cell_size + self.cell_size/2, 
                                text="♞", font=("Arial", 26), fill="black", tags="dynamic")
        
        self.root.update() 

    def log_generation(self, generation, max_fit, is_new_record):
        # Add the score to the right-side visual log
        record_marker = " ⭐ NEW BEST!" if is_new_record else ""
        self.log_text.insert(tk.END, f"Gen {generation}: {max_fit} / 64{record_marker}\n")
        
        # Auto-scroll to the bottom
        self.log_text.see(tk.END)
        self.root.update()