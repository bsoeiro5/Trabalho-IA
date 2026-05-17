from __future__ import annotations

EMPTY   = 0
PLAYER1 = 1   # represented as 'X'
PLAYER2 = 2   # represented as 'O'

DEFAULT_ROWS = 6
DEFAULT_COLS = 7


class PopOutGame:
    """
    Immutable-style game state for PopOut.

    All moves are applied via `apply_move`, which returns a NEW game state and
    leaves the original unchanged. This makes it easy to use in MCTS.
    """

    EMPTY   = EMPTY
    PLAYER1 = PLAYER1
    PLAYER2 = PLAYER2

    # ─── Construction ──────────────────────────────────────────────────────────

    def __init__(self, rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS):
        self.rows = rows
        self.cols = cols
        # board[r][c] = EMPTY | PLAYER1 | PLAYER2
        self.board: list[list[int]] = [[EMPTY] * cols for _ in range(rows)]
        self.current_player: int = PLAYER1
        # Maps frozenboard → count; used for repetition rule
        self.state_history: dict = {}
        self.winner: int | None = None
        self.game_over: bool = False
        self._record_state()

    # ─── State tracking ────────────────────────────────────────────────────────

    def _get_state_key(self) -> tuple:
        return (tuple(tuple(row) for row in self.board), self.current_player)

    def _record_state(self) -> None:
        key = self._get_state_key()
        self.state_history[key] = self.state_history.get(key, 0) + 1

    def get_state_repetitions(self) -> int:
        """How many times the current configuration (board + whose turn) has occurred."""
        return self.state_history.get(self._get_state_key(), 0)

    def is_repetition_draw_available(self) -> bool:
        """Returns True if either player may invoke the repetition-draw rule."""
        return self.get_state_repetitions() >= 3

    # ─── Board queries ─────────────────────────────────────────────────────────

    def is_board_full(self) -> bool:
        """True if every cell in the top row is occupied (no drop possible)."""
        return all(self.board[0][c] != EMPTY for c in range(self.cols))

    def get_drop_moves(self) -> list[int]:
        """Columns where a disc can be dropped (top-row cell is empty)."""
        return [c for c in range(self.cols) if self.board[0][c] == EMPTY]

    def get_pop_moves(self) -> list[int]:
        """Columns where the current player has their own disc on the bottom row."""
        return [c for c in range(self.cols)
                if self.board[self.rows - 1][c] == self.current_player]

    def get_all_moves(self) -> list[tuple[str, int]]:
        """All legal moves as (move_type, column) tuples."""
        if self.game_over:
            return []
        moves = [('drop', c) for c in self.get_drop_moves()]
        moves += [('pop',  c) for c in self.get_pop_moves()]
        return moves

    # ─── Move application ──────────────────────────────────────────────────────

    def apply_move(self, move_type: str, col: int) -> 'PopOutGame | None':
        """
        Apply a move and return a NEW game state.
        Returns None if the move is illegal.
        The current object is never modified.
        """
        if self.game_over:
            return None

        new = self._copy()

        if move_type == 'drop':
            if new.board[0][col] != EMPTY:
                return None                          # Column full
            # Find lowest empty row (gravity)
            row = self.rows - 1
            while row >= 0 and new.board[row][col] != EMPTY:
                row -= 1
            if row < 0:
                return None
            new.board[row][col] = self.current_player
            new._resolve_after_drop()

        elif move_type == 'pop':
            if new.board[self.rows - 1][col] != self.current_player:
                return None                          # No own disc at bottom
            # Remove bottom disc and shift column down
            for r in range(self.rows - 1, 0, -1):
                new.board[r][col] = new.board[r - 1][col]
            new.board[0][col] = EMPTY
            new._resolve_after_pop()

        else:
            return None

        return new

    # ─── Internal resolution helpers ───────────────────────────────────────────

    def _resolve_after_drop(self) -> None:
        p1 = self._check_four_in_row(PLAYER1)
        p2 = self._check_four_in_row(PLAYER2)
        if p1 or p2:
            # For a drop move, simultaneous 4-in-a-row is theoretically possible
            # only if the dropping player completes both—give the win to the dropper.
            if p1 and p2:
                self.winner = self.current_player
            elif p1:
                self.winner = PLAYER1
            else:
                self.winner = PLAYER2
            self.game_over = True
            # Switch current_player so it represents "who would move next".
            # This ensures MCTS stores statistics from the opponent's perspective,
            # making (1 − child.wins/child.visits) correctly reflect the parent's
            # win-rate. Without this, winning moves appear bad to the selector.
            self.current_player = PLAYER2 if self.current_player == PLAYER1 else PLAYER1
        else:
            self._switch_player()

    def _resolve_after_pop(self) -> None:
        p1 = self._check_four_in_row(PLAYER1)
        p2 = self._check_four_in_row(PLAYER2)
        if p1 or p2:
            # Special rule 1: if the pop creates 4-in-a-row for BOTH players
            # simultaneously, the player who popped wins (the opponent's line
            # is ignored). If only one player has a 4-in-a-row, that player
            # wins — even if it is the opponent (a pop can complete the
            # opponent's line by dropping discs down).
            if p1 and p2:
                self.winner = self.current_player
            elif p1:
                self.winner = PLAYER1
            else:
                self.winner = PLAYER2
            self.game_over = True
            self.current_player = PLAYER2 if self.current_player == PLAYER1 else PLAYER1
        else:
            self._switch_player()

    def _switch_player(self) -> None:
        self.current_player = PLAYER2 if self.current_player == PLAYER1 else PLAYER1
        self._record_state()

    # ─── Win detection ─────────────────────────────────────────────────────────

    def _check_four_in_row(self, player: int) -> bool:
        """Return True if `player` has at least four consecutive discs."""
        b = self.board
        R, C = self.rows, self.cols

        # Horizontal
        for r in range(R):
            for c in range(C - 3):
                if b[r][c] == b[r][c+1] == b[r][c+2] == b[r][c+3] == player:
                    return True
        # Vertical
        for r in range(R - 3):
            for c in range(C):
                if b[r][c] == b[r+1][c] == b[r+2][c] == b[r+3][c] == player:
                    return True
        # Diagonal ↘
        for r in range(R - 3):
            for c in range(C - 3):
                if b[r][c] == b[r+1][c+1] == b[r+2][c+2] == b[r+3][c+3] == player:
                    return True
        # Diagonal ↙
        for r in range(R - 3):
            for c in range(3, C):
                if b[r][c] == b[r+1][c-1] == b[r+2][c-2] == b[r+3][c-3] == player:
                    return True
        return False

    # ─── Copy ──────────────────────────────────────────────────────────────────

    def _copy(self) -> 'PopOutGame':
        g = object.__new__(PopOutGame)
        g.rows = self.rows
        g.cols = self.cols
        g.board = [row[:] for row in self.board]
        g.current_player = self.current_player
        g.state_history = dict(self.state_history)
        g.winner = self.winner
        g.game_over = self.game_over
        return g

    # ─── Heuristic evaluation (used by MCTS heuristic rollouts) ───────────────

    def heuristic_score(self, player: int) -> float:
        """
        Simple heuristic: count threats (3-in-a-row with one open) weighted by
        position. Returns a score in roughly [-1, 1] from `player`'s perspective.
        """
        opponent = PLAYER2 if player == PLAYER1 else PLAYER1
        score = 0.0

        def count_window(window):
            p_cnt = window.count(player)
            o_cnt = window.count(opponent)
            e_cnt = window.count(EMPTY)
            if o_cnt > 0 and p_cnt > 0:
                return 0
            if p_cnt == 3 and e_cnt == 1:
                return 5
            if p_cnt == 2 and e_cnt == 2:
                return 2
            if o_cnt == 3 and e_cnt == 1:
                return -5
            if o_cnt == 2 and e_cnt == 2:
                return -2
            return 0

        b = self.board
        R, C = self.rows, self.cols
        for r in range(R):
            for c in range(C - 3):
                score += count_window([b[r][c+i] for i in range(4)])
        for r in range(R - 3):
            for c in range(C):
                score += count_window([b[r+i][c] for i in range(4)])
        for r in range(R - 3):
            for c in range(C - 3):
                score += count_window([b[r+i][c+i] for i in range(4)])
        for r in range(R - 3):
            for c in range(3, C):
                score += count_window([b[r+i][c-i] for i in range(4)])

        max_score = 5 * (R * (C-3) + (R-3) * C + 2 * (R-3) * (C-3))
        return score / (max_score + 1e-9)

    # ─── Display ───────────────────────────────────────────────────────────────

    @staticmethod
    def player_symbol(player: int) -> str:
        return 'X' if player == PLAYER1 else 'O'

    def display(self) -> None:
        """Print the board to stdout in the format shown in the assignment."""
        sym = {EMPTY: '-', PLAYER1: 'X', PLAYER2: 'O'}
        print()
        for row in self.board:
            print(''.join(sym[c] for c in row))
        print('1234567'[:self.cols])
        if not self.game_over:
            print(f"\nIt is {self.player_symbol(self.current_player)}'s turn.")
        elif self.winner:
            print(f"\n{self.player_symbol(self.winner)} wins!")
        else:
            print("\nIt's a draw!")
        print()

    def get_board_flat(self) -> list:
        """Flat list of board cells (row-major) for ML/dataset use."""
        return [cell for row in self.board for cell in row]

    def encode_state(self) -> list:
        """
        Encode the board from the CURRENT PLAYER's perspective.
        own disc = 1, opponent = 2, empty = 0.
        Returns a flat list of 42 integers (row-major).
        This perspective-invariant encoding is useful for ML datasets.
        """
        p   = self.current_player
        opp = PLAYER2 if p == PLAYER1 else PLAYER1
        enc = []
        for row in self.board:
            for cell in row:
                if   cell == p:   enc.append(1)
                elif cell == opp: enc.append(2)
                else:             enc.append(0)
        return enc

    def __repr__(self) -> str:
        sym = {EMPTY: '.', PLAYER1: 'X', PLAYER2: 'O'}
        rows = [''.join(sym[c] for c in row) for row in self.board]
        return '\n'.join(rows)
