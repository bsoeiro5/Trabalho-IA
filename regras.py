import pygame
from dameo_sub.constants import LARGURA, ALTURA, BRANCO, PRETO, CASTANHO

def regras(janela):
    """Exibe a tela com as regras do jogo, permitindo alternar entre diferentes textos."""
    
    # Carrega a imagem de fundo
    background = pygame.image.load("assets/machado.jpeg")
    background = pygame.transform.scale(background, (LARGURA, ALTURA))

    fonte_titulo = pygame.font.Font(None, 70)  # Aumenta o tamanho do título
    fonte_subtitulo = pygame.font.Font(None, 50)  # Fonte para os subtítulos
    fonte_texto = pygame.font.Font(None, 30)

    titulo = fonte_titulo.render("Regras do Jogo", True, BRANCO)  # Título em branco
    
    # Lista de textos de regras com subtítulos
    textos_regras = [
        ("Posição Inicial", ["1. A posição inicial é equilibrada entre o centro e as laterais", "para evitar concentração de peças nas bordas"]),
        ("Movimento Linear", ["2. O movimento linear ocorre quando um grupo contínuo de", "peças da mesma cor se desloca em linha reta, avançando", "uma casa, desde que a casa à frente esteja livre.","", "3. Reis não podem realizar movimento linear"]),
        ("Movimento", ["4. Peças, sejam isoladas ou em movimento linear, só podem", "avançar para a frente, seja na vertical ou nas diagonais", "5. Os Reis movem-se em qualquer direção, como a rainha ","no xadrez","6. Se uma peça chega à última linha do tabuleiro, é", "promovida a Rei","7. Se um grupo em movimento linear alcança a última", "linha, apenas a peça da frente é promovida"]),
        ("Captura", ["","8. Embora as peças possam mover-se", "na diagonal, todas as capturas devem", "ser feitas em linha reta.","", "9. Peças normais podem capturar para a", "frente, para trás e para os lados,", "através de um salto curto","", "10. Reis movem-se como a rainha no", " xadrez, mas capturam como uma", "torre, através de um salto longo"]),
        ("Obrigatoriedade da Captura", ["11. Capturar é obrigatório, tanto para peças normais", "quanto para reis.", "12. Se uma peça captura e fica em posição de capturar", "novamente, deve fazê-lo, permitindo capturas múltiplas", "no mesmo turno", "13.Não é permitido saltar sobre a mesma peça capturada", "mais de uma vez no mesmo turno, mas casas vazias", "podem ser atravessadas várias vezes"])
    ]
    
    # Carregar as imagens para "Posição Inicial"
    img_6x6 = pygame.image.load("assets/6x6.png")
    img_8x8 = pygame.image.load("assets/8x8.png")
    img_12x12 = pygame.image.load("assets/12x12.png")

    # Redimensionar as imagens para tamanhos maiores
    img_6x6 = pygame.transform.scale(img_6x6, (175, 175))
    img_8x8 = pygame.transform.scale(img_8x8, (175, 175))
    img_12x12 = pygame.transform.scale(img_12x12, (175, 175))

    # Carregar as imagens para "Movimento Linear"
    movimento_linear1 = pygame.image.load("assets/movimento_linear1.png")
    movimento_linear2 = pygame.image.load("assets/movimento_linear2.png")

    # Redimensionar as imagens para "Movimento Linear"
    movimento_linear1 = pygame.transform.scale(movimento_linear1, (200, 200))
    movimento_linear2 = pygame.transform.scale(movimento_linear2, (200, 200))

    # Carregar a imagem para "Captura"
    rei_movimento = pygame.image.load("assets/rei_movimento.png")
    rei_movimento = pygame.transform.scale(rei_movimento, (150, 150))  # Redimensionar a imagem

    peça_movimento = pygame.image.load("assets/peça_movimento.png")
    peça_movimento = pygame.transform.scale(peça_movimento, (225, 150))  # Redimensionar a imagem

    rei_captura = pygame.image.load("assets/rei_captura.png")
    rei_captura = pygame.transform.scale(rei_captura, (75, 375))  # Redimensionar a imagem
    
    peça_captura = pygame.image.load("assets/peça_captura.png")
    peça_captura = pygame.transform.scale(peça_captura, (75, 225))  # Redimensionar a imagem
    
    rei_captura_obrigatoria = pygame.image.load("assets/rei_captura_obrigatoria.png")
    rei_captura_obrigatoria = pygame.transform.scale(rei_captura_obrigatoria, (285, 171))  # Redimensionar a imagem

    indice_texto = 0  # Índice do texto atual

    rodando = True
    while rodando:
        janela.blit(background, (0, 0))  # Define o fundo

        # Posiciona o título
        janela.blit(titulo, ((LARGURA - titulo.get_width()) // 2, 50))

        # Renderiza o subtítulo e o texto das regras atual
        subtitulo_texto, regras_texto = textos_regras[indice_texto]
        subtitulo = fonte_subtitulo.render(subtitulo_texto, True, BRANCO)
        janela.blit(subtitulo, ((LARGURA - subtitulo.get_width()) // 2, 150))

        y_offset = 290
        for linha in regras_texto:
            texto = fonte_texto.render(linha, True, PRETO)
            janela.blit(texto, (100, y_offset))
            y_offset += 30

        # Mostrar imagens se o subtítulo for "Posição Inicial"
        if subtitulo_texto == "Posição Inicial":
            janela.blit(img_6x6, (102, 400))  # Posição da primeira imagem (elevada)
            janela.blit(img_8x8, (302, 450))  # Posição da imagem central
            janela.blit(img_12x12, (502, 400))  # Posição da terceira imagem (elevada)

        # Mostrar imagens se o subtítulo for "Movimento Linear"
        if subtitulo_texto == "Movimento Linear":
            janela.blit(movimento_linear1, (160, 450))  # Posição da primeira imagem
            janela.blit(movimento_linear2, (410, 450))  # Posição da segunda imagem

        if subtitulo_texto == "Movimento":
            janela.blit(rei_movimento, ((LARGURA - rei_movimento.get_width()-200) // 2, 533))
            janela.blit(peça_movimento,((LARGURA - peça_movimento.get_width()+200)//2,533)) # Centralizar a imagem

        if subtitulo_texto == "Captura":
            janela.blit(rei_captura, ((LARGURA - rei_captura.get_width()+300) // 2, 300))
            janela.blit(peça_captura, ((LARGURA - peça_captura.get_width()+500) // 2, 300))

        if subtitulo_texto == "Obrigatoriedade da Captura":
            janela.blit(rei_captura_obrigatoria, ((LARGURA - rei_captura_obrigatoria.get_width()) // 2, 520))

        # Desenhar botões de seta com borda preta e cor castanha
        seta_esquerda = pygame.Rect(40, ALTURA // 2 + 75, 50, 50)
        seta_direita = pygame.Rect(LARGURA - 100, ALTURA // 2 + 75, 50, 50)
        
        # Borda preta
        pygame.draw.rect(janela, PRETO, seta_esquerda.inflate(4, 4))  # Borda da seta esquerda
        pygame.draw.rect(janela, PRETO, seta_direita.inflate(4, 4))  # Borda da seta direita
        
        # Cor castanha
        pygame.draw.rect(janela, CASTANHO, seta_esquerda)
        pygame.draw.rect(janela, CASTANHO, seta_direita)

        # Desenhar setas
        # Seta esquerda
        pygame.draw.polygon(janela, BRANCO, [
            (seta_esquerda.x + 35, seta_esquerda.y + 10),  # Ponta da seta
            (seta_esquerda.x + 10, seta_esquerda.y + 25),  # Base superior
            (seta_esquerda.x + 35, seta_esquerda.y + 40)   # Base inferior
        ])
        
        # Seta direita
        pygame.draw.polygon(janela, BRANCO, [
            (seta_direita.x + 15, seta_direita.y + 10),  # Ponta da seta
            (seta_direita.x + 40, seta_direita.y + 25),  # Base superior
            (seta_direita.x + 15, seta_direita.y + 40)   # Base inferior
        ])

        pygame.display.update()

        # Loop de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    rodando = False
            if evento.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if seta_esquerda.collidepoint(x, y):
                    indice_texto = (indice_texto - 1) % len(textos_regras)  # Voltar ao texto anterior (circular)
                elif seta_direita.collidepoint(x, y):
                    indice_texto = (indice_texto + 1) % len(textos_regras)  # Avançar ao próximo texto (circular)