from __future__ import annotations

"""
Monte Carlo Tree Search (MCTS) for PopOut
==========================================

Implementation details
----------------------
* Four classic MCTS phases: Selection → Expansion → Simulation → Backpropagation.
* Upper Confidence Bound for Trees (UCT) governs child selection during the
  Selection phase.
* win/visit statistics are stored from EACH NODE's current player's perspective.
  Parent uses  (1 − child.wins/child.visits)  for UCT, which equals the parent's
  win-rate viewed through that child.

Variants explored
-----------------
1. Standard MCTS-UCT            – exploration_constant = √2
2. High-exploration MCTS        – exploration_constant = 2.5
3. Low-exploration (greedy)     – exploration_constant = 0.5
4. Progressive Widening         – max_children limits the branching factor
5. Heuristic Rollout            – rollout uses simple 1-step look-ahead
6. UCT-Tuned                    – replaces the exploration term with a tighter bound

UCT formula (standard):
    UCT(v) = (1 − Q/N) + C · √( ln(N_parent) / N )
where Q = cumulative wins, N = visits.
"""

import math
import random

from popout_game import PopOutGame, PLAYER1, PLAYER2


# ──────────────────────────────────────────────────────────────────────────────
# Node
# ──────────────────────────────────────────────────────────────────────────────

class MCTSNode:
    """
    A node in the MCTS search tree.

    Attributes
    ----------
    game_state   : PopOutGame – game state AT this node (the player in
                   game_state.current_player is the one who will MOVE next).
    parent       : MCTSNode | None
    move         : (move_type, col) that was applied to reach this node.
    wins         : cumulative reward from THIS NODE's current player's perspective.
    visits       : total number of times this node was visited.
    untried_moves: moves not yet expanded into children.
    """

    __slots__ = ('game_state', 'parent', 'move', 'children',
                 'wins', 'visits', 'untried_moves')

    def __init__(self, game_state: PopOutGame,
                 parent: 'MCTSNode | None' = None,
                 move: tuple | None = None):
        self.game_state   = game_state
        self.parent       = parent
        self.move         = move
        self.children: list['MCTSNode'] = []
        self.wins         = 0.0
        self.visits       = 0
        self.untried_moves: list[tuple] = list(game_state.get_all_moves())

    # ── Predicates ──────────────────────────────────────────────────────────

    def is_terminal(self) -> bool:
        return self.game_state.game_over

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    # ── UCT value (from PARENT's perspective) ───────────────────────────────

    def uct_value(self, C: float) -> float:
        """
        UCT from the PARENT's perspective:
            (1 − Q/N) + C · √( ln(parent.N) / N )

        A child with high Q/N means the CHILD's player wins often there —
        which is BAD for the parent (opponent).  Inverting with (1−Q/N) gives
        the PARENT's estimated win-rate.
        """
        if self.visits == 0:
            return float('inf')
        exploitation = 1.0 - (self.wins / self.visits)
        exploration  = C * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def uct_tuned_value(self, C: float) -> float:
        """
        UCT-Tuned (Auer et al.): replaces the exploration term with a tighter
        empirical variance bound.

            (1 − Q/N) + C · √( ln(parent.N)/N · min(1/4, V) )

        where V = variance estimate = Q/N − (Q/N)^2 + √(2·ln(parent.N)/N)
        """
        if self.visits == 0:
            return float('inf')
        q = self.wins / self.visits
        variance = q - q * q + math.sqrt(2 * math.log(self.parent.visits) / self.visits)
        exploitation = 1.0 - q
        exploration  = C * math.sqrt(math.log(self.parent.visits) / self.visits
                                     * min(0.25, variance))
        return exploitation + exploration

    # ── Child selection ─────────────────────────────────────────────────────

    def best_child(self, C: float, use_tuned: bool = False) -> 'MCTSNode':
        if use_tuned:
            return max(self.children, key=lambda ch: ch.uct_tuned_value(C))
        return max(self.children, key=lambda ch: ch.uct_value(C))


# ──────────────────────────────────────────────────────────────────────────────
# MCTS
# ──────────────────────────────────────────────────────────────────────────────

class MCTS:
    """
    Monte Carlo Tree Search for PopOut.

    Parameters
    ----------
    iterations          : int   – search budget (number of tree walk-downs).
    exploration_constant: float – C in UCT; higher → more exploration.
    max_children        : int|None – progressive widening: cap on children per node.
    rollout_strategy    : str   – 'random' | 'heuristic'.
    use_tuned_uct       : bool  – use UCT-Tuned instead of standard UCT.
    name                : str   – human-readable label for reporting.
    """

    def __init__(self,
                 iterations: int = 1000,
                 exploration_constant: float = math.sqrt(2),
                 max_children: int | None = None,
                 rollout_strategy: str = 'random',
                 use_tuned_uct: bool = False,
                 name: str = 'MCTS'):
        self.iterations           = iterations
        self.exploration_constant = exploration_constant
        self.max_children         = max_children
        self.rollout_strategy     = rollout_strategy
        self.use_tuned_uct        = use_tuned_uct
        self.name                 = name

    # ── Public API ──────────────────────────────────────────────────────────

    def get_best_move(self, game_state: PopOutGame) -> tuple | None:
        """
        Run MCTS from `game_state` and return the best (move_type, col).
        Uses the *robust child* policy: most-visited child at the root.
        """
        root = MCTSNode(game_state)

        for _ in range(self.iterations):
            leaf   = self._select(root)
            if not leaf.is_terminal():
                leaf = self._expand(leaf)
            result = self._simulate(leaf)
            self._backpropagate(leaf, result)

        if not root.children:
            moves = game_state.get_all_moves()
            return random.choice(moves) if moves else None

        return max(root.children, key=lambda ch: ch.visits).move

    def get_move_stats(self, game_state: PopOutGame) -> dict:
        """
        Run MCTS and return a dict with per-child statistics for analysis.
        """
        root = MCTSNode(game_state)
        for _ in range(self.iterations):
            leaf   = self._select(root)
            if not leaf.is_terminal():
                leaf = self._expand(leaf)
            result = self._simulate(leaf)
            self._backpropagate(leaf, result)

        stats = {}
        for ch in root.children:
            stats[ch.move] = {
                'visits'  : ch.visits,
                'win_rate': ch.wins / ch.visits if ch.visits else 0.0,
            }
        return stats

    # ── Phase 1 – Selection ─────────────────────────────────────────────────

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Descend the tree following UCT until a non-fully-expanded or terminal node."""
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child(self.exploration_constant, self.use_tuned_uct)
        return node

    # ── Phase 2 – Expansion ─────────────────────────────────────────────────

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Add one new child for a random untried move.

        With progressive widening (max_children is set), expansion stops once
        the limit is reached and UCT traversal continues on existing children.
        """
        if not node.untried_moves:
            return node

        # Progressive widening: stop expanding when limit is hit
        if (self.max_children is not None
                and len(node.children) >= self.max_children):
            return (node.best_child(self.exploration_constant, self.use_tuned_uct)
                    if node.children else node)

        move      = random.choice(node.untried_moves)
        new_state = node.game_state.apply_move(*move)

        if new_state is None:
            node.untried_moves.remove(move)
            return self._expand(node)

        child = MCTSNode(new_state, parent=node, move=move)
        node.untried_moves.remove(move)
        node.children.append(child)
        return child

    # ── Phase 3 – Simulation (Rollout) ──────────────────────────────────────

    def _simulate(self, node: MCTSNode) -> float:
        """
        Roll out a game from node's state using the chosen policy.
        Returns reward ∈ {0.0, 0.5, 1.0} from the perspective of the player
        who is to move AT `node`.
        """
        state  = node.game_state._copy()
        player = node.game_state.current_player
        steps  = 0
        max_steps = 200    # safety cap against infinite cycles

        while not state.game_over and steps < max_steps:
            moves = state.get_all_moves()
            if not moves:
                break

            if self.rollout_strategy == 'heuristic':
                move = self._heuristic_select(state, moves)
            else:
                move = random.choice(moves)

            nxt = state.apply_move(*move)
            if nxt is None:
                moves = [m for m in moves if m != move]
                if not moves:
                    break
                continue
            state = nxt
            steps += 1

        if state.winner == player:
            return 1.0
        if state.winner is None:
            return 0.5   # draw or depth-limit reached
        return 0.0

    def _heuristic_select(self, state: PopOutGame,
                          moves: list[tuple]) -> tuple:
        """
        One-step look-ahead rollout policy:
        1. Take an immediate win.
        2. Block an immediate opponent win.
        3. Otherwise pick randomly.
        """
        player   = state.current_player
        opponent = PLAYER2 if player == PLAYER1 else PLAYER1

        for move in moves:
            s = state.apply_move(*move)
            if s and s.winner == player:
                return move

        for move in moves:
            s = state.apply_move(*move)
            if s and s.winner == opponent:
                return move

        return random.choice(moves)

    # ── Phase 4 – Backpropagation ────────────────────────────────────────────

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        """
        Walk from `node` to the root, updating visit counts and win sums.
        The result is alternated at each level (opponent's perspective = 1−result).
        """
        while node is not None:
            node.visits += 1
            node.wins   += result
            result = 1.0 - result    # flip for the parent's perspective
            node = node.parent


# ──────────────────────────────────────────────────────────────────────────────
# Factory helpers for the experiments section
# ──────────────────────────────────────────────────────────────────────────────

def make_standard_mcts(iterations: int = 1000) -> MCTS:
    """Standard MCTS with UCT (C = √2)."""
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                name='MCTS-Standard')


def make_high_exploration_mcts(iterations: int = 1000) -> MCTS:
    """High-exploration MCTS (C = 2.5) — broader tree, shallower."""
    return MCTS(iterations=iterations,
                exploration_constant=2.5,
                name='MCTS-HighExploration')


def make_low_exploration_mcts(iterations: int = 1000) -> MCTS:
    """Low-exploration / greedy MCTS (C = 0.5) — exploits more, explores less."""
    return MCTS(iterations=iterations,
                exploration_constant=0.5,
                name='MCTS-LowExploration')


def make_progressive_widening_mcts(iterations: int = 1000,
                                   max_children: int = 4) -> MCTS:
    """Progressive widening: limit children per node to reduce branching."""
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                max_children=max_children,
                name=f'MCTS-PW({max_children})')


def make_heuristic_mcts(iterations: int = 1000) -> MCTS:
    """MCTS with one-step look-ahead rollout instead of pure random."""
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                rollout_strategy='heuristic',
                name='MCTS-Heuristic')


def make_tuned_uct_mcts(iterations: int = 1000) -> MCTS:
    """UCT-Tuned: tighter exploration bound using empirical variance."""
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                use_tuned_uct=True,
                name='MCTS-UCT-Tuned')
