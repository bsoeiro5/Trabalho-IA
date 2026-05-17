import pygame
import sys
import math
import os
import csv
import random
from popout_game import PopOutGame, PLAYER1, PLAYER2, EMPTY
from mcts import (make_standard_mcts, make_heuristic_mcts,
                  make_progressive_widening_mcts, make_high_exploration_mcts)
from decision_tree import ID3Tree


DATASET_CSV   = os.path.join('datasets', 'popout_dataset.csv')
FEATURE_NAMES = [f'cell_{r}_{c}' for r in range(6) for c in range(7)]


def _parse_move_label(label: str) -> tuple | None:
    try:
        mtype, col = label.split('_')
        return (mtype, int(col))
    except (ValueError, AttributeError):
        return None


def _load_dataset(path: str = DATASET_CSV):
    if not os.path.exists(path):
        return None, None
    X, y = [], []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f); next(reader)
        for row in reader:
            X.append([int(v) for v in row[:-1]])
            y.append(row[-1])
    return X, y


class ID3Player:
    def __init__(self, tree: ID3Tree, name: str = 'ID3-Tree'):
        self.tree = tree
        self.name = name
        self.fallback_count = 0
        self.move_count = 0

    @classmethod
    def from_dataset(cls, path: str = DATASET_CSV,
                     max_depth: int = 15,
                     min_samples_split: int = 5) -> 'ID3Player':
        X, y = _load_dataset(path)
        if X is None:
            raise FileNotFoundError(
                f'Dataset não encontrado em {path}. '
                f'Corra `python generate_dataset.py` primeiro.')
        tree = ID3Tree(max_depth=max_depth,
                       min_samples_split=min_samples_split)
        tree.fit(X, y, attribute_names=FEATURE_NAMES, continuous_attrs=set())
        return cls(tree)

    def get_best_move(self, game: PopOutGame):
        self.move_count += 1
        legal = game.get_all_moves()
        if not legal:
            return None
        pred = self.tree.predict_one(game.encode_state())
        move = _parse_move_label(pred) if isinstance(pred, str) else None
        if move in legal:
            return move
        self.fallback_count += 1
        return random.choice(legal)


SQUARESIZE = 90
COLS = 7
ROWS = 6
HEADER_H = 110
FOOTER_H = 44
BOARD_PADDING = 16
BOARD_W = COLS * SQUARESIZE
BOARD_H = ROWS * SQUARESIZE
WIDTH  = BOARD_W + BOARD_PADDING * 2
HEIGHT = HEADER_H + BOARD_H + FOOTER_H
RADIUS = int(SQUARESIZE / 2 - 7)
SIZE = (WIDTH, HEIGHT)


BG          = (15,  20,  40)
BOARD_COLOR = (25,  80, 180)
BOARD_DARK  = (15,  50, 120)
BOARD_LIGHT = (40, 110, 220)
HOLE_COLOR  = (10,  14,  30)
P1_COLOR    = (210,  45,  45)
P1_LIGHT    = (255, 120, 110)
P2_COLOR    = (220, 170,   0)
P2_LIGHT    = (255, 235, 100)
HINT_COLOR  = (50,  210,  90)
HINT_LIGHT  = (140, 255, 160)
TEXT_WHITE  = (235, 240, 255)
TEXT_DIM    = (150, 160, 190)
ACCENT      = ( 80, 160, 255)
PANEL_BG    = ( 22,  28,  55)
PANEL_BORDER= ( 55,  85, 160)
SELECTED_BG = ( 35,  75, 155)
HOVER_BG    = ( 28,  45, 100)
WIN_OVERLAY = (  0,   0,   0, 160)


def draw_piece(surface, color, light, cx, cy, radius):
    shadow_surf = pygame.Surface((radius*2+10, radius*2+10), pygame.SRCALPHA)
    pygame.draw.circle(shadow_surf, (0, 0, 0, 80), (radius+5, radius+7), radius)
    surface.blit(shadow_surf, (cx - radius - 5 + 3, cy - radius - 5 + 3))

    pygame.draw.circle(surface, color, (cx, cy), radius)

    dark = tuple(max(0, c - 50) for c in color)
    pygame.draw.circle(surface, dark, (cx, cy), radius, 3)

    highlight_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
    pygame.draw.circle(highlight_surf, (*light, 120),
                       (radius - radius//4, radius - radius//4), radius//3)
    surface.blit(highlight_surf, (cx - radius, cy - radius))


def draw_rounded_rect(surface, color, rect, radius=12, border_color=None, border_width=2):
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)


class PopOutGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(SIZE)
        pygame.display.set_caption("PopOut — Connect 4 Variant")
        self.font_title  = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_main   = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small  = pygame.font.SysFont("Arial", 15)
        self.font_tiny   = pygame.font.SysFont("Arial", 13)
        self.clock = pygame.time.Clock()
        self.bx = BOARD_PADDING
        self.by = HEADER_H

    def _board_rect(self):
        return pygame.Rect(self.bx - 6, self.by - 6,
                           BOARD_W + 12, BOARD_H + 12)

    def draw_board(self, game: PopOutGame, message="", pop_mode=False, show_hints=False):
        self.screen.fill(BG)

        header_rect = pygame.Rect(0, 0, WIDTH, HEADER_H)
        draw_rounded_rect(self.screen, PANEL_BG, header_rect, radius=0)
        pygame.draw.line(self.screen, PANEL_BORDER, (0, HEADER_H - 1), (WIDTH, HEADER_H - 1), 2)

        if not game.game_over:
            player_color = P1_COLOR if game.current_player == PLAYER1 else P2_COLOR
            player_light = P1_LIGHT if game.current_player == PLAYER1 else P2_LIGHT
            player_name  = "Jogador X" if game.current_player == PLAYER1 else "Jogador O"
            draw_piece(self.screen, player_color, player_light, 36, 38, 20)
            label = self.font_main.render(player_name, True, TEXT_WHITE)
            self.screen.blit(label, (66, 22))

        msg_label = self.font_main.render(message, True, ACCENT)
        self.screen.blit(msg_label, (18, 62))

        if pop_mode:
            badge_rect = pygame.Rect(WIDTH - 130, 20, 112, 34)
            draw_rounded_rect(self.screen, (180, 60, 0), badge_rect, radius=8,
                              border_color=(255, 120, 0), border_width=2)
            badge_label = self.font_small.render("MODO POP", True, (255, 220, 150))
            self.screen.blit(badge_label, (WIDTH - 120, 29))

        shadow = pygame.Surface((BOARD_W + 20, BOARD_H + 20), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 0))
        pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=16)
        self.screen.blit(shadow, (self.bx - 10 + 6, self.by - 10 + 8))

        board_rect = pygame.Rect(self.bx, self.by, BOARD_W, BOARD_H)
        draw_rounded_rect(self.screen, BOARD_COLOR, board_rect, radius=12,
                          border_color=BOARD_LIGHT, border_width=3)

        for r in range(game.rows):
            for c in range(game.cols):
                cx = self.bx + int(c * SQUARESIZE + SQUARESIZE / 2)
                cy = self.by + int(r * SQUARESIZE + SQUARESIZE / 2)

                cell = game.board[r][c]
                if cell == EMPTY:
                    pygame.draw.circle(self.screen, HOLE_COLOR, (cx, cy), RADIUS)
                    pygame.draw.circle(self.screen, (5, 8, 20), (cx, cy), RADIUS, 3)
                    refl = pygame.Surface((RADIUS*2, RADIUS*2), pygame.SRCALPHA)
                    pygame.draw.circle(refl, (255, 255, 255, 18),
                                       (RADIUS - RADIUS//4, RADIUS - RADIUS//4), RADIUS//4)
                    self.screen.blit(refl, (cx - RADIUS, cy - RADIUS))
                elif cell == PLAYER1:
                    draw_piece(self.screen, P1_COLOR, P1_LIGHT, cx, cy, RADIUS)
                elif cell == PLAYER2:
                    draw_piece(self.screen, P2_COLOR, P2_LIGHT, cx, cy, RADIUS)

        if show_hints and not game.game_over:
            if pop_mode:
                for c in game.get_pop_moves():
                    cx = self.bx + int(c * SQUARESIZE + SQUARESIZE / 2)
                    cy = self.by + int((game.rows - 1) * SQUARESIZE + SQUARESIZE / 2)
                    hint_surf = pygame.Surface((RADIUS*2, RADIUS*2), pygame.SRCALPHA)
                    pygame.draw.circle(hint_surf, (*HINT_COLOR, 90), (RADIUS, RADIUS), RADIUS)
                    pygame.draw.circle(hint_surf, (*HINT_COLOR, 200), (RADIUS, RADIUS), 10)
                    self.screen.blit(hint_surf, (cx - RADIUS, cy - RADIUS))
            else:
                for c in game.get_drop_moves():
                    r = game.rows - 1
                    while r >= 0 and game.board[r][c] != EMPTY:
                        r -= 1
                    if r >= 0:
                        cx = self.bx + int(c * SQUARESIZE + SQUARESIZE / 2)
                        cy = self.by + int(r * SQUARESIZE + SQUARESIZE / 2)
                        hint_surf = pygame.Surface((RADIUS*2, RADIUS*2), pygame.SRCALPHA)
                        pygame.draw.circle(hint_surf, (*HINT_COLOR, 70), (RADIUS, RADIUS), RADIUS)
                        pygame.draw.circle(hint_surf, (*HINT_LIGHT, 220), (RADIUS, RADIUS), 10)
                        self.screen.blit(hint_surf, (cx - RADIUS, cy - RADIUS))

        footer_y = self.by + BOARD_H
        footer_rect = pygame.Rect(0, footer_y, WIDTH, FOOTER_H)
        draw_rounded_rect(self.screen, PANEL_BG, footer_rect, radius=0)
        pygame.draw.line(self.screen, PANEL_BORDER, (0, footer_y), (WIDTH, footer_y), 2)

        help_parts = [
            ("Clique ", ACCENT, "DROP"),
            ("  |  ", TEXT_DIM, ""),
            ("P ", ACCENT, "+ Clique = "),
            (" POP", (255, 160, 60), ""),
        ]
        x_off = 18
        for key, kcolor, rest in help_parts:
            lbl = self.font_tiny.render(key, True, kcolor)
            self.screen.blit(lbl, (x_off, footer_y + 14))
            x_off += lbl.get_width()
            if rest:
                lbl2 = self.font_tiny.render(rest, True, TEXT_DIM)
                self.screen.blit(lbl2, (x_off, footer_y + 14))
                x_off += lbl2.get_width()

        pygame.display.update()

    def get_menu_choice(self, title, options, can_go_back = False):
        option_rects = []

        while True:
            mx, my = pygame.mouse.get_pos()
            self.screen.fill(BG)

            actual_options = list(options)
            if can_go_back:
                actual_options.append("Voltar")

            panel_w = WIDTH - 80
            panel_x = 40
            panel_y = 30
            opt_h = 52
            panel_h = 80 + len(actual_options) * opt_h + 20
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            draw_rounded_rect(self.screen, PANEL_BG, panel_rect, radius=16,
                              border_color=PANEL_BORDER, border_width=2)

            title_surf = self.font_title.render(title, True, TEXT_WHITE)
            self.screen.blit(title_surf, (panel_x + 24, panel_y + 22))
            pygame.draw.line(self.screen, PANEL_BORDER,
                             (panel_x + 24, panel_y + 58),
                             (panel_x + panel_w - 24, panel_y + 58), 1)

            option_rects = []
            for i, opt in enumerate(actual_options):
                is_back = can_go_back and i == len(actual_options) - 1
                oy = panel_y + 70 + i * opt_h
                rect = pygame.Rect(panel_x + 16, oy, panel_w - 32, opt_h - 8)
                option_rects.append(rect)

                is_hovered = rect.collidepoint(mx, my)
                if is_back:
                    bg = SELECTED_BG if is_hovered else HOVER_BG
                else:
                    bg = SELECTED_BG if is_hovered else HOVER_BG

                draw_rounded_rect(self.screen, bg, rect, radius=10,
                                  border_color=ACCENT if is_hovered else PANEL_BORDER,
                                  border_width=2 if is_hovered else 1)

                num_text = "B" if is_back else str(i + 1)
                num_surf = self.font_main.render(str(i + 1), True, ACCENT)
                self.screen.blit(num_surf, (rect.x + 16, rect.y + 10))

                opt_surf = self.font_main.render(opt, True, TEXT_WHITE if is_hovered else TEXT_DIM)
                self.screen.blit(opt_surf, (rect.x + 46, rect.y + 10))

            num_opts = len(actual_options)
            hint = self.font_tiny.render(f"Use o rato ou teclas 1–{num_opts} para selecionar", True, TEXT_DIM)
            self.screen.blit(hint, (panel_x + 24, panel_y + panel_h - 22))

            pygame.display.update()
            self.clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for i, rect in enumerate(option_rects):
                        if rect.collidepoint(event.pos):
                            if can_go_back and i == len(actual_options) - 1:
                                return -1
                            return i + 1
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and can_go_back:
                        return -1
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        val = event.key - pygame.K_0
                        if 1 <= val <= len(options):
                            if can_go_back and val == len(actual_options):
                                return -1
                            return val

    def _show_end_overlay(self, game):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        winner = game.winner
        if winner:
            color = P1_COLOR if winner == PLAYER1 else P2_COLOR
            light = P1_LIGHT if winner == PLAYER1 else P2_LIGHT
            sym   = "X" if winner == PLAYER1 else "O"
            msg   = f"Jogador {sym} Venceu!"
        else:
            color = ACCENT
            light = TEXT_WHITE
            msg   = "Empate!"

        box_w, box_h = 380, 120
        box_x = (WIDTH - box_w) // 2
        box_y = (HEIGHT - box_h) // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)
        draw_rounded_rect(self.screen, PANEL_BG, box_rect, radius=18,
                          border_color=color, border_width=3)

        if winner:
            draw_piece(self.screen, color, light, box_x + 50, box_y + box_h // 2, 22)

        msg_surf = self.font_title.render(msg, True, color)
        self.screen.blit(msg_surf, (box_x + (80 if winner else 50), box_y + 30))

        sub_surf = self.font_small.render("Clique ou prima uma tecla para sair", True, TEXT_DIM)
        self.screen.blit(sub_surf, (box_x + 100, box_y + 78))

        pygame.display.update()

    def play(self, ai1=None, ai2=None):
        game = PopOutGame()
        pop_mode = False

        while not game.game_over:
            current_ai = ai1 if game.current_player == PLAYER1 else ai2

            msg = "Turno da IA..." if current_ai else "A sua vez"
            self.draw_board(game, msg, pop_mode, show_hints=(current_ai is None))

            if game.is_repetition_draw_available():
                if ai1 and ai2:
                    break

            if game.is_board_full():
                if current_ai is None:
                    choice = self.get_menu_choice(
                        "Tabuleiro cheio! O que deseja fazer?",
                        ["Fazer Pop (continuar)", "Declarar Empate"],
                        can_go_back=False
                    )
                    if choice == 2:
                        break
                pop_mode = True

            if current_ai:
                pygame.time.wait(400)
                move = current_ai.get_best_move(game)
                if move:
                    game = game.apply_move(*move)
                else:
                    break
            else:
                move_made = False
                while not move_made:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit(); sys.exit()

                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_p:
                                pop_mode = not pop_mode
                                player_sym = "X" if game.current_player == PLAYER1 else "O"
                                self.draw_board(game,
                                               f"Turno: {player_sym}",
                                               pop_mode, show_hints=True)

                        if event.type == pygame.MOUSEBUTTONDOWN:
                            col = (event.pos[0] - self.bx) // SQUARESIZE
                            if 0 <= col < COLS:
                                m_type = 'pop' if pop_mode else 'drop'
                                new_game = game.apply_move(m_type, col)
                                if new_game:
                                    game = new_game
                                    move_made = True
                                    pop_mode = False

            if game.game_over:
                break

        self.draw_board(game, "Fim de Jogo", False)
        self._show_end_overlay(game)

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type in [pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                    waiting = False


def main():
    gui = PopOutGUI()
    while True:
        mode = gui.get_menu_choice("PopOut — Selecione Modo",
                                ["Humano vs Humano",
                                    "Humano vs Computador",
                                    "Computador vs Computador"], can_go_back=False)

        if mode == 1:
            gui.play(None, None)

        elif mode == 2:
            ai_choice = gui.get_menu_choice("Escolha o Algoritmo de IA",
                                        ["Standard MCTS",
                                            "Heuristic MCTS",
                                            "High Exploration",
                                            "Progressive Widening",
                                            "ID3 (Árvore de Decisão)"], can_go_back=True)

            if ai_choice == -1: continue

            try:
                algos = {
                    1: lambda: make_standard_mcts(1000),
                    2: lambda: make_heuristic_mcts(1000),
                    3: lambda: make_high_exploration_mcts(1000),
                    4: lambda: make_progressive_widening_mcts(1000),
                    5: lambda: ID3Player.from_dataset(),
                }
                ai_instance = algos[ai_choice]()
            except FileNotFoundError as exc:
                print(f'[ERRO] {exc}')
                continue

            side = gui.get_menu_choice("Jogar como?",
                                    ["Jogador 1 (X — Vermelho)",
                                        "Jogador 2 (O — Amarelo)"], can_go_back=True)
            if side == -1: continue

            if side == 1:
                gui.play(None, ai_instance)
            else:
                gui.play(ai_instance, None)

        elif mode == 3:
            ai_options = ["Standard MCTS", "Heuristic MCTS",
                          "High Exploration", "Prog. Widening",
                          "ID3 (Árvore de Decisão)"]
            c1 = gui.get_menu_choice("IA para Jogador 1 (X)", ai_options, can_go_back=True)
            if c1 == -1: continue
            c2 = gui.get_menu_choice("IA para Jogador 2 (O)", ai_options, can_go_back=True)
            if c2 == -1: continue

            def pick(c):
                if c == 5:
                    return ID3Player.from_dataset()
                return {
                    1: make_standard_mcts(500),
                    2: make_heuristic_mcts(500),
                    3: make_high_exploration_mcts(500),
                    4: make_progressive_widening_mcts(500),
                }[c]

            try:
                p1 = pick(c1); p2 = pick(c2)
            except FileNotFoundError as exc:
                print(f'[ERRO] {exc}')
                continue
            gui.play(p1, p2)


if __name__ == '__main__':
    main()
