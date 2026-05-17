from __future__ import annotations

import math
import random

from popout_game import PopOutGame, PLAYER1, PLAYER2


class MCTSNode:

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

    def is_terminal(self) -> bool:
        return self.game_state.game_over

    def is_fully_expanded(self) -> bool:
        return len(self.untried_moves) == 0

    def uct_value(self, C: float) -> float:
        if self.visits == 0:
            return float('inf')
        exploitation = 1.0 - (self.wins / self.visits)
        exploration  = C * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def uct_tuned_value(self, C: float) -> float:
        if self.visits == 0:
            return float('inf')
        q = self.wins / self.visits
        variance = q - q * q + math.sqrt(2 * math.log(self.parent.visits) / self.visits)
        exploitation = 1.0 - q
        exploration  = C * math.sqrt(math.log(self.parent.visits) / self.visits
                                     * min(0.25, variance))
        return exploitation + exploration

    def best_child(self, C: float, use_tuned: bool = False) -> 'MCTSNode':
        if use_tuned:
            return max(self.children, key=lambda ch: ch.uct_tuned_value(C))
        return max(self.children, key=lambda ch: ch.uct_value(C))


class MCTS:

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

    def get_best_move(self, game_state: PopOutGame) -> tuple | None:
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

    def _select(self, node: MCTSNode) -> MCTSNode:
        while not node.is_terminal() and node.is_fully_expanded():
            node = node.best_child(self.exploration_constant, self.use_tuned_uct)
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        if not node.untried_moves:
            return node

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

    def _simulate(self, node: MCTSNode) -> float:
        state  = node.game_state._copy()
        player = node.game_state.current_player
        steps  = 0
        max_steps = 200

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
            return 0.5
        return 0.0

    def _heuristic_select(self, state: PopOutGame,
                          moves: list[tuple]) -> tuple:
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

    def _backpropagate(self, node: MCTSNode, result: float) -> None:
        while node is not None:
            node.visits += 1
            node.wins   += result
            result = 1.0 - result
            node = node.parent


def make_standard_mcts(iterations: int = 1000) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                name='MCTS-Standard')


def make_high_exploration_mcts(iterations: int = 1000) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=2.5,
                name='MCTS-HighExploration')


def make_low_exploration_mcts(iterations: int = 1000) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=0.5,
                name='MCTS-LowExploration')


def make_progressive_widening_mcts(iterations: int = 1000,
                                   max_children: int = 4) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                max_children=max_children,
                name=f'MCTS-PW({max_children})')


def make_heuristic_mcts(iterations: int = 1000) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                rollout_strategy='heuristic',
                name='MCTS-Heuristic')


def make_tuned_uct_mcts(iterations: int = 1000) -> MCTS:
    return MCTS(iterations=iterations,
                exploration_constant=math.sqrt(2),
                use_tuned_uct=True,
                name='MCTS-UCT-Tuned')
