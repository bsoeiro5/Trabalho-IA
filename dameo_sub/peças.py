from .constants import LARANJA, VERDE, LARANJA_ESCURO, PRETO, VERDE_ESCURO, coroa
import pygame

class Peças:
    ESPAÇO = 10
    BORDA = 3

    def __init__(self, linha, coluna, cor, tamanho_quadrado):
        self.linha = linha
        self.coluna = coluna
        self.cor = cor
        self.TAMANHO_QUADRADO = tamanho_quadrado
        
        if self.cor == VERDE:
            self.corsecundaria = VERDE_ESCURO
        else:
            self.corsecundaria = LARANJA_ESCURO
        self.king = False

        if self.cor == LARANJA:
            self.direções = -1
        else:
            self.direções = 1

        self.x = 0
        self.y = 0
        self.calc_pos()

    def calc_pos(self):     #calcular a posição da peça
        self.x = self.TAMANHO_QUADRADO * self.coluna + self.TAMANHO_QUADRADO // 2
        self.y = self.TAMANHO_QUADRADO * self.linha + self.TAMANHO_QUADRADO // 2

    def make_king(self):
        self.king = True

    def draw(self, win):
        raio = self.TAMANHO_QUADRADO // 2 - self.ESPAÇO
        pygame.draw.circle(win, self.corsecundaria, (self.x, self.y), raio + self.BORDA)
        pygame.draw.circle(win, self.cor, (self.x, self.y), raio)
        pygame.draw.circle(win, self.corsecundaria, (self.x, self.y), raio - 5)
        pygame.draw.circle(win, self.cor, (self.x, self.y), raio - 7)
        if self.king:
            win.blit(coroa, (self.x - coroa.get_width() // 2, self.y - coroa.get_height() // 2))
    
    def movimento(self, linha, coluna):
        self.linha = linha
        self.coluna = coluna
        self.calc_pos()
    
    def __repr__(self):
        return str(self.cor)