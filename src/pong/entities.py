"""Игровые объекты: ракетка и шарик."""

from collections import deque

import pygame

from src.pong.config import (
    BALL_RADIUS, BALL_SPEED, COURT_BOTTOM, COURT_TOP,
    PADDLE_HEIGHT, PADDLE_SPEED, PADDLE_WIDTH,
)
from src.pong.physics import clamp


class Paddle:
    """Ракетка игрока с плавным движением по вертикали."""

    def __init__(self, x, center_y):
        """Создаёт ракетку на заданной горизонтальной позиции."""
        self.position_y = float(center_y - PADDLE_HEIGHT / 2)
        self.rect = pygame.Rect(
            int(x), round(self.position_y),
            PADDLE_WIDTH, PADDLE_HEIGHT,
        )
        self.impact_flash = 0.0

    def move(self, direction, dt):
        """Двигает ракетку, не позволяя выйти за границы арены."""
        self.position_y = clamp(
            self.position_y + direction * PADDLE_SPEED * dt,
            COURT_TOP + 14,
            COURT_BOTTOM - PADDLE_HEIGHT - 14,
        )
        self.rect.y = round(self.position_y)
        self.impact_flash = max(0.0, self.impact_flash - dt * 4)

    def reset(self, center_y):
        """Возвращает ракетку в начальное положение."""
        self.position_y = center_y - self.rect.height / 2
        self.rect.y = round(self.position_y)
        self.impact_flash = 0.0


class Ball:
    """Шарик с непрерывными координатами и историей движения."""

    def __init__(self, center_x, center_y):
        """Размещает шарик в центре арены."""
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.radius = BALL_RADIUS
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.trail = deque(maxlen=16)
        self.reset(center_x, center_y)

    @property
    def rect(self):
        """Возвращает прямоугольник для проверки столкновений."""
        return pygame.Rect(
            round(self.center_x - self.radius),
            round(self.center_y - self.radius),
            self.radius * 2, self.radius * 2,
        )

    def reset(self, center_x, center_y):
        """Останавливает шарик в центре перед новой подачей."""
        self.center_x = float(center_x)
        self.center_y = float(center_y)
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.trail.clear()

    def serve(self, direction, tilt=0.0):
        """Запускает шарик в выбранную сторону."""
        self.velocity_x = BALL_SPEED * (1 if direction >= 0 else -1)
        self.velocity_y = BALL_SPEED * tilt
        self.trail.clear()

    def move(self, dt):
        """Сдвигает шарик и сохраняет позиции для светового следа."""
        self.trail.append((self.center_x, self.center_y))
        self.center_x += self.velocity_x * dt
        self.center_y += self.velocity_y * dt
