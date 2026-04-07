"""
PopOut Dataset Generator
========================
Gera um dataset de pares (estado, jogada) jogando partidas de self-play com MCTS.
O dataset é guardado em datasets/popout_dataset.csv e pode ser usado para treinar
uma árvore de decisão ID3.

Uso:
    python generate_dataset.py [n_games] [mcts_iterations]

Exemplos:
    python generate_dataset.py          # 100 jogos, 400 iterações
    python generate_dataset.py 200 600  # 200 jogos, 600 iterações

Formato do CSV:
    cell_0_0, cell_0_1, ..., cell_5_6, move
    - cell_r_c ∈ {0, 1, 2}  (0=vazio, 1=própria peça, 2=peça adversária)
    - move ∈ {'drop_0', ..., 'drop_6', 'pop_0', ..., 'pop_6'}
"""

import csv
import math
import sys
import time
import os

from popout_game import PopOutGame, PLAYER1, PLAYER2
from mcts import make_heuristic_mcts, make_standard_mcts


# ──────────────────────────────────────────────────────────────────────────────

OUTPUT_CSV    = os.path.join('datasets', 'popout_dataset.csv')
N_GAMES       = 100
MCTS_ITERS    = 400
FEATURE_NAMES = [f'cell_{r}_{c}' for r in range(6) for c in range(7)]


def generate(n_games: int = N_GAMES,
             mcts_iterations: int = MCTS_ITERS,
             output_csv: str = OUTPUT_CSV) -> int:
    """
    Gera o dataset e devolve o número de amostras gravadas.

    Estratégia: ambos os jogadores usam MCTS heurístico para gerar jogadas
    de maior qualidade do que o random puro.  O estado é codificado da
    perspetiva do jogador atual para tornar o dataset invariante ao jogador.
    """
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    ai = make_heuristic_mcts(iterations=mcts_iterations)
    rows = []

    print(f"A gerar {n_games} jogos com {mcts_iterations} iterações MCTS…")
    t0 = time.time()

    for game_idx in range(n_games):
        game = PopOutGame()

        while not game.game_over:
            if game.is_repetition_draw_available():
                break

            move = ai.get_best_move(game)
            if move is None:
                break

            # Gravar (estado, jogada) ANTES de aplicar o movimento
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

    # Gravar CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(FEATURE_NAMES + ['move'])
        writer.writerows(rows)

    elapsed = time.time() - t0
    print(f"\nDataset gravado em '{output_csv}'")
    print(f"  {len(rows)} amostras  |  {len(set(r[-1] for r in rows))} jogadas únicas  |  {elapsed:.1f}s")
    return len(rows)


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    n_games = int(sys.argv[1]) if len(sys.argv) > 1 else N_GAMES
    iters   = int(sys.argv[2]) if len(sys.argv) > 2 else MCTS_ITERS
    generate(n_games=n_games, mcts_iterations=iters)
