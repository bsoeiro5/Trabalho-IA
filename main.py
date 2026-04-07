import pygame
import sys
import math
from popout_game import PopOutGame, PLAYER1, PLAYER2, EMPTY
from mcts import (make_standard_mcts, make_heuristic_mcts,
                  make_progressive_widening_mcts, make_high_exploration_mcts)

# --- Configurações Visuais ---
SQUARESIZE = 100
WIDTH = 7 * SQUARESIZE
HEIGHT = (6 + 1) * SQUARESIZE  # +1 para a área de interface/mensagens
RADIUS = int(SQUARESIZE / 2 - 5)
SIZE = (WIDTH, HEIGHT)

COLOR_BOARD = (0, 0, 255)
COLOR_EMPTY = (0, 0, 0)
COLOR_P1 = (255, 0, 0)     # X = Vermelho
COLOR_P2 = (255, 255, 0)   # O = Amarelo
COLOR_TEXT = (255, 255, 255)
COLOR_HINT = (0, 255, 0)   # Verde para as sugestões

class PopOutGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SIZE)
        pygame.display.set_caption("PopOut - Connect 4 Variant")
        self.font = pygame.font.SysFont("monospace", 30)
        self.small_font = pygame.font.SysFont("monospace", 18)
        self.clock = pygame.time.Clock()

    def draw_board(self, game: PopOutGame, message="", pop_mode=False, show_hints=False):
        self.screen.fill(COLOR_EMPTY)
        
        # Desenhar o retângulo azul do tabuleiro
        pygame.draw.rect(self.screen, COLOR_BOARD, (0, SQUARESIZE, WIDTH, HEIGHT - SQUARESIZE))

        # Desenhar as peças
        for r in range(game.rows):
            for c in range(game.cols):
                pos = (int(c * SQUARESIZE + SQUARESIZE/2), int((r+1) * SQUARESIZE + SQUARESIZE/2))
                if game.board[r][c] == EMPTY:
                    pygame.draw.circle(self.screen, COLOR_EMPTY, pos, RADIUS)
                elif game.board[r][c] == PLAYER1:
                    pygame.draw.circle(self.screen, COLOR_P1, pos, RADIUS)
                elif game.board[r][c] == PLAYER2:
                    pygame.draw.circle(self.screen, COLOR_P2, pos, RADIUS)

        if show_hints and not game.game_over:
            if pop_mode:
                # Mostrar onde se pode fazer POP (apenas na linha de baixo)
                pop_cols = game.get_pop_moves()
                for c in pop_cols:
                    # Desenha um ponto pequeno no centro da peça de baixo
                    pos = (int(c * SQUARESIZE + SQUARESIZE/2), int((game.rows) * SQUARESIZE + SQUARESIZE/2))
                    pygame.draw.circle(self.screen, COLOR_HINT, pos, 10)
            else:
                # Mostrar onde se pode fazer DROP
                drop_cols = game.get_drop_moves()
                for c in drop_cols:
                    # Encontrar a linha onde a peça vai cair (gravidade)
                    r = game.rows - 1
                    while r >= 0 and game.board[r][c] != EMPTY:
                        r -= 1
                    # Desenha um ponto pequeno na célula vazia onde a peça ficará
                    pos = (int(c * SQUARESIZE + SQUARESIZE/2), int((r+1) * SQUARESIZE + SQUARESIZE/2))
                    pygame.draw.circle(self.screen, COLOR_HINT, pos, 10)

        # Mensagem de estado no topo
        label = self.font.render(message, 1, COLOR_TEXT)
        self.screen.blit(label, (20, 10))
        
        # Legenda de comandos no fundo (opcional)
        help_txt = "Clique: DROP | Tecla P + Clique: POP"
        help_label = self.small_font.render(help_txt, 1, (200, 200, 200))
        self.screen.blit(help_label, (20, 70))

        pygame.display.update()

    def get_menu_choice(self, title, options):
        """Menu textual simples em Pygame para seleções iniciais."""
        while True:
            self.screen.fill(COLOR_EMPTY)
            title_label = self.font.render(title, 1, COLOR_TEXT)
            self.screen.blit(title_label, (50, 50))
            
            for i, opt in enumerate(options):
                opt_label = self.small_font.render(f"{i+1}. {opt}", 1, COLOR_TEXT)
                self.screen.blit(opt_label, (50, 120 + i * 40))
            
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        val = event.key - pygame.K_0
                        if 1 <= val <= len(options):
                            return val

    def play(self, ai1=None, ai2=None):
        game = PopOutGame()
        game_over = False
        pop_mode = False # Se True, o próximo clique tenta um POP

        while not game.game_over:
            current_ai = ai1 if game.current_player == PLAYER1 else ai2

            msg = f"Turno: {'X' if game.current_player == PLAYER1 else 'O'}"
            if pop_mode: msg += " [MODO POP]"
            self.draw_board(game, msg,pop_mode, show_hints=(current_ai is None))

            # Lógica de Repetição
            if game.is_repetition_draw_available():
                # Em GUI, podemos simplificar: se for AI vs AI termina, se houver humano, mostra aviso
                if ai1 and ai2:
                    print("Empate por repetição automático.")
                    break

            current_ai = ai1 if game.current_player == PLAYER1 else ai2

            if current_ai:
                # Turno da IA
                pygame.time.wait(500) # Pausa para o humano ver a jogada
                move = current_ai.get_best_move(game)
                if move:
                    game = game.apply_move(*move)
                else: break
            else:
                # Turno do Humano
                move_made = False
                while not move_made:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()
                        
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_p: # Segurar P para ativar modo Pop
                                pop_mode = not pop_mode
                                self.draw_board(game, f"Turno: {'X' if game.current_player == PLAYER1 else 'O'} {'[MODO POP]' if pop_mode else ''}", pop_mode, show_hints=True)

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            col = event.pos[0] // SQUARESIZE
                            m_type = 'pop' if pop_mode else 'drop'
                            
                            new_game = game.apply_move(m_type, col)
                            if new_game:
                                game = new_game
                                move_made = True
                                pop_mode = False # Reset mode
                            else:
                                print("Jogada Inválida!")

            if game.game_over:
                break

        # Fim de jogo
        winner_sym = game.player_symbol(game.winner) if game.winner else "Empate"
        final_msg = f"FIM: {winner_sym} Venceu!" if game.winner else "FIM: Empate!"
        self.draw_board(game, final_msg)
        
        # Esperar um pouco antes de fechar ou voltar ao menu
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in [pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    waiting = False

def main():
    gui = PopOutGUI()
    
    mode = gui.get_menu_choice("POP OUT - Selecione Modo", 
                               ["Human vs Human", "Human vs Computer", "Computer vs Computer"])

    if mode == 1:
        gui.play(None, None)
    
    elif mode == 2:
        ai_choice = gui.get_menu_choice("Escolha a IA", 
                                       ["Standard MCTS", "Heuristic MCTS", "Progressive Widening"])
        algos = {
            1: make_standard_mcts(1000),
            2: make_heuristic_mcts(1000),
            3: make_progressive_widening_mcts(1000),
        }
        side = gui.get_menu_choice("Jogar como?", ["Jogador 1 (X)", "Jogador 2 (O)"])
        if side == 1:
            gui.play(None, algos[ai_choice])
        else:
            gui.play(algos[ai_choice], None)

    elif mode == 3:
        c1 = gui.get_menu_choice("IA para Jogador 1 (X)", 
                                ["Standard", "Heuristic", "High Exploration", "Prog. Widening"])
        c2 = gui.get_menu_choice("IA para Jogador 2 (O)", 
                                ["Standard", "Heuristic", "High Exploration", "Prog. Widening"])
        
        def pick(c):
            return {
                1: make_standard_mcts(500),
                2: make_heuristic_mcts(500),
                3: make_high_exploration_mcts(500),
                4: make_progressive_widening_mcts(500),
            }[c]
        
        gui.play(pick(c1), pick(c2))

if __name__ == '__main__':
    main()