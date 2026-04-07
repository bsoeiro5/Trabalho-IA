import pygame
from .constants import VERDE, LARANJA, ALTURA, AZUL, LARGURA
from .tabuleiro import Tabuleiro 

class Game:
    def __init__(self, win, linhas=8):
        self.LINHAS = linhas  # Store LINHAS as an instance variable
        self.COLUNAS = linhas  # Assuming square board
        self.TAMANHO_QUADRADO = LARGURA // self.COLUNAS  # Calculate TAMANHO_QUADRADO
        self._init()
        self.win = win

    def _init(self):
        self.selected = None
        self.tabuleiro = Tabuleiro(self.LINHAS) 
        self.turn = VERDE
        self.valid_moves = {}
        self.must_capture = False
        self.capturing_piece = None  # Armazena a peça que está a capturar

    def winner(self):
        return self.tabuleiro.winner()
    
    def update(self,win):
        self.tabuleiro.desenhar(win)
        self.draw_valid_moves(self.valid_moves)
        pygame.display.update()

    def reset(self):
        self._init()

    def select(self, linha, coluna):
        # Se há uma peça em processo de captura múltipla
        if self.capturing_piece:
            # Verifica se o clique foi em um movimento válido
            if (linha, coluna) in self.valid_moves:
                return self._process_move(linha, coluna)
            else:
                # Se clicou em outro lugar, mantém a seleção da peça que está capturando
                return False
        
        peça = self.tabuleiro.get_peça(linha, coluna)
        
        # Verifica se há capturas obrigatórias
        self._check_capture_requirements()
        
        # Só permite selecionar peça se for do jogador atual
        if peça != 0 and peça.cor == self.turn:
            # Se há capturas obrigatórias, só permite selecionar peças que podem capturar
            if self.must_capture:
                self.valid_moves = self.tabuleiro.get_valid_moves(peça)
                self.valid_moves = {move: skipped for move, skipped in self.valid_moves.items() if skipped}
                
                if self.valid_moves:  # Se esta peça pode capturar
                    self.selected = peça
                    return True
                return False
            else:
                # Sem capturas obrigatórias, seleciona normalmente
                self.selected = peça
                self.valid_moves = self.tabuleiro.get_valid_moves(peça)
                return True
        
        # Se já tem uma peça selecionada e clicou em um movimento válido
        if self.selected and (linha, coluna) in self.valid_moves:
            return self._process_move(linha, coluna)
        
        # Se clicou em uma posição inválida, apenas limpa a seleção
        self.selected = None
        self.valid_moves = {}
        return False

    def _process_move(self, linha, coluna):
        if (linha, coluna) in self.valid_moves:
            peça = self.selected
            skipped = self.valid_moves[(linha, coluna)]
            
            # Faz o movimento
            self.tabuleiro.movimento(peça, linha, coluna)
            
            if skipped:  # Se houve captura
                self.tabuleiro.remove(skipped)
                
                # Verifica se há mais capturas disponíveis
                self.valid_moves = self.tabuleiro.get_valid_moves(peça)
                # Filtra apenas movimentos de captura
                self.valid_moves = {move: skip for move, skip in self.valid_moves.items() if skip}
                
                if self.valid_moves:  # Se pode continuar capturando
                    self.capturing_piece = peça
                    self.selected = peça
                    self.must_capture = True
                    return True
            
            # Fim do turno
            self._end_turn()
            return True
        
        return False

    def _end_turn(self):
        self.selected = None
        self.capturing_piece = None
        self.valid_moves = {}
        self.must_capture = False
        self.turn = LARANJA if self.turn == VERDE else VERDE

    def _check_capture_requirements(self):
        self.must_capture = False
        # Verifica se há capturas obrigatórias
        for linha in range(self.LINHAS):
            for coluna in range(self.COLUNAS):
                peça = self.tabuleiro.get_peça(linha, coluna)
                if peça != 0 and peça.cor == self.turn:
                    moves = self.tabuleiro.get_valid_moves(peça)
                    if any(skipped for skipped in moves.values() if skipped):
                        self.must_capture = True
                        return

    def draw_valid_moves(self, movimentos):
        for movimento in movimentos:
            linha, coluna = movimento
            pygame.draw.circle(self.win, AZUL, (coluna * self.TAMANHO_QUADRADO + self.TAMANHO_QUADRADO//2, linha * self.TAMANHO_QUADRADO + self.TAMANHO_QUADRADO//2), 15)

    def display_winner_message(self, winner):
        pygame.font.init()
        font = pygame.font.Font(None, 48)  # Usa a fonte padrão do pygame
        message = "Empate!" if winner is None else f"O jogador {winner} ganhou!"
        text = font.render(message, True, (0, 0, 255))  # Cor azul para a mensagem
        text_rect = text.get_rect(center=(LARGURA//2, ALTURA//2))
        self.win.blit(text, text_rect)
        pygame.display.update()

    def verificar_fim_do_jogo(self):
        # Verifica se há um vencedor
        vencedor = self.winner()
        
        if vencedor:
            self.display_winner_message(vencedor)  # Exibe a mensagem de vencedor
            return True
        
        # Verifica se o jogo terminou em empate (nenhum jogador pode se mover)
        verde_moves = any(
            self.tabuleiro.get_valid_moves(self.tabuleiro.get_peça(linha, coluna))
            for linha in range(self.LINHAS)
            for coluna in range(self.LINHAS)
            if self.tabuleiro.get_peça(linha, coluna) != 0 and self.tabuleiro.get_peça(linha, coluna).cor == VERDE
        )
        laranja_moves = any(
            self.tabuleiro.get_valid_moves(self.tabuleiro.get_peça(linha, coluna))
            for linha in range(self.LINHAS)
            for coluna in range(self.LINHAS)
            if self.tabuleiro.get_peça(linha, coluna) != 0 and self.tabuleiro.get_peça(linha, coluna).cor == LARANJA
        )
        
        if not verde_moves and not laranja_moves:
            self.display_winner_message(None)  # Exibe mensagem de empate
            return True
        
        return False
    
    def change_turn(self):
        self.valid_moves = {}
        if self.turn == VERDE:
            self.turn = LARANJA
        else:
            self.turn = VERDE
        print(f"Turno mudado para: {self.turn}")
    
    def get_tabuleiro(self):
        return self.tabuleiro

    def ai_move(self, tabuleiro):
        """Atualiza o tabuleiro com o movimento da IA"""
        if tabuleiro:
            current_turn = self.turn 
            self.tabuleiro = tabuleiro
            print(f"Movimento da IA aplicado com sucesso para peças {current_turn}")
            if self.turn == current_turn:
                self.change_turn()
                print(f"Turno mudado explicitamente para {self.turn}")
            else:
                print(f"Turno já foi alterado pelo algoritmo para {self.turn}")
        else:
            print("Erro: Tabuleiro inválido recebido pela IA")
    
    def get_valid_moves_for_piece(self, piece):
        """Retorna todos os movimentos válidos para uma peça específica."""
        if piece != 0 and piece.cor == self.turn:
            return self.tabuleiro.get_valid_moves(piece)
        return {}