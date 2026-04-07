"""
PopOut – Text-based game runner
================================
Supports three game modes:
  1. Human vs Human   (hvh)
  2. Human vs Computer (hvc)
  3. Computer vs Computer (cvc)

Run with:
    python main.py
"""

import math
import sys
from popout_game import PopOutGame, PLAYER1, PLAYER2
from mcts import (MCTS, make_standard_mcts, make_heuristic_mcts,
                  make_progressive_widening_mcts, make_high_exploration_mcts)


# ──────────────────────────────────────────────────────────────────────────────
# Human input helpers
# ──────────────────────────────────────────────────────────────────────────────

def ask_int(prompt: str, lo: int, hi: int) -> int:
    while True:
        try:
            v = int(input(prompt))
            if lo <= v <= hi:
                return v
            print(f"  Please enter a number between {lo} and {hi}.")
        except ValueError:
            print("  Invalid input. Please enter an integer.")


def get_human_move(game: PopOutGame) -> tuple[str, int]:
    """
    Ask the human player for a move.
    Input format: 'd<col>' for drop or 'p<col>' for pop  (e.g. 'd4', 'p2').
    """
    drop_cols = game.get_drop_moves()
    pop_cols  = game.get_pop_moves()
    player_sym = game.player_symbol(game.current_player)

    print(f"It is {player_sym}'s turn.")
    print(f"  Drop columns available : {[c+1 for c in drop_cols]}")
    print(f"  Pop  columns available : {[c+1 for c in pop_cols]}")
    print("  Enter move as 'd<col>' to drop or 'p<col>' to pop  (e.g. d4 or p2).")

    while True:
        raw = input("  Your move: ").strip().lower()
        if len(raw) >= 2 and raw[0] in ('d', 'p'):
            try:
                col = int(raw[1:]) - 1   # convert to 0-indexed
                move_type = 'drop' if raw[0] == 'd' else 'pop'
                if move_type == 'drop' and col in drop_cols:
                    return move_type, col
                if move_type == 'pop' and col in pop_cols:
                    return move_type, col
            except ValueError:
                pass
        print("  Invalid move. Try again.")


# ──────────────────────────────────────────────────────────────────────────────
# Game loop
# ──────────────────────────────────────────────────────────────────────────────

def play_game(ai1=None, ai2=None, show_board=True) -> int | None:
    """
    Run one complete game.

    ai1 / ai2 : MCTS instances for PLAYER1 / PLAYER2.
                Pass None to use human input for that player.

    Returns: winner (PLAYER1 | PLAYER2) or None for draw.
    """
    game = PopOutGame()
    move_count = 0

    while not game.game_over:
        if show_board:
            game.display()

        # Check repetition-draw availability (simplified: automatic in CvC)
        if game.is_repetition_draw_available():
            if ai1 is None or ai2 is None:
                ans = input("The same position has occurred 3 times. "
                            "Declare draw? (y/n): ").strip().lower()
                if ans == 'y':
                    print("Draw declared by repetition.")
                    return None
            else:
                print("[Auto] Draw declared by repetition rule.")
                return None

        # Whose turn is it?
        current_ai = ai1 if game.current_player == PLAYER1 else ai2

        if current_ai is None:
            # Human
            move_type, col = get_human_move(game)
        else:
            # AI
            sym = game.player_symbol(game.current_player)
            print(f"[{current_ai.name}] ({sym}) is thinking…")
            move = current_ai.get_best_move(game)
            if move is None:
                print("AI has no moves. Game over.")
                break
            move_type, col = move
            print(f"[{current_ai.name}] plays {move_type.upper()} column {col+1}")

        new_game = game.apply_move(move_type, col)
        if new_game is None:
            print("Illegal move — skipping.")
            continue
        game = new_game
        move_count += 1

    if show_board:
        game.display()

    if game.winner:
        sym = game.player_symbol(game.winner)
        print(f"{'='*30}\n{sym} wins after {move_count} moves!\n{'='*30}")
    else:
        print(f"{'='*30}\nDraw after {move_count} moves!\n{'='*30}")

    return game.winner


# ──────────────────────────────────────────────────────────────────────────────
# Main menu
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 40)
    print("         P O P O U T")
    print("  (Connect-4 variant with pop moves)")
    print("=" * 40)
    print("\nGame modes:")
    print("  1 - Human vs Human")
    print("  2 - Human vs Computer")
    print("  3 - Computer vs Computer")
    mode = ask_int("\nSelect mode (1-3): ", 1, 3)

    if mode == 1:
        print("\n[Human vs Human]")
        play_game(ai1=None, ai2=None)

    elif mode == 2:
        print("\nAI algorithms:")
        print("  1 - Standard MCTS-UCT  (1000 iterations)")
        print("  2 - MCTS with heuristic rollout")
        print("  3 - MCTS progressive widening")
        choice = ask_int("Select AI (1-3): ", 1, 3)
        algos = {
            1: make_standard_mcts(1000),
            2: make_heuristic_mcts(1000),
            3: make_progressive_widening_mcts(1000),
        }
        ai = algos[choice]
        side = ask_int("Play as which player? 1=X (first), 2=O (second): ", 1, 2)
        if side == 1:
            play_game(ai1=None, ai2=ai)
        else:
            play_game(ai1=ai, ai2=None)

    else:
        print("\n[Computer vs Computer]")
        print("Algorithm for X (Player 1):")
        print("  1 - Standard MCTS-UCT")
        print("  2 - MCTS Heuristic rollout")
        print("  3 - MCTS High exploration (C=2.5)")
        print("  4 - MCTS Progressive widening")
        c1 = ask_int("  Select (1-4): ", 1, 4)
        print("Algorithm for O (Player 2):")
        c2 = ask_int("  Select (1-4): ", 1, 4)

        def pick(c):
            return {
                1: make_standard_mcts(500),
                2: make_heuristic_mcts(500),
                3: make_high_exploration_mcts(500),
                4: make_progressive_widening_mcts(500),
            }[c]

        play_game(ai1=pick(c1), ai2=pick(c2))


if __name__ == '__main__':
    main()
