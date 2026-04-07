import math
import random
from dameo_sub.game import Game
from dameo_sub.tabuleiro import Tabuleiro
from dameo_sub.peças import Peças
from dameo_sub.constants import VERDE, LARANJA
from copy import deepcopy


class Node:
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state
        self.parent = parent
        self.move = move
        self.children = []
        self.wins = 0
        self.visits = 0
        self.untried_moves = self._get_untried_moves()

    def UCT_select_child(self, exploration_constant):
        if not self.children:
            return None
        
        # Fórmula UCT: exploitation (wins/visits) + exploration (sqrt(log(parent_visits)/child_visits))
        return max(self.children,
                  key=lambda c: (c.wins / c.visits if c.visits > 0 else 0) +
                               exploration_constant * math.sqrt(math.log(self.visits) / c.visits) if c.visits > 0 else float('inf'))

    def add_child(self, move, game_state):
        child = Node(game_state, parent=self, move=move)
        self.untried_moves.remove(move)
        self.children.append(child)
        return child

    def update(self, result):
        self.visits += 1
        self.wins += result

    def is_terminal(self):
        return self.game_state.tabuleiro.winner() is not None

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def _get_untried_moves(self):
        # CORREÇÃO: Verificar se há movimentos de captura obrigatórios primeiro
        moves = []
        capture_moves = []
        
        for piece in self.game_state.tabuleiro.get_all_peças(self.game_state.turn):
            valid_moves = self.game_state.tabuleiro.get_valid_moves(piece)
            for move, skip in valid_moves.items():
                if skip:  # Este é um movimento de captura
                    capture_moves.append((piece, move, skip))
                else:
                    moves.append((piece, move, skip))
        
        # Se houver movimentos de captura, apenas eles são válidos
        if capture_moves:
            return capture_moves
        return moves
    
class MCTS:
    def __init__(self, iterations=1000, simulation_depth=20, exploration_constant=1.4):
        self.iterations = iterations
        self.simulation_depth = simulation_depth
        self.exploration_constant = exploration_constant
        self.nodes_expanded = 0
        self.simulations_run = 0
        print(f"MCTS inicializado: {iterations} iterações, {simulation_depth} profundidade, {exploration_constant} const. exploração")

    def get_move(self, game):
        capture_moves = self._get_capture_moves(game)
        
        if capture_moves:
            print(f"IA: Encontrei {len(capture_moves)} movimentos de captura obrigatórios")
            root = Node(game)
            root.untried_moves = capture_moves
            
            # Execute MCTS para escolher o melhor movimento de captura
            for i in range(self.iterations):
                if i % 100 == 0:
                    print(f"MCTS: iteração {i}/{self.iterations}")
                
                node = self._select(root)
                if not node.is_terminal():
                    node = self._expand(node)
                    reward = self._simulate(node)
                    self._backpropagate(node, reward)

            if not root.children:
                return None

            best_child = max(root.children, key=lambda c: c.visits)
            chosen_move = best_child.move
            
            # Após executar o movimento, verificar se há mais capturas disponíveis
            peca, novo_pos, skip = chosen_move
            return chosen_move, True  # Retorna o movimento e um flag indicando que é uma captura
        else:
            root = Node(game)
            
            # MCTS normal para movimentos não-captura
            for i in range(self.iterations):
                if i % 100 == 0:
                    print(f"MCTS: iteração {i}/{self.iterations}")
                
                node = self._select(root)
                if not node.is_terminal():
                    node = self._expand(node)
                    reward = self._simulate(node)
                    self._backpropagate(node, reward)

            if not root.children:
                return None, False

            best_child = max(root.children, key=lambda c: c.visits)
            return best_child.move, False  # Retorna o movimento e indica que não é captura

    def _get_capture_moves(self, game):
        """Retorna todos os movimentos de captura disponíveis"""
        capture_moves = []
        for piece in game.tabuleiro.get_all_peças(game.turn):
            valid_moves = game.tabuleiro.get_valid_moves(piece)
            for move, skip in valid_moves.items():
                if skip:  # Este é um movimento de captura
                    capture_moves.append((piece, move, skip))
        return capture_moves

    def _select(self, node):
        while not node.is_terminal() and node.is_fully_expanded():
            child = node.UCT_select_child(self.exploration_constant)
            if child is None:
                break
            node = child
        return node

    def _expand(self, node):
        self.nodes_expanded += 1
        if node.untried_moves:
            move = random.choice(node.untried_moves)
            new_state = self._copy_game_state(node.game_state)
            
            # Aplicar o movimento no novo estado
            peca, novo_pos, skip = move
            
            # Obter a peça correspondente no novo tabuleiro
            new_peca = new_state.tabuleiro.get_peça(peca.linha, peca.coluna)
            
            # Realizar o movimento
            new_state.tabuleiro.movimento(new_peca, novo_pos[0], novo_pos[1])
            
            # Remover peças capturadas
            if skip:
                # Converter os objetos de peça para peças no novo tabuleiro
                new_skips = []
                for s in skip:
                    new_skips.append(new_state.tabuleiro.get_peça(s.linha, s.coluna))
                new_state.tabuleiro.remove(new_skips)
            
            new_state.change_turn()
            
            child = node.add_child(move, new_state)
            return child
        return node

    def _simulate(self, node):
        self.simulations_run += 1
        state = self._copy_game_state(node.game_state)
        depth = 0
        original_turn = state.turn
        
        while depth < self.simulation_depth:
            winner = state.tabuleiro.winner()
            if winner:
                if (winner == 'VERDE' and original_turn == VERDE) or \
                   (winner == 'LARANJA' and original_turn == LARANJA):
                    return 1.0
                else:
                    return 0.0
            
            # Verificar movimentos obrigatórios de captura primeiro
            capture_moves = []
            for piece in state.tabuleiro.get_all_peças(state.turn):
                valid_moves = state.tabuleiro.get_valid_moves(piece)
                for move, skip in valid_moves.items():
                    if skip:  # É um movimento de captura
                        capture_moves.append((piece, move, skip))
            
            if capture_moves:  # Se existem capturas obrigatórias
                # Escolher uma captura aleatória
                piece, move, skip = random.choice(capture_moves)
                
                # Realizar a captura
                state.tabuleiro.movimento(piece, move[0], move[1])
                state.tabuleiro.remove(skip)
                
                # Verificar se a mesma peça pode continuar capturando
                more_captures = False
                new_piece = state.tabuleiro.get_peça(move[0], move[1])
                valid_moves = state.tabuleiro.get_valid_moves(new_piece)
                
                for next_move, next_skip in valid_moves.items():
                    if next_skip:  # Há mais capturas disponíveis
                        more_captures = True
                        break
                
                if more_captures:
                    continue  # Não muda o turno, continua com a mesma peça
            else:
                # Se não há capturas, faz um movimento normal
                valid_moves = self._get_valid_moves(state)
                if not valid_moves:
                    break
                    
                piece, move, skip = random.choice(valid_moves)
                state.tabuleiro.movimento(piece, move[0], move[1])
            
            # Só muda o turno se não houver mais capturas disponíveis
            state.change_turn()
            depth += 1
        
        return self._evaluate_state(state, original_turn)

    def _evaluate_state(self, state, original_turn):
        # Usar a heurística implementada no tabuleiro
        score = state.tabuleiro.heuristica()
        
        # Ajustar o score baseado no turno original
        if original_turn == LARANJA:
            score = -score
            
        # Normalizar entre 0 e 1 usando sigmoid
        return 1 / (1 + math.exp(-score/10))

    def _backpropagate(self, node, reward):
        while node:
            node.update(reward)
            node = node.parent
            # Inverter a recompensa para o próximo nível
            reward = 1 - reward

    def _get_valid_moves(self, game):
        moves = []
        for peca in game.tabuleiro.get_all_peças(game.turn):
            valid_moves = game.tabuleiro.get_valid_moves(peca)
            for move, skip in valid_moves.items():
                moves.append((peca, move, skip))
        return moves

    def _copy_game_state(self, game):
        new_game = type(game)(game.win, game.LINHAS)  # Pass LINHAS to the Game constructor
        new_game.turn = game.turn
        new_game.selected = None
        new_game.valid_moves = {}
        
        # Copiar tabuleiro
        new_game.tabuleiro = Tabuleiro(game.LINHAS)  # Pass LINHAS to Tabuleiro constructor
        new_game.tabuleiro.board = [[self._copy_peca(peca, game.TAMANHO_QUADRADO) for peca in row] for row in game.tabuleiro.board]
        new_game.tabuleiro.verdes_left = game.tabuleiro.verdes_left
        new_game.tabuleiro.laranjas_left = game.tabuleiro.laranjas_left
        new_game.tabuleiro.verdes_kings = game.tabuleiro.verdes_kings
        new_game.tabuleiro.laranjas_kings = game.tabuleiro.laranjas_kings
        
        return new_game

    def _copy_peca(self, peca, tamanho_quadrado):
        if peca == 0:
            return 0
        new_peca = Peças(peca.linha, peca.coluna, peca.cor, tamanho_quadrado)
        new_peca.king = peca.king
        return new_peca