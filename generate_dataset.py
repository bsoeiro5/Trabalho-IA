from __future__ import annotations

import csv
import math
import random
import sys
import time
import os

from popout_game import PopOutGame, PLAYER1, PLAYER2
from mcts import make_heuristic_mcts, make_standard_mcts

OUTPUT_CSV    = os.path.join('datasets', 'popout_dataset.csv')
N_GAMES       = 100
MCTS_ITERS    = 400
VARIANT       = 'heuristic'
FEATURE_NAMES = [f'cell_{r}_{c}' for r in range(6) for c in range(7)]

VARIANTS = {
    'heuristic': make_heuristic_mcts,
    'standard':  make_standard_mcts,
}


def generate(n_games: int = N_GAMES,
             mcts_iterations: int = MCTS_ITERS,
             output_csv: str = OUTPUT_CSV,
             variant: str = VARIANT,
             seed: int | None = 42) -> int:
    if variant not in VARIANTS:
        raise ValueError(f"variant deve ser um de {list(VARIANTS)}; recebi {variant!r}")

    if seed is not None:
        random.seed(seed)

    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    ai = VARIANTS[variant](iterations=mcts_iterations)
    rows = []

    print(f"A gerar {n_games} jogos com {mcts_iterations} iterações MCTS "
          f"({variant}, seed={seed})…")
    t0 = time.time()

    for game_idx in range(n_games):
        game = PopOutGame()

        while not game.game_over:
            if game.is_repetition_draw_available():
                break

            move = ai.get_best_move(game)
            if move is None:
                break

            state_enc  = game.encode_state()
            move_label = f'{move[0]}_{move[1]}'
            rows.append(state_enc + [move_label])

            new_game = game.apply_move(*move)
            if new_game is None:
                break
            game = new_game

        if (game_idx + 1) % 20 == 0 or (game_idx + 1) == n_games:
            elapsed = time.time() - t0
            print(f"  [{game_idx+1:>4}/{n_games}] {len(rows):>6} amostras  "
                  f"({elapsed:.1f}s decorridos)")

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(FEATURE_NAMES + ['move'])
        writer.writerows(rows)

    elapsed = time.time() - t0
    print(f"\nDataset gravado em '{output_csv}'")
    print(f"  {len(rows)} amostras  |  {len(set(r[-1] for r in rows))} jogadas únicas  |  {elapsed:.1f}s")
    return len(rows)

if __name__ == '__main__':
    n_games = int(sys.argv[1]) if len(sys.argv) > 1 else N_GAMES
    iters   = int(sys.argv[2]) if len(sys.argv) > 2 else MCTS_ITERS
    variant = sys.argv[3]      if len(sys.argv) > 3 else VARIANT
    out_csv = sys.argv[4]      if len(sys.argv) > 4 else OUTPUT_CSV
    generate(n_games=n_games, mcts_iterations=iters,
             output_csv=out_csv, variant=variant)