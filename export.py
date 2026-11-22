"""Exporte la solution trouvée dans un fichier texte et un fichier JSON."""

import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def export_solution(best_knight, generation, history=None, directory=BASE):
    """Écrit solution.txt et solution.json, puis renvoie leurs chemins."""
    # Chemin du cavalier sous forme de paires (ligne, colonne)
    path = [(int(row), int(col)) for row, col in best_knight.path]
    # Fitness réelle du parcours
    fitness = best_knight.evaluate_fitness()

    # --- Fichier texte lisible ---
    txt = Path(directory) / "solution.txt"
    lignes = [
        "Solution du problème du cavalier",
        "===============================",
        f"Génération : {generation}",
        f"Fitness    : {fitness} / 64",
        f"Cases      : {len(path)}",
        "",
        "Chemin (ligne, colonne) :",
    ]
    for i, (row, col) in enumerate(path, 1):
        lignes.append(f"{i:2d}. ({row}, {col})")
    txt.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    # --- Fichier JSON structuré ---
    js = Path(directory) / "solution.json"
    donnees = {
        "generation": generation,
        "fitness": fitness,
        "cases": len(path),
        "path": [list(position) for position in path],
        "history": [
            {"generation": g, "fitness": f}
            for g, f in (history or [])
        ],
    }
    js.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Solution exportée : {txt.name} et {js.name}")
    return txt, js
