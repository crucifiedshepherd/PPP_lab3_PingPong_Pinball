"""Ретро-меню выбора Pong или Pinball с отдельными PNG-ресурсами."""

import math
from pathlib import Path

import pygame

MENU_SIZE = (1200, 800)
CREAM = (255, 247, 228)
AMBER = (253, 177, 93)
BROWN = (74, 29, 19)
ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "menu"


class ArcadeMenu:
    """Отрисовывает стартовый экран и обрабатывает его кнопки."""

    def __init__(self):
        """Создаёт расположение кнопок и загружает фоновый рисунок."""
        self.elapsed = 0.0
        self.buttons = {
            "pong": pygame.Rect(325, 354, 550, 92),
            "pinball": pygame.Rect(325, 459, 550, 92),
            "quit": pygame.Rect(325, 574, 550, 92),
        }
        self.images = {}
        for name in (
            "retro_background", "title_plate",
            "button_normal", "button_hover",
        ):
            try:
                image = pygame.image.load(str(ASSET_DIR / (name + ".png")))
                self.images[name] = image.convert_alpha()
            except (pygame.error, OSError):
                self.images[name] = None
        self.font_title = pygame.font.SysFont(
            "Georgia, Palatino, DejaVu Serif", 60, bold=True,
        )
        self.font_button = pygame.font.SysFont(
            "Avenir Next, Trebuchet MS, DejaVu Sans", 35, bold=True,
        )
        self.font_small = pygame.font.SysFont(
            "Avenir Next, Trebuchet MS, DejaVu Sans", 21,
            bold=True,
        )
        self.font_micro = pygame.font.SysFont(
            "Avenir Next, Trebuchet MS, DejaVu Sans", 16,
            bold=True,
        )

    def handle_event(self, event):
        """Возвращает команду меню по клавише или нажатию мыши."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                return "pong"
            if event.key == pygame.K_2:
                return "pinball"
            if event.key == pygame.K_ESCAPE:
                return "quit"
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for name, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    return name
        return None

    def update(self, dt):
        """Обновляет только декоративные анимации."""
        self.elapsed += dt

    @staticmethod
    def _draw_label(surface, label, font, center, color, shadow=True):
        """Рисует надпись с центральным выравниванием."""
        text = font.render(label, True, color)
        rect = text.get_rect(center=center)
        if shadow:
            shade = font.render(label, True, (24, 10, 9))
            surface.blit(shade, rect.move(1, 3))
        surface.blit(text, rect)

    def _background(self, surface):
        """Рисует текстуру ретро-автомата с запасной заливкой."""
        bg = self.images["retro_background"]
        if bg is None:
            surface.fill((73, 24, 16))
        else:
            surface.blit(bg, (0, 0))
        # Лёгкая тень за кнопками повышает читаемость центральной зоны.
        veil = pygame.Surface(MENU_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(
            veil, (33, 10, 9, 72), pygame.Rect(240, 215, 720, 545),
        )
        surface.blit(veil, (0, 0))

    def _title(self, surface):
        """Рисует основную титульную табличку и подзаголовок."""
        plaque = self.images["title_plate"]
        if plaque is not None:
            surface.blit(plaque, plaque.get_rect(center=(600, 217)))
        else:
            pygame.draw.rect(
                surface, BROWN, (140, 143, 920, 160),
                border_radius=25,
            )
        self._draw_label(
            surface, "PING-PONG & PINBALL", self.font_title,
            (600, 206), CREAM,
        )
        self._draw_label(
            surface, "TWO GAMES · ONE ARCADE", self.font_small,
            (600, 258), AMBER,
        )
        self._draw_label(
            surface, "SELECT YOUR GAME", self.font_small,
            (600, 326), CREAM,
        )

    def _button(self, surface, name, title, subtitle, index):
        """Рисует одну кнопку с декоративным номером."""
        rect = self.buttons[name]
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        sprite_name = "button_hover" if hovered else "button_normal"
        art = self.images[sprite_name]
        if art is not None:
            surface.blit(art, rect.topleft)
        else:
            pygame.draw.rect(
                surface, BROWN, rect, border_radius=22,
            )
            pygame.draw.rect(
                surface, AMBER, rect, 3, border_radius=22,
            )
        caption_color = BROWN if hovered else CREAM
        sub_color = (138, 67, 34) if hovered else AMBER
        font = self.font_button
        self._draw_label(
            surface, title, font, (rect.centerx, rect.y + 38),
            caption_color, shadow=not hovered,
        )
        self._draw_label(
            surface, subtitle, self.font_micro,
            (rect.centerx, rect.y + 69), sub_color,
            shadow=False,
        )
        self._draw_label(
            surface, str(index).zfill(2), self.font_small,
            (rect.x + 47, rect.centery), sub_color, shadow=False,
        )
        if hovered:
            phase = 0.5 + 0.5 * math.sin(self.elapsed * 7)
            glow = (255, round(165 + 58 * phase), 96)
            pygame.draw.line(
                surface, glow, (rect.x + 26, rect.bottom - 14),
                (rect.right - 26, rect.bottom - 14), 2,
            )

    def draw(self, surface):
        """Отрисовывает главный экран выбора игрового режима."""
        self._background(surface)
        self._title(surface)
        self._button(
            surface, "pong", "PING-PONG", "TWO PLAYERS · NEON ARENA", 1,
        )
        self._button(
            surface, "pinball", "PINBALL", "SOLO · COPPER GLASS", 2,
        )
        self._button(surface, "quit", "QUIT", "EXIT THE ARCADE", 3)
        self._draw_label(
            surface, "PRESS 1 / 2 TO PLAY   ·   ESC TO QUIT",
            self.font_micro, (600, 696), (255, 238, 207),
        )
