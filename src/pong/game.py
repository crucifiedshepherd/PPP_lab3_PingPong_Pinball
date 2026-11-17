"""Игровой процесс и столкновения неонового Pong."""

import math
import random

import pygame

from src.pong.audio import PongSounds
from src.pong.config import (
    BALL_SPEED, COURT_BOTTOM, COURT_LEFT, COURT_RIGHT, COURT_TOP,
    CYAN, HEIGHT, MAX_BALL_SPEED, PINK, WIDTH, WIN_SCORE,
)
from src.pong.entities import Ball, Paddle
from src.pong.physics import clamp, paddle_reflection
from src.pong.renderer import PongRenderer
from src.pong.sprites import PongSprites


class PongGame(PongRenderer):
    """Обрабатывает управление, очки и визуальные события Pong."""

    WIN_SCORE = WIN_SCORE

    def __init__(self, screen):
        """Создаёт игру для уже открытого окна Pygame."""
        self.screen = screen
        self.left_paddle = Paddle(COURT_LEFT + 28, HEIGHT / 2 + 45)
        self.right_paddle = Paddle(COURT_RIGHT - 50, HEIGHT / 2 + 45)
        self.ball = Ball(WIDTH / 2, (COURT_TOP + COURT_BOTTOM) / 2)
        self.art = PongSprites()
        self.sounds = PongSounds()
        self.particles = []
        self.left_score = 0
        self.right_score = 0
        self.winner = 0
        self.is_finished = False
        self.is_paused = False
        self.menu_requested = False
        self.quit_requested = False
        self.serve_timer = 0.9
        self.serve_direction = random.choice((-1, 1))
        self.elapsed = 0.0
        self.restart()

    def restart(self):
        """Запускает новую партию с нулевым счётом."""
        self.left_score = 0
        self.right_score = 0
        self.winner = 0
        self.is_finished = False
        self.is_paused = False
        self.menu_requested = False
        self.quit_requested = False
        self.elapsed = 0.0
        self.particles.clear()
        self.left_paddle.reset((COURT_TOP + COURT_BOTTOM) / 2)
        self.right_paddle.reset((COURT_TOP + COURT_BOTTOM) / 2)
        self._prepare_serve(random.choice((-1, 1)))

    def _prepare_serve(self, direction):
        """Ставит шарик в центр перед следующей подачей."""
        self.ball.reset(WIDTH / 2, (COURT_TOP + COURT_BOTTOM) / 2)
        self.serve_direction = direction
        self.serve_timer = 0.9

    def _pause(self):
        """Открывает или закрывает меню, останавливая игру."""
        if not self.is_finished:
            self.is_paused = not self.is_paused
            self.sounds.play("pause")

    def handle_event(self, event):
        """Обрабатывает Esc и нажатия кнопок экранного меню."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._pause()
                return
            if self.is_finished and event.key == pygame.K_r:
                self.restart()
                return
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
            and (self.is_paused or self.is_finished)
        ):
            for name, rect in self.overlay_buttons(
                self.is_finished,
            ).items():
                if rect.collidepoint(event.pos):
                    self.sounds.play("select")
                    self._menu_action(name)
                    break

    def _menu_action(self, name):
        """Выбирает действие из меню паузы или Game Over."""
        if name == "resume" and not self.is_finished:
            self.is_paused = False
        elif name == "restart":
            self.restart()
        elif name == "menu":
            self.menu_requested = True
        elif name == "quit":
            self.quit_requested = True

    def _spawn_sparks(self, position, tint, count=13):
        """Создаёт частицы столкновения без влияния на физику."""
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(55, 250)
            self.particles.append({
                "x": float(position[0]),
                "y": float(position[1]),
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": tint,
                "life": random.uniform(.14, .42),
                "duration": .42,
            })
        self.particles = self.particles[-110:]

    def _update_particles(self, dt):
        """Продвигает искры и удаляет погасшие частицы."""
        for effect in self.particles:
            effect["x"] += effect["vx"] * dt
            effect["y"] += effect["vy"] * dt
            effect["life"] -= dt
        self.particles = [
            effect for effect in self.particles if effect["life"] > 0
        ]

    def _player_input(self):
        """Читает W/S и стрелки независимо для двух игроков."""
        keys = pygame.key.get_pressed()
        left = int(bool(keys[pygame.K_s])) - int(bool(keys[pygame.K_w]))
        right = (
            int(bool(keys[pygame.K_DOWN]))
            - int(bool(keys[pygame.K_UP]))
        )
        return left, right

    def _check_wall_collision(self):
        """Отражает шарик от верхней и нижней границы арены."""
        if self.ball.center_y - self.ball.radius <= COURT_TOP + 11:
            self.ball.center_y = COURT_TOP + 11 + self.ball.radius
            self.ball.velocity_y = abs(self.ball.velocity_y)
            self._spawn_sparks(
                (self.ball.center_x, self.ball.center_y), CYAN, 5,
            )
            self.sounds.play("wall")
        elif self.ball.center_y + self.ball.radius >= COURT_BOTTOM - 9:
            self.ball.center_y = COURT_BOTTOM - 9 - self.ball.radius
            self.ball.velocity_y = -abs(self.ball.velocity_y)
            self._spawn_sparks(
                (self.ball.center_x, self.ball.center_y), PINK, 5,
            )
            self.sounds.play("wall")

    def _bounce(self, paddle, rightwards):
        """Отражает шарик от ракетки с учётом точки столкновения."""
        if not self.ball.rect.colliderect(paddle.rect):
            return
        if rightwards and self.ball.velocity_x >= 0:
            return
        if not rightwards and self.ball.velocity_x <= 0:
            return
        if rightwards:
            self.ball.center_x = paddle.rect.right + self.ball.radius
        else:
            self.ball.center_x = paddle.rect.left - self.ball.radius
        contact = (
            (self.ball.center_y - paddle.rect.centery)
            / (paddle.rect.height / 2)
        )
        speed = min(
            MAX_BALL_SPEED,
            math.hypot(self.ball.velocity_x, self.ball.velocity_y) * 1.06,
        )
        self.ball.velocity_x, self.ball.velocity_y = paddle_reflection(
            contact, speed, 1 if rightwards else -1,
        )
        # Небольшой вертикальный разброс не даёт застревать на одной оси.
        if abs(self.ball.velocity_y) < 58:
            self.ball.velocity_y = 58 if contact >= 0 else -58
        paddle.impact_flash = 1.0
        self._spawn_sparks(
            (self.ball.center_x, self.ball.center_y),
            CYAN if rightwards else PINK, 18,
        )
        self.sounds.play("paddle")

    def _check_paddle_collision(self):
        """Проверяет столкновения с двумя ракетками."""
        self._bounce(self.left_paddle, True)
        self._bounce(self.right_paddle, False)

    def _award_point(self, player):
        """Начисляет очко и запускает новую подачу."""
        if player == 1:
            self.left_score += 1
            tint = CYAN
        else:
            self.right_score += 1
            tint = PINK
        self._spawn_sparks((WIDTH / 2, HEIGHT / 2), tint, 34)
        self.sounds.play("score")
        if self.left_score >= self.WIN_SCORE:
            self.winner = 1
        elif self.right_score >= self.WIN_SCORE:
            self.winner = 2
        if self.winner:
            self.is_finished = True
            self.sounds.play("win")
            self.ball.velocity_x = 0
            self.ball.velocity_y = 0
        else:
            self._prepare_serve(-1 if player == 1 else 1)

    def _check_score(self):
        """Проверяет пересечение шариком боковых линий."""
        if self.ball.center_x + self.ball.radius < COURT_LEFT:
            self._award_point(2)
        elif self.ball.center_x - self.ball.radius > COURT_RIGHT:
            self._award_point(1)

    def update(self, dt=1 / 60):
        """Выполняет один кадр игры; на паузе физика отключена."""
        dt = clamp(dt, 0.0, 0.035)
        if self.is_paused or self.is_finished:
            return
        self.elapsed += dt
        self._update_particles(dt)
        left, right = self._player_input()
        self.left_paddle.move(left, dt)
        self.right_paddle.move(right, dt)
        if self.serve_timer > 0:
            self.serve_timer -= dt
            if self.serve_timer <= 0:
                self.ball.serve(
                    self.serve_direction, random.uniform(-.33, .33),
                )
            return
        # Физические подшаги предотвращают проскок сквозь ракетки.
        steps = max(1, math.ceil(dt / (1 / 180)))
        part = dt / steps
        for _ in range(steps):
            self.ball.move(part)
            self._check_wall_collision()
            self._check_paddle_collision()
            self._check_score()
            if self.serve_timer > 0 or self.is_finished:
                break
