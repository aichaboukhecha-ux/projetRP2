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
├── main.py
├── interface.py
├── Pastel Pink Pixel Chessboard.png       # empty board background
├── Pastel Pink Pixel Chessboard(1).png    # piece sheet; source for the knight sprites
├── knight_black.png                       # extracted runtime sprite
├── knight_white.png                       # extracted alternate sprite
├── fonts/PressStart2P-Regular.ttf
└── tools/extract_knight.py
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

The status line reports `Step n / 64`. The screen can be resized; board art and
sprite scaling use nearest-neighbor resampling to preserve crisp pixels.

## Generation display

The header also reports **`GEN n`** — the generation in which the genetic
algorithm first produced the displayed 64-square tour. It is passed from
`main.py` (`population.generation`) into `draw_solution(best_knight, generation)`
and rendered next to the title. If no generation is supplied the label falls
back to `GEN —`.

`main.py` stops after `MAX_GENERATIONS = 5000` instead of looping forever, and
the player accepts a partial tour (any non-empty path of at most 64 squares),
so a run that hits the cap still opens and replays its best path.
