# Knight's Tour — pastel pixel interface

The existing genetic algorithm remains unchanged. `interface.py` displays its
`best_knight.path` as a numbered, animated 8×8 tour over the supplied empty
board artwork.

## Files

```text
projetRP2/
├── chromosome.py
├── knight.py
├── population.py
├── export.py                            # écrit solution.txt et solution.json
├── main.py
├── interface.py
├── Pastel Pink Pixel Chessboard.png       # empty board background
├── Pastel Pink Pixel Chessboard(1).png    # piece sheet; source for the knight sprites
├── knight_black.png                       # extracted runtime sprite
├── knight_white.png                       # extracted alternate sprite
├── fonts/PressStart2P-Regular.ttf
├── tools/extract_knight.py
└── tools/_verif_*.py                      # scripts de vérification du cahier des charges
```

## Install and run

From this folder:

```bash
python -m pip install -r requirements.txt
python tools/extract_knight.py
python main.py
```

`interface.py` automatically runs the extractor if `knight_black.png` is
missing. The extractor can also be pointed at another piece sheet with
`python tools/extract_knight.py --source "Pastel Pink Pixel Chessboard(1).png"`.
All runtime paths are resolved relative to `interface.py`, so `main.py` can be
launched from another working directory.

## Playback controls

- **Space** or **Pause/Resume**: pause or resume playback
- **R** or **Replay**: restart the tour
- **Left / Right** or **◀ / ▶**: step backward or forward
- **+ / −**: change the delay between squares
- **F1**: show or hide grid outlines
- **H** or **HISTO**: show or hide the fitness / generation curve
- **P** or **PATH**: show or hide the list of the 64 moves

The status line reports `Step n / 64`. The screen can be resized; board art and
sprite scaling use nearest-neighbor resampling to preserve crisp pixels.
Coordinates `1–8` are drawn on all four sides of the board, as in Figure 2 of
the assignment.

## Path line

A semi-transparent berry line joins the centre of every visited square in
order, so the knight's route reads at a glance. It is drawn in the tint layer
*before* the numbers, which keeps it blended with the board art and always
under the move numbers. The line grows with playback: at `Step 1` there is
nothing to draw, and it is complete when all 64 squares are reached.

## Generation display

The header also reports **`GEN n`** — the generation in which the genetic
algorithm first produced the displayed 64-square tour. It is passed from
`main.py` (`population.generation`) into `draw_solution(best_knight, generation)`
and rendered next to the title. If no generation is supplied the label falls
back to `GEN —`.

`main.py` stops after `MAX_GENERATIONS = 5000` instead of looping forever, and
the player accepts a partial tour (any non-empty path of at most 64 squares),
so a run that hits the cap still opens and replays its best path.

## Solution path (P / PATH)

Opens **« Chemin de la solution »**: a scrollable, read-only list of every
square visited, in order, with the knight move that was taken from the previous
square (`1 haut-droite` … `8 haut-gauche`). The header shows the generation,
the fitness and the number of squares.

## Generation history (H / HISTO)

Opens **« Historique des générations »**: a curve of the best fitness against
the generation, drawn from the `history` list collected by `main.py`. Axes,
gridlines and ticks (fitness 0–64, generations) are drawn on a Tk canvas, so no
plotting library is required.

Both windows can be open at the same time and are children of the main window.

## Solution export

When a tour is found, `export.py::export_solution()` writes two files next to
`main.py` (both are gitignored, they are regenerated on every run):

| File | Content |
|---|---|
| `solution.txt` | generation, fitness, and the 64 positions listed one per line |
| `solution.json` | `generation`, `fitness`, `cases`, `path` (64 pairs), `history` (generation/fitness per generation) |

## Verification scripts

```bash
PYTHONPATH=. python tools/_verif_spec.py        # 52 checks against the assignment
PYTHONPATH=. python tools/_verif_nouveautes.py  # coordinates, history, export
PYTHONPATH=. python tools/_verif_chemin.py      # solution path window
PYTHONPATH=. python tools/_verif_ligne.py       # path line on the board
```

107 checks in total, all passing.

All comments and docstrings in the source are written in simple French, and
the method signatures match the assignment exactly
(`move_forward(direction)`, `move_backward(direction)`, `mutation()`,
`evaluate_fitness()` looping over `path`, cycle orders as in the PDF example).
