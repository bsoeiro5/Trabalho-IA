import pygame
from .constants import CINZA, BRANCO, LARANJA, VERDE, PRETO, ALTURA, LARGURA
from .peças import Peças

class Tabuleiro:
    def __init__(self, linhas=8):
        self.LINHAS = linhas
        self.COLUNAS = linhas
        self.TAMANHO_QUADRADO = LARGURA // self.COLUNAS
        self.board = []
        self.verdes_left = self.laranjas_left = 18
        self.verdes_kings = self.laranjas_kings = 0
        self.create_tabuleiro()

    def draw_quadrados(self, win):
        win.fill(CINZA)
        for LINHA in range(self.LINHAS):
            for COLUNA in range(LINHA % 2, self.COLUNAS, 2):
                pygame.draw.rect(win, BRANCO, (LINHA * self.TAMANHO_QUADRADO, COLUNA * self.TAMANHO_QUADRADO, self.TAMANHO_QUADRADO, self.TAMANHO_QUADRADO))

    def draw_bordas(self, win):
        for LINHA in range(self.LINHAS):
            pygame.draw.line(win, PRETO, (0, LINHA * self.TAMANHO_QUADRADO), (ALTURA, LINHA * self.TAMANHO_QUADRADO), 2)
            for COLUNA in range(self.COLUNAS):
                pygame.draw.line(win, PRETO, (COLUNA * self.TAMANHO_QUADRADO, 0), (COLUNA * self.TAMANHO_QUADRADO, ALTURA), 2)

    def heuristica(self):
        # Peso para peças normais e kings
        peso_normal = 1
        peso_king = 2

        # Diferença de peças (kings valem mais)
        diferenca_pecas = (self.laranjas_left + self.laranjas_kings * peso_king) - (self.verdes_left + self.verdes_kings * peso_king)

        # Avaliação da proximidade de peças para se tornarem kings
        proximidade_kings_verde = sum(peca.linha for linha in self.board for peca in linha if peca != 0 and peca.cor == VERDE)
        proximidade_kings_laranja = sum((self.LINHAS - 1 - peca.linha) for linha in self.board for peca in linha if peca != 0 and peca.cor == LARANJA)
        fator_kings = (proximidade_kings_laranja - proximidade_kings_verde) / (self.LINHAS * self.laranjas_left + self.verdes_left + 1)  # Normalização

        # Controle do tabuleiro (posições centrais são estratégicas)
        pontos_estrategicos = [(self.LINHAS//2, self.COLUNAS//2), (self.LINHAS//2 - 1, self.COLUNAS//2), 
                              (self.LINHAS//2, self.COLUNAS//2 - 1), (self.LINHAS//2 - 1, self.COLUNAS//2 - 1)]
        controle_verde = sum(1 for linha, coluna in pontos_estrategicos if self.board[linha][coluna] != 0 and self.board[linha][coluna].cor == VERDE)
        controle_laranja = sum(1 for linha, coluna in pontos_estrategicos if self.board[linha][coluna] != 0 and self.board[linha][coluna].cor == LARANJA)
        controle_tabuleiro = controle_laranja - controle_verde

        # Combinação dos fatores com pesos ajustáveis
        return diferenca_pecas + fator_kings * 1.5 + controle_tabuleiro * 2

    def get_all_peças(self, cor):
        peças = []
        for LINHA in self.board:
            for peça in LINHA:
                if peça != 0 and peça.cor == cor:
                    peças.append(peça)
        return peças

    def movimento(self, peca, linha, coluna):
        self.board[peca.linha][peca.coluna], self.board[linha][coluna] = self.board[linha][coluna], self.board[peca.linha][peca.coluna]
        peca.movimento(linha, coluna)

        # Corrigir a lógica de transformação em king
        if (peca.cor == VERDE and linha == self.LINHAS - 1) or (peca.cor == LARANJA and linha == 0):
            peca.make_king()
            if peca.cor == VERDE:
                self.verdes_kings += 1
            else:
                self.laranjas_kings += 1
            
            print(f"Movimento realizado: peça agora está em ({peca.linha}, {peca.coluna})")

    def get_peça(self, linha, coluna):
        return self.board[linha][coluna]

    def create_tabuleiro(self):
        # Definir o número de linhas com peças baseado no tamanho do tabuleiro
        if self.LINHAS == 6:
            linhas_com_peças = 2
        elif self.LINHAS == 8:
            linhas_com_peças = 3
        elif self.LINHAS == 12:
            linhas_com_peças = 4
        else:
            raise ValueError("Tamanho do tabuleiro não suportado. Use 6x6, 8x8 ou 12x12.")

        for LINHA in range(self.LINHAS):
            self.board.append([])  # Cria uma linha (lista vazia)
            for COLUNA in range(self.COLUNAS):
                # Linhas do topo (peças verdes)
                if LINHA < linhas_com_peças and COLUNA >= LINHA and COLUNA < self.COLUNAS - LINHA:
                    self.board[LINHA].append(Peças(LINHA, COLUNA, VERDE, self.TAMANHO_QUADRADO))
                    # Linhas da base (peças laranjas)
                elif LINHA >= self.LINHAS - linhas_com_peças and COLUNA >= (self.LINHAS - 1 - LINHA) and COLUNA < self.COLUNAS - (self.LINHAS - 1 - LINHA):
                    self.board[LINHA].append(Peças(LINHA, COLUNA, LARANJA, self.TAMANHO_QUADRADO))
                else:
                    self.board[LINHA].append(0)  # Espaço vazio

    def desenhar(self, win): 
        self.draw_quadrados(win)
        for LINHA in range(self.LINHAS):
            for COLUNA in range(self.COLUNAS):
                peças = self.board[LINHA][COLUNA]
                if peças != 0:
                    peças.draw(win)
        self.draw_bordas(win)

    def remove(self, peças):
        for peça in peças:
            self.board[peça.linha][peça.coluna] = 0
            if peça != 0:
                if peça.cor == LARANJA:
                    self.laranjas_left -= 1
                else:
                    self.verdes_left -= 1

    def winner(self):
        if self.laranjas_left <= 0:
            return 'VERDE'
        elif self.verdes_left <= 0:
            return 'LARANJA'
        return None
    
    def get_valid_moves(self, peca):
        movimentos = {}
        esquerda = peca.coluna - 1
        direita = peca.coluna + 1
        linha = peca.linha

        if peca.king:
            movimentos.update(self._get_king_moves(peca))


        if peca.cor == LARANJA:
            movimentos.update(self._traverse_left(linha -1, max(linha-7, -1), -1, peca.cor, esquerda))
            movimentos.update(self._traverse_right(linha -1, max(linha-7, -1), -1, peca.cor, direita))
            movimentos.update(self._traverse_vertical(linha - 1, max(linha-7, -1), -1, peca.cor, peca.coluna))
            movimentos.update(self._traverse_horizontal(peca.coluna - 1, -1, -1, peca.cor, linha))
            movimentos.update(self._traverse_horizontal(peca.coluna + 1, self.COLUNAS, 1, peca.cor, linha))
            
        if peca.cor == VERDE:
            movimentos.update(self._traverse_left(linha +1, min(linha+7, self.LINHAS), 1, peca.cor, esquerda))
            movimentos.update(self._traverse_right(linha +1, min(linha+7, self.LINHAS), 1, peca.cor, direita))
            movimentos.update(self._traverse_vertical(linha + 1, min(linha+7, self.LINHAS), 1, peca.cor, peca.coluna))
            movimentos.update(self._traverse_horizontal(peca.coluna - 1, -1, -1, peca.cor, linha))
            movimentos.update(self._traverse_horizontal(peca.coluna + 1, self.COLUNAS, 1, peca.cor, linha))

        # Adiciona a verificação de captura para trás
        movimentos.update(self._check_backward_capture(peca))

        return movimentos
    
    def _get_king_moves(self, king):
        """ Retorna todos os movimentos possíveis do king. """
        movimentos = {}

        # Movimento livre em todas as direções
        movimentos.update(self._traverse_line(king.linha, king.coluna, -1, 0))  # Para cima
        movimentos.update(self._traverse_line(king.linha, king.coluna, 1, 0))   # Para baixo
        movimentos.update(self._traverse_line(king.linha, king.coluna, 0, -1))  # Para a esquerda
        movimentos.update(self._traverse_line(king.linha, king.coluna, 0, 1))   # Para a direita
        movimentos.update(self._traverse_line(king.linha, king.coluna, -1, -1)) # Diagonal superior esquerda
        movimentos.update(self._traverse_line(king.linha, king.coluna, -1, 1))  # Diagonal superior direita
        movimentos.update(self._traverse_line(king.linha, king.coluna, 1, -1))  # Diagonal inferior esquerda
        movimentos.update(self._traverse_line(king.linha, king.coluna, 1, 1))   # Diagonal inferior direita

        # Captura apenas na horizontal e vertical
        movimentos.update(self._king_capture(king, -1, 0))  # Captura para cima
        movimentos.update(self._king_capture(king, 1, 0))   # Captura para baixo
        movimentos.update(self._king_capture(king, 0, -1))  # Captura para a esquerda
        movimentos.update(self._king_capture(king, 0, 1))   # Captura para a direita

        return movimentos

    def _traverse_line(self, linha, coluna, dir_linha, dir_coluna):
        """ Move-se livremente em linha reta até encontrar uma peça ou borda do tabuleiro. """
        movimentos = {}
        r, c = linha + dir_linha, coluna + dir_coluna

        while 0 <= r < self.LINHAS and 0 <= c < self.COLUNAS:
            if self.board[r][c] == 0:  # Casa vazia, pode se mover
                movimentos[(r, c)] = []
            else:  # Encontrou uma peça, bloqueia o caminho
                break
            r += dir_linha
            c += dir_coluna

        return movimentos

    def _king_capture(self, king, dir_linha, dir_coluna):
        """ Captura para frente na direção horizontal ou vertical, podendo seguir até onde desejar após capturar. """
        movimentos = {}
        r, c = king.linha + dir_linha, king.coluna + dir_coluna
        capturada = None

        while 0 <= r < self.LINHAS and 0 <= c < self.COLUNAS:
            peça = self.board[r][c]

            if peça == 0:  # Casa vazia
                if capturada:  # Se já capturou, pode continuar
                    movimentos[(r, c)] = [capturada]
            elif peça.cor == king.cor:  # Peça da mesma cor bloqueia
                break
            else:  # Peça adversária
                if capturada:  # Se já capturou antes, não pode capturar duas vezes seguidas
                    break
                capturada = peça  # Marca a peça para possível captura

            r += dir_linha
            c += dir_coluna

        return movimentos

    def _traverse_diagonal_king(self, start_linha, start_coluna, step_linha, step_coluna):
        movimentos = {}

        linha, coluna = start_linha, start_coluna
        while 0 <= linha < self.LINHAS and 0 <= coluna < self.COLUNAS:
            if self.board[linha][coluna] == 0:  # Se for casa vazia, adiciona como movimento válido
                movimentos[(linha, coluna)] = []
            else:  # Se encontrar uma peça, para
                break

            linha += step_linha
            coluna += step_coluna

        return movimentos

    def _traverse_left(self, start, stop, step, cor, left, skipped=[]):
        movimentos = {}
        last = []

        for r in range(start, stop, step):
            if left < 0:
                break

            current = self.board[r][left]
            if current == 0:  # Casa vazia
                if skipped:
                    movimentos[(r, left)] = skipped
                else:
                    movimentos[(r, left)] = last

                if last:
                    if step == -1:
                        row = max(r - 1, 0)
                    else:
                        row = min(r + 1, self.LINHAS)
                    movimentos.update(self._traverse_left(r + step, row, step, cor, left - 1, skipped=skipped))
                    movimentos.update(self._traverse_right(r + step, row, step, cor, left + 1, skipped=skipped))
                break

            elif current.cor == cor:  # Se for peça da mesma cor, apenas continua
                left -= 1
                continue

            else:  # Peça do adversário (BLOQUEIA O MOVIMENTO)
                break

        left -= 1

        return movimentos

    def _traverse_right(self, start, stop, step, cor, right, skipped=[]):
        movimentos = {}
        last = []

        for r in range(start, stop, step):
            if right >= self.COLUNAS:
                break

            current = self.board[r][right]
            if current == 0:  # Casa vazia
                if skipped:
                    movimentos[(r, right)] = skipped
                else:
                    movimentos[(r, right)] = last

                if last:
                    if step == -1:
                        row = max(r - 1, 0)
                    else:
                        row = min(r + 1, self.LINHAS)
                    movimentos.update(self._traverse_left(r + step, row, step, cor, right - 1, skipped=skipped))
                    movimentos.update(self._traverse_right(r + step, row, step, cor, right + 1, skipped=skipped))
                break

            elif current.cor == cor:  # Se for peça da mesma cor, apenas continua
                right += 1
                continue

            else:  # Peça do adversário (BLOQUEIA O MOVIMENTO)
                break

        right += 1

        return movimentos

    def _traverse_vertical(self, start, stop, step, cor, coluna, skipped=[]):
        movimentos = {}
        last = []  # Peças que podem ser capturadas
        linear = False

        for r in range(start, stop, step):
            current = self.board[r][coluna]

            if current == 0:  # Casa vazia
                if skipped:
                    movimentos[(r, coluna)] = skipped
                else:
                    movimentos[(r, coluna)] = last

                if last:
                    if step == -1:
                        row = max(r - 1, 0)
                    else:
                        row = min(r + 1, self.LINHAS)

                    movimentos.update(self._traverse_left(r + step, row, step, cor, coluna - 1, skipped=skipped))
                    movimentos.update(self._traverse_right(r + step, row, step, cor, coluna + 1, skipped=skipped))
                break

            elif current.cor == cor: # Peça da mesma cor -> permite ultrapassar
                linear = True
                continue

            else:  # Peça adversária
                if last:  # Já encontrou uma peça adversária antes? Bloqueia o movimento
                    break
                if linear:  # Se já encontrou uma peça da mesma cor, não pode capturar
                    break
                else:
                    last.append(current)  # Marca para possível captura

        return movimentos
    
    def _traverse_horizontal(self, start, stop, step, cor, linha, skipped=[]):
        movimentos = {}
        last = []  # Peças que podem ser capturadas
        encontrou_adversario = False  # Flag para indicar se encontrou uma peça adversária

        for c in range(start, stop, step):
            if not 0 <= c < self.COLUNAS:  # Verificar se está dentro dos limites do tabuleiro
                break

            current = self.board[linha][c]

            if current == 0:  # Casa vazia
                if encontrou_adversario:  # Apenas permite mover se já encontrou uma peça adversária
                    movimentos[(linha, c)] = last
                break  # Não permite continuar movimento sem pular uma peça adversária

            elif current.cor == cor:  # Peça da mesma cor -> bloqueia o movimento
                break

            else:  # Peça adversária
                if encontrou_adversario:  # Se já encontrou uma peça adversária antes, a captura está bloqueada
                    break
                else:
                    last.append(current)  # Marca a peça adversária como capturada
                    encontrou_adversario = True  # Define a flag como verdadeira para permitir o pulo
                    continue  # Continua para verificar a casa seguinte

        return movimentos
    
    # Adicione este método à classe Tabuleiro
    def has_forced_captures(self, cor):
        for linha in range(self.LINHAS):
            for coluna in range(self.COLUNAS):
                peça = self.board[linha][coluna]
                if peça != 0 and peça.cor == cor:
                    moves = self.get_valid_moves(peça)
                    if any(moves.values()):  # Se houver algum movimento de captura
                        return True
        return False
    
    def _check_backward_capture(self, peca):
        movimentos = {}
        linha = peca.linha
        coluna = peca.coluna

        # Verifica a captura para trás
        if peca.cor == VERDE and linha > 1:
            if self.board[linha-1][coluna] != 0 and self.board[linha-1][coluna].cor != peca.cor:
                if self.board[linha-2][coluna] == 0:
                    movimentos[(linha-2, coluna)] = [self.board[linha-1][coluna]]
        elif peca.cor == LARANJA and linha < self.LINHAS - 2:
            if self.board[linha+1][coluna] != 0 and self.board[linha+1][coluna].cor != peca.cor:
                if self.board[linha+2][coluna] == 0:
                    movimentos[(linha+2, coluna)] = [self.board[linha+1][coluna]]

        return movimentos
    