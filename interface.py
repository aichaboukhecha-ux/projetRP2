"""Fenêtre d'animation de la solution du problème du cavalier."""

from __future__ import annotations

import importlib.util
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageTk


BASE = Path(__file__).resolve().parent
BOARD_PATH = BASE / "Pastel Pink Pixel Chessboard.png"
PIECE_SHEET_PATH = BASE / "Pastel Pink Pixel Chessboard(1).png"
KNIGHT_PATH = BASE / "knight_black.png"
FONT_PATH = BASE / "fonts" / "PressStart2P-Regular.ttf"

# Couleurs pastel de l'interface
PALETTE = {
    "light": "#ffd6e8",
    "pink": "#f7a8c9",
    "rose": "#d96ba0",
    "berry": "#a8326e",
    "frame": "#f9c2dc",
}

# Zone jouable de l'image, exprimée en fractions
BOARD_AREA = (197 / 1297, 132 / 1213, 1100 / 1297, 1043 / 1213)
GRID = (0.0, 0.0, 1.0, 1.0)


def _font_file() -> Path:
    return FONT_PATH


def _ensure_knight_sprite() -> None:
    # Si le sprite du cavalier existe déjà, on n'a rien à faire
    if KNIGHT_PATH.exists():
        return
    # Sinon on charge le script d'extraction par chemin absolu
    extractor_path = BASE / "tools" / "extract_knight.py"
    spec = importlib.util.spec_from_file_location("_knight_sprite_extractor", extractor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load knight sprite extractor: {extractor_path}")
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    # Extrait le cavalier depuis la planche d'images
    extractor.extract(PIECE_SHEET_PATH, BASE)
    if not KNIGHT_PATH.exists():
        raise FileNotFoundError(f"Knight extraction did not create {KNIGHT_PATH}")


class _TourPlayer:
    def __init__(self, root: tk.Tk, path: list[tuple[int, int]],
                 generation: int | None = None) -> None:
        # Le parcours doit contenir entre 1 et 64 cases
        if not (1 <= len(path) <= 64):
            raise ValueError(f"Expected a tour of at most 64 squares, got {len(path)}")
        self.path = [(int(row), int(col)) for row, col in path]
        # Nombre de cases du parcours affiché
        self.total = len(self.path)
        # Génération qui a produit ce parcours
        self.generation = generation
        # Chaque case doit être sur l'échiquier
        if any(not (0 <= row < 8 and 0 <= col < 8) for row, col in self.path):
            raise ValueError("Every path position must be a (row, col) pair from 0 to 7")

        self.root = root
        # Charge l'image du plateau et découpe la zone jouable
        source_board = Image.open(BOARD_PATH).convert("RGBA")
        left, top, right, bottom = BOARD_AREA
        self.board = source_board.crop((
            round(source_board.width * left),
            round(source_board.height * top),
            round(source_board.width * right),
            round(source_board.height * bottom),
        ))
        # Sprite du cavalier
        self.knight = Image.open(KNIGHT_PATH).convert("RGBA")
        # Case affichée actuellement (0 = rien d'affiché)
        self.step = 0
        # Délai entre deux cases en millisecondes
        self.delay_ms = 220
        # Lecture en cours ou en pause
        self.running = True
        # Grille affichée ou non
        self.grid_visible = False
        # Identifiants des animations planifiées
        self.animation_id: str | None = None
        self.animation_frame_id: str | None = None
        # Sert à garder les images en mémoire
        self.frame_photos: list[ImageTk.PhotoImage] = []
        self.board_photo: ImageTk.PhotoImage | None = None
        self.knight_photo: ImageTk.PhotoImage | None = None

        # Construit les widgets puis lance la lecture
        self._build_ui()
        self._load_fonts()
        # Raccourcis clavier
        self.root.bind("<space>", self.toggle_pause)
        self.root.bind("<KeyPress-r>", self.replay)
        self.root.bind("<KeyPress-R>", self.replay)
        self.root.bind("<Left>", self.step_backward)
        self.root.bind("<Right>", self.step_forward)
        self.root.bind("<F1>", self.toggle_grid)
        self.root.bind("<plus>", self.speed_up)
        self.root.bind("<equal>", self.speed_up)
        self.root.bind("<KP_Add>", self.speed_up)
        self.root.bind("<minus>", self.slow_down)
        self.root.bind("<KP_Subtract>", self.slow_down)
        self.canvas.bind("<Configure>", self._on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._render()
        self._schedule_next()

    def _build_ui(self) -> None:
        # Fenêtre principale
        self.root.title("Knight's Tour — Pastel Pixel Edition")
        self.root.configure(bg=PALETTE["frame"])
        self.root.minsize(600, 500)

        # Dimensionne le plateau selon l'écran
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        board_h = min(800, int((screen_h - 210) * 0.92))
        board_w = int(board_h * self.board.width / self.board.height)
        scale = min(1.0, screen_w * 0.92 / board_w)
        board_w = int(board_w * scale)
        board_h = int(board_h * scale)

        # Barre du haut : titre, génération, étape et progression
        header = tk.Frame(self.root, bg=PALETTE["berry"], padx=14, pady=10)
        header.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(
            header, text="KNIGHT'S TOUR", bg=PALETTE["berry"], fg=PALETTE["light"],
            font=("TkFixedFont", 14, "bold"),
        ).pack(side="left")
        # Affiche la génération qui a donné la solution
        gen_text = f"GEN {self.generation}" if self.generation is not None else "GEN —"
        tk.Label(
            header, text=gen_text, bg=PALETTE["berry"], fg=PALETTE["pink"],
            font=("TkFixedFont", 11, "bold"),
        ).pack(side="left", padx=(18, 0))
        # Affiche l'étape en cours
        self.status = tk.Label(
            header, text=f"STEP 00 / {self.total}", bg=PALETTE["berry"], fg="white",
            font=("TkFixedFont", 11, "bold"),
        )
        self.status.pack(side="right", padx=(12, 0))
        # Barre de progression
        self.progress = tk.Canvas(
            header, width=150, height=14, bg=PALETTE["light"],
            highlightthickness=0, bd=0,
        )
        self.progress.pack(side="right", padx=8)

        # Zone d'affichage du plateau
        self.canvas = tk.Canvas(
            self.root,
            width=board_w,
            height=board_h,
            bg=PALETTE["light"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=4)

        # Boutons de commande
        controls_border = tk.Frame(self.root, bg=PALETTE["berry"], padx=3, pady=3)
        controls_border.pack(fill="x", padx=12, pady=(4, 0))
        controls = tk.Frame(controls_border, bg=PALETTE["frame"], padx=8, pady=7)
        controls.pack(fill="x")
        self.speed_label = tk.Label(
            controls, text="SPEED 220 ms", bg=PALETTE["frame"], fg=PALETTE["berry"],
            font=("TkFixedFont", 9, "bold"),
        )

        # Crée un bouton pour chaque commande
        self.buttons: dict[str, tk.Button] = {}
        for label, key, command in (
            ("◀ BACK", "back", self.step_backward),
            ("NEXT ▶", "next", self.step_forward),
            ("PAUSE", "pause", self.toggle_pause),
            ("REPLAY", "replay", self.replay),
            ("−", "slower", self.slow_down),
            ("+", "faster", self.speed_up),
        ):
            button = tk.Button(
                controls, text=label, command=command,
                bg=PALETTE["pink"], fg=PALETTE["berry"], activebackground=PALETTE["rose"],
                activeforeground="white", relief="raised", bd=4, padx=10, pady=7,
                font=("TkFixedFont", 9, "bold"), cursor="hand2",
            )
            button.pack(side="left", padx=3)
            self.buttons[key] = button
        self.speed_label.pack(side="right", padx=8)

        # Rappel des raccourcis clavier
        tk.Label(
            self.root, text="SPACE pause  ·  ← / → step  ·  R replay  ·  + / − speed  ·  F1 grid",
            bg=PALETTE["frame"], fg=PALETTE["berry"], font=("TkFixedFont", 8),
        ).pack(pady=(7, 10))

    def _load_fonts(self) -> None:
        # Retourne le fichier de police s'il existe, sinon None
        self.pixel_font_path = _font_file() if _font_file().is_file() else None

    def _on_resize(self, _event: tk.Event) -> None:
        # Redessine le plateau à la nouvelle taille
        self._render()

    def _cell_pixel_font(self, cell_w: int, cell_h: int) -> ImageFont.ImageFont:
        # Taille du texte proportionnelle à la case
        size = max(12, min(32, int(cell_h * 0.24)))
        if self.pixel_font_path:
            try:
                return ImageFont.truetype(str(self.pixel_font_path), size=size)
            except OSError:
                pass
        # Police de repli si le fichier est illisible
        return ImageFont.load_default()

    def _compose_board(self, width: int, height: int) -> tuple[Image.Image, tuple[int, int, int, int]]:
        # Agrandit le plateau à la taille demandée
        scaled = self.board.resize((width, height), Image.Resampling.NEAREST)
        # Zone de la grille en pixels
        grid_x0, grid_y0, grid_x1, grid_y1 = GRID
        x0, x1 = round(width * grid_x0), round(width * grid_x1)
        y0, y1 = round(height * grid_y0), round(height * grid_y1)
        # Taille d'une case
        cell_w = (x1 - x0) / 8
        cell_h = (y1 - y0) / 8

        # Colorie les cases déjà visitées
        tint = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        tint_draw = ImageDraw.Draw(tint)
        for index, (row, col) in enumerate(self.path[:self.step]):
            # La dernière case visitée est plus foncée
            alpha = 118 if index == self.step - 1 else 68
            color = (217, 107, 160, alpha) if index == self.step - 1 else (247, 168, 201, alpha)
            left = round(x0 + col * cell_w)
            top = round(y0 + row * cell_h)
            right = round(x0 + (col + 1) * cell_w)
            bottom = round(y0 + (row + 1) * cell_h)
            tint_draw.rectangle((left, top, right - 1, bottom - 1), fill=color)
        scaled = Image.alpha_composite(scaled, tint)

        # Dessine le numéro de chaque case visitée
        if self.step:
            draw = ImageDraw.Draw(scaled)
            font = self._cell_pixel_font(max(1, round(cell_w)), max(1, round(cell_h)))
            for index, (row, col) in enumerate(self.path[:self.step]):
                number = str(index + 1)
                px = round(x0 + col * cell_w + cell_w * 0.08)
                py = round(y0 + row * cell_h + cell_h * 0.07)
                draw.text(
                    (px, py), number, font=font, fill=PALETTE["berry"],
                    stroke_width=max(1, round(height * 0.0015)), stroke_fill=PALETTE["light"],
                )
        return scaled, (x0, y0, x1, y1)

    def _render(self, knight_position: tuple[float, float] | None = None) -> None:
        # Ne fait rien si la fenêtre est fermée
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        # Taille de la zone d'affichage
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        # Ajuste le plateau pour qu'il reste entier
        scale = min(canvas_w / self.board.width, canvas_h / self.board.height)
        width = max(1, int(self.board.width * scale))
        height = max(1, int(self.board.height * scale))
        # Centre le plateau dans la fenêtre
        offset_x = (canvas_w - width) // 2
        offset_y = (canvas_h - height) // 2
        composed, (x0, y0, x1, y1) = self._compose_board(width, height)
        self.board_photo = ImageTk.PhotoImage(composed, master=self.root)
        # Garde une référence pour éviter la suppression par Python
        self.frame_photos = [self.board_photo]

        # Redessine la fenêtre
        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, image=self.board_photo, anchor="nw")
        cell_w = (x1 - x0) / 8
        cell_h = (y1 - y0) / 8

        # Dessine la grille si elle est active
        if self.grid_visible:
            for i in range(9):
                xx = offset_x + x0 + round(i * cell_w)
                yy = offset_y + y0 + round(i * cell_h)
                self.canvas.create_line(xx, offset_y + y0, xx, offset_y + y1,
                                        fill=PALETTE["berry"], width=2)
                self.canvas.create_line(offset_x + x0, yy, offset_x + x1, yy,
                                        fill=PALETTE["berry"], width=2)

        # Dessine le cavalier sur sa case
        if self.step:
            if knight_position is None:
                row, col = self.path[self.step - 1]
                row_f, col_f = float(row), float(col)
            else:
                row_f, col_f = knight_position
            # Réduit le sprite pour qu'il tienne dans la case
            max_w, max_h = int(cell_w * 0.78), int(cell_h * 0.78)
            sprite = self.knight.copy()
            sprite.thumbnail((max_w, max_h), Image.Resampling.NEAREST)
            self.knight_photo = ImageTk.PhotoImage(sprite, master=self.root)
            self.frame_photos.append(self.knight_photo)
            # Centre le cavalier sur la case
            center_x = offset_x + x0 + (col_f + 0.5) * cell_w
            center_y = offset_y + y0 + (row_f + 0.5) * cell_h
            self.canvas.create_image(center_x, center_y, image=self.knight_photo, anchor="center")

        # Met à jour l'étape, la progression et la vitesse
        self.status.configure(text=f"STEP {self.step:02d} / {self.total}")
        self.progress.delete("all")
        progress_w = max(1, self.progress.winfo_width())
        progress_h = max(1, self.progress.winfo_height())
        self.progress.create_rectangle(
            0, 0, round(progress_w * self.step / self.total), progress_h,
            fill=PALETTE["rose"], outline="",
        )
        self.speed_label.configure(text=f"SPEED {self.delay_ms} ms")
        self.buttons["pause"].configure(text="RESUME" if not self.running else "PAUSE")

    def _schedule_next(self) -> None:
        # Planifie la case suivante si la lecture est en cours
        if self.running and self.step < self.total and self.animation_id is None:
            self.animation_id = self.root.after(self.delay_ms, self._advance)

    def _advance(self) -> None:
        self.animation_id = None
        # S'arrête si la lecture est en pause ou si le parcours est fini
        if not self.running or self.step >= self.total:
            return
        # Case précédente et case à atteindre
        previous = self.path[self.step - 1] if self.step else self.path[0]
        self.step += 1
        current = self.path[self.step - 1]
        # Affiche tout de suite la case numérotée
        self._render(knight_position=(float(previous[0]), float(previous[1])))
        start = previous
        end = current
        # À la première étape, le cavalier est déjà sur sa case
        if self.step == 1:
            start = end
        # Anime le cavalier sur 9 images
        frame_count = 9
        def animate(frame: int = 1) -> None:
            if frame > frame_count:
                self.animation_frame_id = None
                self._render()
                # Fin du parcours : la lecture s'arrête toute seule
                if self.step >= self.total:
                    self.running = False
                    self._render()
                else:
                    self._schedule_next()
                return
            # Position intermédiaire entre les deux cases
            t = frame / frame_count
            self._render((start[0] + (end[0] - start[0]) * t,
                          start[1] + (end[1] - start[1]) * t))
            self.animation_frame_id = self.root.after(14, animate, frame + 1)
        animate()

    def _cancel_callbacks(self) -> None:
        # Annule les animations en attente
        for callback in (self.animation_id, self.animation_frame_id):
            if callback is not None:
                try:
                    self.root.after_cancel(callback)
                except tk.TclError:
                    pass
        self.animation_id = None
        self.animation_frame_id = None

    def toggle_pause(self, _event: tk.Event | None = None) -> str:
        # Bascule entre lecture et pause
        self.running = not self.running
        if self.running:
            self._schedule_next()
        else:
            self._cancel_callbacks()
        self._render()
        return "break"

    def replay(self, _event: tk.Event | None = None) -> str:
        # Recommence le parcours depuis le début
        self._cancel_callbacks()
        self.step = 0
        self.running = True
        self._render()
        self._schedule_next()
        return "break"

    def step_backward(self, _event: tk.Event | None = None) -> str:
        # Revient à la case précédente
        self._cancel_callbacks()
        self.running = False
        self.step = max(0, self.step - 1)
        self._render()
        return "break"

    def step_forward(self, _event: tk.Event | None = None) -> str:
        # Avance à la case suivante
        self._cancel_callbacks()
        self.running = False
        self.step = min(self.total, self.step + 1)
        self._render()
        return "break"

    def speed_up(self, _event: tk.Event | None = None) -> str:
        # Accélère la lecture (40 ms minimum)
        self.delay_ms = max(40, self.delay_ms - 40)
        self._render()
        return "break"

    def slow_down(self, _event: tk.Event | None = None) -> str:
        # Ralentit la lecture (1200 ms maximum)
        self.delay_ms = min(1200, self.delay_ms + 40)
        self._render()
        return "break"

    def toggle_grid(self, _event: tk.Event | None = None) -> str:
        # Affiche ou masque la grille
        self.grid_visible = not self.grid_visible
        self._render()
        return "break"

    def close(self) -> None:
        # Ferme la fenêtre
        self._cancel_callbacks()
        self.root.destroy()


def draw_solution(best_knight, generation: int | None = None) -> None:
    """Affiche et anime le parcours du meilleur cavalier.

    `generation` est la génération qui a produit le parcours.
    """
    # Vérifie que l'image du plateau existe
    if not BOARD_PATH.is_file():
        raise FileNotFoundError(f"Board background not found: {BOARD_PATH}")
    # Prépare le sprite du cavalier si besoin
    _ensure_knight_sprite()
    # Crée la fenêtre et lance l'animation
    root = tk.Tk()
    _TourPlayer(root, best_knight.path, generation)
    root.mainloop()
