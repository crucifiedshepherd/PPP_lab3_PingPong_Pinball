"""Отрисовка неоновой арены, счёта и игровых меню Pong."""

import math
from functools import lru_cache

import pygame

from src.pong.config import (
    COURT_BOTTOM, COURT_LEFT, COURT_RIGHT, COURT_TOP,
    CYAN, HEIGHT, IVORY, NAVY, PINK, WIDTH,
)


class PongRenderer:
    """Предоставляет игровые и интерфейсные элементы Pong."""

    @staticmethod
    @lru_cache(maxsize=48)
    def _font(size, bold=False):
        """Подбирает современный системный шрифт с запасным вариантом."""
        return pygame.font.SysFont(
            "Avenir Next, Trebuchet MS, DejaVu Sans", size, bold=bold,
        )

    @staticmethod
    def _text(surface, caption, font, center, color, glow=False):
        """Рисует надпись с мягкой тенью для контраста."""
        text = font.render(caption, True, color)
        rect = text.get_rect(center=center)
        if glow:
            shadow = font.render(caption, True, (31, 78, 113))
            surface.blit(shadow, rect.move(2, 4))
        surface.blit(text, rect)

    @staticmethod
    def overlay_buttons(finished=False):
        """Возвращает расположение кнопок паузы и конца партии."""
        if finished:
            return {
                "restart": pygame.Rect(383, 451, 206, 60),
                "menu": pygame.Rect(609, 451, 206, 60),
                "quit": pygame.Rect(460, 529, 280, 52),
            }
        return {
            "resume": pygame.Rect(383, 451, 206, 60),
            "restart": pygame.Rect(609, 451, 206, 60),
            "menu": pygame.Rect(383, 529, 206, 58),
            "quit": pygame.Rect(609, 529, 206, 58),
        }

    def _draw_ball(self, surface):
        """Рисует светящийся шарик и затухающий след."""
        points = list(self.ball.trail)
        trail_count = len(points)
        for index, point in enumerate(points):
            ratio = (index + 1) / max(1, trail_count)
            radius = max(2, int(7 * ratio))
            glow = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.circle(
                glow, (122, 222, 254, int(63 * ratio)),
                (25, 25), radius + 8,
            )
            pygame.draw.circle(
                glow, (224, 249, 255, int(140 * ratio)),
                (25, 25), radius,
            )
            surface.blit(glow, (point[0] - 25, point[1] - 25))

        img = self.art.get("ball", (66, 66))
        x, y = round(self.ball.center_x), round(self.ball.center_y)
        if img is not None:
            surface.blit(img, img.get_rect(center=(x, y)))
        else:
            pygame.draw.circle(surface, IVORY, (x, y), self.ball.radius)

    def _draw_paddle(self, surface, paddle, name, color):
        """Рисует ракетку с цветным ореолом и эффектом удара."""
        rect = paddle.rect
        glow = pygame.Surface((68, rect.height + 45), pygame.SRCALPHA)
        intensity = 70 + round(72 * paddle.impact_flash)
        pygame.draw.rect(
            glow, (*color, intensity),
            pygame.Rect(15, 13, 38, rect.height + 12),
            border_radius=19,
        )
        glow = pygame.transform.smoothscale(
            glow, (82, rect.height + 51),
        )
        surface.blit(glow, (rect.centerx - 41, rect.y - 25))
        art = self.art.get(name, (48, rect.height + 42))
        if art is not None:
            surface.blit(art, art.get_rect(center=rect.center))
        else:
            pygame.draw.rect(surface, color, rect, border_radius=10)

    def _draw_particles(self, surface):
        """Рисует короткие вспышки после столкновений."""
        sparks = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for effect in self.particles:
            ratio = max(0.0, effect["life"] / effect["duration"])
            x = round(effect["x"])
            y = round(effect["y"])
            radius = max(1, round(4 * ratio))
            pygame.draw.circle(
                sparks, (*effect["color"], int(230 * ratio)),
                (x, y), radius,
            )
        surface.blit(sparks, (0, 0))

    def _draw_score(self, surface):
        """Рисует цифровой счёт и подписи игроков."""
        small = self._font(20, True)
        big = self._font(78, True)
        self._text(
            surface, "PLAYER 01", small, (178, 62), CYAN,
        )
        self._text(
            surface, "W / S", self._font(17), (178, 96),
            (177, 202, 220),
        )
        self._text(
            surface, "PLAYER 02", small, (1022, 62), PINK,
        )
        self._text(
            surface, "UP / DOWN", self._font(17), (1022, 96),
            (177, 202, 220),
        )
        self._text(
            surface, str(self.left_score).zfill(2), big,
            (484, 76), CYAN, glow=True,
        )
        self._text(
            surface, ":", self._font(62, True),
            (600, 75), IVORY,
        )
        self._text(
            surface, str(self.right_score).zfill(2), big,
            (716, 76), PINK, glow=True,
        )
        pygame.draw.line(
            surface, (34, 78, 115), (78, 135), (1122, 135), 1,
        )

    def _draw_serve(self, surface):
        """Показывает короткую подсказку перед подачей."""
        if self.serve_timer <= 0 or self.is_finished:
            return
        pulse = 0.75 + 0.25 * math.sin(self.elapsed * 7)
        panel = pygame.Surface((450, 66), pygame.SRCALPHA)
        pygame.draw.rect(
            panel, (7, 21, 37, round(199 * pulse)),
            (0, 0, 450, 66), border_radius=15,
        )
        pygame.draw.rect(
            panel, (*CYAN, 180),
            (0, 0, 450, 66), 2, border_radius=15,
        )
        surface.blit(panel, (375, 396))
        self._text(
            surface, "GET READY", self._font(32, True),
            (600, 428), IVORY,
        )

    def _draw_button(self, surface, rect, caption, hovered, tint):
        """Рисует контрастную кнопку меню."""
        fill = (38, 68, 91) if hovered else (12, 31, 52)
        pygame.draw.rect(surface, (3, 11, 24), rect.move(0, 6),
                         border_radius=13)
        pygame.draw.rect(surface, fill, rect, border_radius=13)
        pygame.draw.rect(surface, tint, rect, 3, border_radius=13)
        if hovered:
            pygame.draw.rect(
                surface, (220, 243, 255), rect.inflate(-8, -8),
                1, border_radius=10,
            )
        self._text(
            surface, caption, self._font(22, True),
            rect.center, IVORY,
        )

    def _draw_modal(self, surface):
        """Рисует полноэкранное затемнение и меню паузы или победы."""
        screen_shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        screen_shade.fill((4, 9, 21, 218))
        surface.blit(screen_shade, (0, 0))
        panel = pygame.Rect(303, 196, 594, 430)
        pygame.draw.rect(surface, (2, 10, 19), panel.move(7, 9),
                         border_radius=24)
        pygame.draw.rect(surface, (9, 24, 46), panel,
                         border_radius=24)
        pygame.draw.rect(surface, CYAN, panel, 3, border_radius=24)
        pygame.draw.line(surface, PINK, (341, 219), (859, 219), 2)
        title = "GAME OVER" if self.is_finished else "PAUSED"
        self._text(
            surface, title, self._font(52, True),
            (600, 290), IVORY, glow=True,
        )
        sub = (
            "PLAYER {} WINS!".format(self.winner)
            if self.is_finished else "GAME ON HOLD"
        )
        self._text(
            surface, sub, self._font(21, True),
            (600, 352), CYAN if self.winner != 2 else PINK,
        )
        self._text(
            surface, "{}  :  {}".format(
                self.left_score, self.right_score,
            ), self._font(28, True), (600, 395), IVORY,
        )
        mouse = pygame.mouse.get_pos()
        for name, rect in self.overlay_buttons(self.is_finished).items():
            captions = {
                "resume": "RESUME", "restart": "RESTART",
                "menu": "MAIN MENU", "quit": "QUIT GAME",
            }
            tint = PINK if name == "quit" else CYAN
            self._draw_button(surface, rect, captions[name],
                              rect.collidepoint(mouse), tint)

    def draw(self, surface=None):
        """Собирает окончательный кадр Pong."""
        surface = surface or self.screen
        background = self.art.background()
        if background is None:
            surface.fill(NAVY)
        else:
            surface.blit(background, (0, 0))
        self._draw_score(surface)
        self._draw_paddle(
            surface, self.left_paddle, "paddle_cyan", CYAN,
        )
        self._draw_paddle(
            surface, self.right_paddle, "paddle_pink", PINK,
        )
        self._draw_ball(surface)
        self._draw_particles(surface)
        self._draw_serve(surface)
        self._text(
            surface, "FIRST TO 5", self._font(17, True),
            (600, 768), (125, 170, 201),
        )
        if self.is_finished or self.is_paused:
            self._draw_modal(surface)
