"""Pastel pixel-art playback window for the Knight's Tour solution."""

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

PALETTE = {
    "light": "#ffd6e8",
    "pink": "#f7a8c9",
    "rose": "#d96ba0",
    "berry": "#a8326e",
    "frame": "#f9c2dc",
}

# Playable area in the supplied image, kept as fractions so the crop is stable
# if the image is resaved at a different resolution.
BOARD_AREA = (197 / 1297, 132 / 1213, 1100 / 1297, 1043 / 1213)
GRID = (0.0, 0.0, 1.0, 1.0)


def _font_file() -> Path:
    return FONT_PATH


def _ensure_knight_sprite() -> None:
    if KNIGHT_PATH.exists():
        return
    # Load the sibling script by absolute path so this fallback also works
    # when the application was launched from a different current directory.
    extractor_path = BASE / "tools" / "extract_knight.py"
    spec = importlib.util.spec_from_file_location("_knight_sprite_extractor", extractor_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load knight sprite extractor: {extractor_path}")
    extractor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extractor)
    extractor.extract(PIECE_SHEET_PATH, BASE)
    if not KNIGHT_PATH.exists():
        raise FileNotFoundError(f"Knight extraction did not create {KNIGHT_PATH}")


class _TourPlayer:
    def __init__(self, root: tk.Tk, path: list[tuple[int, int]],
                 generation: int | None = None) -> None:
        if not (1 <= len(path) <= 64):
            raise ValueError(f"Expected a tour of at most 64 squares, got {len(path)}")
        self.path = [(int(row), int(col)) for row, col in path]
        # Length of the tour actually found, so a partial run still renders.
        self.total = len(self.path)
        self.generation = generation
        if any(not (0 <= row < 8 and 0 <= col < 8) for row, col in self.path):
            raise ValueError("Every path position must be a (row, col) pair from 0 to 7")

        self.root = root
        source_board = Image.open(BOARD_PATH).convert("RGBA")
        left, top, right, bottom = BOARD_AREA
        self.board = source_board.crop((
            round(source_board.width * left),
            round(source_board.height * top),
            round(source_board.width * right),
            round(source_board.height * bottom),
        ))
        self.knight = Image.open(KNIGHT_PATH).convert("RGBA")
        self.step = 0
        self.delay_ms = 220
        self.running = True
        self.grid_visible = False
        self.animation_id: str | None = None
        self.animation_frame_id: str | None = None
        self.frame_photos: list[ImageTk.PhotoImage] = []
        self.board_photo: ImageTk.PhotoImage | None = None
        self.knight_photo: ImageTk.PhotoImage | None = None

        self._build_ui()
        self._load_fonts()
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
        self.root.title("Knight's Tour — Pastel Pixel Edition")
        self.root.configure(bg=PALETTE["frame"])
        self.root.minsize(600, 500)

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        board_h = min(800, int((screen_h - 210) * 0.92))
        board_w = int(board_h * self.board.width / self.board.height)
        scale = min(1.0, screen_w * 0.92 / board_w)
        board_w = int(board_w * scale)
        board_h = int(board_h * scale)
        header = tk.Frame(self.root, bg=PALETTE["berry"], padx=14, pady=10)
        header.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(
            header, text="KNIGHT'S TOUR", bg=PALETTE["berry"], fg=PALETTE["light"],
            font=("TkFixedFont", 14, "bold"),
        ).pack(side="left")
        # The generation that produced the displayed tour, as reported by main().
        gen_text = f"GEN {self.generation}" if self.generation is not None else "GEN —"
        tk.Label(
            header, text=gen_text, bg=PALETTE["berry"], fg=PALETTE["pink"],
            font=("TkFixedFont", 11, "bold"),
        ).pack(side="left", padx=(18, 0))
        self.status = tk.Label(
            header, text=f"STEP 00 / {self.total}", bg=PALETTE["berry"], fg="white",
            font=("TkFixedFont", 11, "bold"),
        )
        self.status.pack(side="right", padx=(12, 0))
        self.progress = tk.Canvas(
            header, width=150, height=14, bg=PALETTE["light"],
            highlightthickness=0, bd=0,
        )
        self.progress.pack(side="right", padx=8)

        self.canvas = tk.Canvas(
            self.root,
            width=board_w,
            height=board_h,
            bg=PALETTE["light"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=12, pady=4)

        controls_border = tk.Frame(self.root, bg=PALETTE["berry"], padx=3, pady=3)
        controls_border.pack(fill="x", padx=12, pady=(4, 0))
        controls = tk.Frame(controls_border, bg=PALETTE["frame"], padx=8, pady=7)
        controls.pack(fill="x")
        self.speed_label = tk.Label(
            controls, text="SPEED 220 ms", bg=PALETTE["frame"], fg=PALETTE["berry"],
            font=("TkFixedFont", 9, "bold"),
        )

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

        tk.Label(
            self.root, text="SPACE pause  ·  ← / → step  ·  R replay  ·  + / − speed  ·  F1 grid",
            bg=PALETTE["frame"], fg=PALETTE["berry"], font=("TkFixedFont", 8),
        ).pack(pady=(7, 10))

    def _load_fonts(self) -> None:
        # Tk itself cannot load a font file portably; Pillow renders the bundled
        # pixel font into the board image, with a bitmap-friendly built-in fallback.
        self.pixel_font_path = _font_file() if _font_file().is_file() else None

    def _on_resize(self, _event: tk.Event) -> None:
        self._render()

    def _cell_pixel_font(self, cell_w: int, cell_h: int) -> ImageFont.ImageFont:
        size = max(12, min(32, int(cell_h * 0.24)))
        if self.pixel_font_path:
            try:
                return ImageFont.truetype(str(self.pixel_font_path), size=size)
            except OSError:
                pass
        return ImageFont.load_default()

    def _compose_board(self, width: int, height: int) -> tuple[Image.Image, tuple[int, int, int, int]]:
        scaled = self.board.resize((width, height), Image.Resampling.NEAREST)
        grid_x0, grid_y0, grid_x1, grid_y1 = GRID
        x0, x1 = round(width * grid_x0), round(width * grid_x1)
        y0, y1 = round(height * grid_y0), round(height * grid_y1)
        cell_w = (x1 - x0) / 8
        cell_h = (y1 - y0) / 8

        tint = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        tint_draw = ImageDraw.Draw(tint)
        for index, (row, col) in enumerate(self.path[:self.step]):
            alpha = 118 if index == self.step - 1 else 68
            color = (217, 107, 160, alpha) if index == self.step - 1 else (247, 168, 201, alpha)
            left = round(x0 + col * cell_w)
            top = round(y0 + row * cell_h)
            right = round(x0 + (col + 1) * cell_w)
            bottom = round(y0 + (row + 1) * cell_h)
            tint_draw.rectangle((left, top, right - 1, bottom - 1), fill=color)
        scaled = Image.alpha_composite(scaled, tint)

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
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())
        scale = min(canvas_w / self.board.width, canvas_h / self.board.height)
        width = max(1, int(self.board.width * scale))
        height = max(1, int(self.board.height * scale))
        offset_x = (canvas_w - width) // 2
        offset_y = (canvas_h - height) // 2
        composed, (x0, y0, x1, y1) = self._compose_board(width, height)
        self.board_photo = ImageTk.PhotoImage(composed, master=self.root)
        self.frame_photos = [self.board_photo]

        self.canvas.delete("all")
        self.canvas.create_image(offset_x, offset_y, image=self.board_photo, anchor="nw")
        cell_w = (x1 - x0) / 8
        cell_h = (y1 - y0) / 8

        if self.grid_visible:
            for i in range(9):
                xx = offset_x + x0 + round(i * cell_w)
                yy = offset_y + y0 + round(i * cell_h)
                self.canvas.create_line(xx, offset_y + y0, xx, offset_y + y1,
                                        fill=PALETTE["berry"], width=2)
                self.canvas.create_line(offset_x + x0, yy, offset_x + x1, yy,
                                        fill=PALETTE["berry"], width=2)

        if self.step:
            if knight_position is None:
                row, col = self.path[self.step - 1]
                row_f, col_f = float(row), float(col)
            else:
                row_f, col_f = knight_position
            max_w, max_h = int(cell_w * 0.78), int(cell_h * 0.78)
            sprite = self.knight.copy()
            sprite.thumbnail((max_w, max_h), Image.Resampling.NEAREST)
            self.knight_photo = ImageTk.PhotoImage(sprite, master=self.root)
            self.frame_photos.append(self.knight_photo)
            center_x = offset_x + x0 + (col_f + 0.5) * cell_w
            center_y = offset_y + y0 + (row_f + 0.5) * cell_h
            self.canvas.create_image(center_x, center_y, image=self.knight_photo, anchor="center")
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
        if self.running and self.step < self.total and self.animation_id is None:
            self.animation_id = self.root.after(self.delay_ms, self._advance)

    def _advance(self) -> None:
        self.animation_id = None
        if not self.running or self.step >= self.total:
            return
        previous = self.path[self.step - 1] if self.step else self.path[0]
        self.step += 1
        current = self.path[self.step - 1]
        # Reveal the numbered square immediately and animate the sprite over 9 frames.
        self._render(knight_position=(float(previous[0]), float(previous[1])))
        start = previous
        end = current
        if self.step == 1:
            start = end
        frame_count = 9
        def animate(frame: int = 1) -> None:
            if frame > frame_count:
                self.animation_frame_id = None
                self._render()
                if self.step >= self.total:
                    self.running = False
                    self._render()
                else:
                    self._schedule_next()
                return
            t = frame / frame_count
            self._render((start[0] + (end[0] - start[0]) * t,
                          start[1] + (end[1] - start[1]) * t))
            self.animation_frame_id = self.root.after(14, animate, frame + 1)
        animate()

    def _cancel_callbacks(self) -> None:
        for callback in (self.animation_id, self.animation_frame_id):
            if callback is not None:
                try:
                    self.root.after_cancel(callback)
                except tk.TclError:
                    pass
        self.animation_id = None
        self.animation_frame_id = None

    def toggle_pause(self, _event: tk.Event | None = None) -> str:
        self.running = not self.running
        if self.running:
            self._schedule_next()
        else:
            self._cancel_callbacks()
        self._render()
        return "break"

    def replay(self, _event: tk.Event | None = None) -> str:
        self._cancel_callbacks()
        self.step = 0
        self.running = True
        self._render()
        self._schedule_next()
        return "break"

    def step_backward(self, _event: tk.Event | None = None) -> str:
        self._cancel_callbacks()
        self.running = False
        self.step = max(0, self.step - 1)
        self._render()
        return "break"

    def step_forward(self, _event: tk.Event | None = None) -> str:
        self._cancel_callbacks()
        self.running = False
        self.step = min(self.total, self.step + 1)
        self._render()
        return "break"

    def speed_up(self, _event: tk.Event | None = None) -> str:
        self.delay_ms = max(40, self.delay_ms - 40)
        self._render()
        return "break"

    def slow_down(self, _event: tk.Event | None = None) -> str:
        self.delay_ms = min(1200, self.delay_ms + 40)
        self._render()
        return "break"

    def toggle_grid(self, _event: tk.Event | None = None) -> str:
        self.grid_visible = not self.grid_visible
        self._render()
        return "break"

    def close(self) -> None:
        self._cancel_callbacks()
        self.root.destroy()


def draw_solution(best_knight, generation: int | None = None) -> None:
    """Display and animate ``best_knight.path`` in a resizable Tk window.

    ``generation`` is the generation that produced the tour; it is shown in
    the window header so the viewer can see how long the GA took.
    """
    if not BOARD_PATH.is_file():
        raise FileNotFoundError(f"Board background not found: {BOARD_PATH}")
    _ensure_knight_sprite()
    root = tk.Tk()
    _TourPlayer(root, best_knight.path, generation)
    root.mainloop()
