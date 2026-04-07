import pygame

# Constantes do tabuleiro
LARGURA, ALTURA = 800, 800  
LINHAS, COLUNAS = 8, 8
TAMANHO_QUADRADO = LARGURA // COLUNAS

# Cores RGB
VERMELHO = (255, 0, 0)
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
AZUL = (0, 0, 255)
CINZA = (128, 128, 128)
AMARELO = (255, 255, 0)
VERDE = (0, 255, 0)
ROSA = (255, 0, 255)
LARANJA = (255, 165, 0)
AZUL_CLARO = (135, 206, 250)
CASTANHO = (139, 69, 19)
ROXO = (128, 0, 128)
LARANJA_ESCURO = (255, 140, 0)
VERDE_ESCURO = (0, 100, 0)

coroa = pygame.transform.scale(pygame.image.load('assets/crown.png'), (44, 25))
