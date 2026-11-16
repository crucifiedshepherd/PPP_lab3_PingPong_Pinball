"""Управление партией, начисление очков и физический цикл."""

import math

import pygame

from src.pinball.config import (
    BLUE, BOTTOM, BRASS, HEIGHT, METAL, RED, STEP, TEAL, WIDTH,
)
from src.pinball.objects import Ball, Bumper, Flipper, Rail, Standup
from src.pinball.renderer import PinballRenderer


class PinballGame(PinballRenderer):
    """Управляет игровым состоянием и использует методы визуализации."""

    def __init__(self, width=WIDTH, height=HEIGHT):
        """Create the table, physical objects, HUD, and game state."""
        if not pygame.font.get_init():
            pygame.font.init()
        # Поле рисуется в базовом разрешении и масштабируется отдельно.
        self.scene = pygame.Surface((WIDTH, HEIGHT))
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 33)
        self.font_small = pygame.font.Font(None, 26)
        # Подготавливаем шарик и обе управляемые ракетки.
        self.ball = Ball()
        self.left_flipper = Flipper(482, 710, 1, RED)
        self.right_flipper = Flipper(772, 710, -1, TEAL)
        # Upper arch and one smooth lower guide on each side.
        # The previous paired guides made V-shaped pockets for the ball.
        self.rails = []
        # У арки несколько сегментов, внизу — по одной направляющей.
        route_groups = [
            ([(368, 213), (368, 170), (414, 127), (482, 107),
              (776, 107), (845, 126), (897, 185)], BRASS, 8),
            ([(335, 560), (467, 685)], METAL, 8),
            ([(935, 560), (787, 685)], METAL, 8),
        ]
        for points, color, thickness in route_groups:
            for before, after in zip(points, points[1:]):
                self.rails.append(Rail(before, after, color, thickness))
        # Бамперы дают очки за контакт.
        self.bumpers = [
            Bumper(626, 274, 36, BRASS),
            Bumper(526, 369, 32, RED),
            Bumper(733, 369, 32, TEAL),
        ]
        self._held_flipper_keys = {"left": set(), "right": set()}
        # Небольшие мишени имеют отдельный номинал очков.
        self.targets = [
            Standup(521, 178, BLUE, 150),
            Standup(628, 166, BRASS, 150),
            Standup(736, 178, BLUE, 150),
            Standup(395, 454, RED, 100),
            Standup(865, 454, TEAL, 100),
        ]
        self.restart()

    def restart(self):
        """Reset score and balls while preserving best score."""
        self.best = max(getattr(self, "best", 0),
                        getattr(self, "score", 0))
        self.score = 0
        self.lives = 3
        self.status = "ready"
        self.ball.reset()
        self.charging = False
        self.charge = 0.0
        self.ball_age = 0.0
        self.saver_used = False
        self.message = ""
        self.message_timer = 0.0
        self.left_flipper.lift = 0.0
        self.right_flipper.lift = 0.0

    @staticmethod
    def _flipper_control(event):
        """Identify a flipper by physical key position, not typing layout."""
        scancode = getattr(event, "scancode", None)

        # SDL2 scan codes refer to positions on the physical keyboard.
        # Russian A (Ф) and D (В) share the same positions as Latin A/D.
        if scancode is not None:
            if scancode in (pygame.KSCAN_A, pygame.KSCAN_LEFT):
                return "left"
            if scancode in (pygame.KSCAN_D, pygame.KSCAN_RIGHT):
                return "right"
            return None

        # Compatibility fallback for synthetic events without a scancode.
        if event.key in (pygame.K_a, pygame.K_LEFT):
            return "left"
        if event.key in (pygame.K_d, pygame.K_RIGHT):
            return "right"
        return None

    def handle_event(self, event):
        """Handle input in any keyboard layout using physical key codes."""
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            control = self._flipper_control(event)
            # Удержание отслеживается по физическому коду клавиши.
            if control is not None:
                scancode = getattr(event, "scancode", None)
                key_id = ("scan", scancode) if scancode is not None else (
                    "key", event.key
                )
                held = self._held_flipper_keys[control]
                if event.type == pygame.KEYDOWN:
                    held.add(key_id)
                else:
                    held.discard(key_id)

            # Пробел заряжает пружину, P ставит на паузу, R сбрасывает.
            if event.type == pygame.KEYDOWN:
                physical = getattr(event, "scancode", None)
                if (event.key == pygame.K_r
                        or physical == getattr(pygame, "KSCAN_R", 21)):
                    self.restart()
                elif (event.key == pygame.K_p
                        or physical == getattr(pygame, "KSCAN_P", 19)):
                    if self.status == "playing":
                        self.status = "paused"
                    elif self.status == "paused":
                        self.status = "playing"
                elif (event.key == pygame.K_SPACE
                      or physical == getattr(pygame, "KSCAN_SPACE", 44)):
                    if self.status == "ready":
                        self.charging = True
            # Шарик запускается после отпускания пробела.
            elif event.type == pygame.KEYUP:
                physical = getattr(event, "scancode", None)
                if ((event.key == pygame.K_SPACE
                     or physical == getattr(pygame, "KSCAN_SPACE", 44))
                        and self.charging):
                    self.charging = False
                    if self.status == "ready":
                        self.ball.launch(self.charge)
                        self.status = "playing"
                        self.charge = 0.0

        # Avoid sticky paddles after switching to another application.
        elif event.type == getattr(pygame, "WINDOWFOCUSLOST", None):
            for held in self._held_flipper_keys.values():
                held.clear()

    def _lost_ball(self):
        """Lose a ball, preserving the accumulated score."""
        self.lives -= 1
        if self.lives <= 0:
            self.status = "over"
            self.message = "GAME OVER"
        else:
            self.ball.reset()
            self.status = "ready"
            self.charging = False
            self.charge = 0.0
            self.message = "BALL LOST"
        self.message_timer = 1.2

    def _award(self, points):
        """Add scored points and activate a brief visual cue."""
        if points:
            self.score += points
            self.best = max(self.score, self.best)
            self.message = "+{}".format(points)
            self.message_timer = 0.65

    def _physics_step(self, dt):
        """Resolve one fixed physics step with moving flippers."""
        self.ball.advance(dt)
        if self.ball.mode != "play":
            return
        # Отдельно разрешаем контакты со всеми типами препятствий.
        for rail in self.rails:
            rail.hit(self.ball)
        for bumper in self.bumpers:
            self._award(bumper.hit(self.ball))
        for target in self.targets:
            self._award(target.hit(self.ball))
        # Движущиеся ракетки рассчитываются на том же подшаге.
        self.left_flipper.hit(self.ball)
        self.right_flipper.hit(self.ball)
        self.ball.cap_speed()
        if self.ball.position.y - self.ball.radius > BOTTOM:
            self._lost_ball()

    def update(self, dt):
        """Update controls and simulation using short physics substeps."""
        dt = max(0.0, min(dt, 0.050))
        keys = pygame.key.get_pressed()
        left_down = (
            bool(self._held_flipper_keys["left"])
            or keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        right_down = (
            bool(self._held_flipper_keys["right"])
            or keys[pygame.K_d] or keys[pygame.K_RIGHT]
        )
        if self.status == "paused":
            return
        if self.status == "ready":
            if self.charging:
                self.charge = min(1.0, self.charge + dt / 0.85)
            self.left_flipper.update(dt, left_down)
            self.right_flipper.update(dt, right_down)
            return
        if self.status != "playing":
            return
        self.ball_age += dt
        self.message_timer = max(0.0, self.message_timer - dt)
        for bumper in self.bumpers:
            bumper.update(dt)
        for target in self.targets:
            target.update(dt)
        # Делим время кадра на короткие подшаги против проскока.
        count = max(1, math.ceil(dt / STEP))
        part = dt / count
        for _ in range(count):
            self.left_flipper.update(part, left_down)
            self.right_flipper.update(part, right_down)
            self._physics_step(part)
            if self.status != "playing":
                break
        # Точки следа сохраняем только при реальном движении по столу.
        if self.status == "playing" and self.ball.mode == "play":
            if (not self.ball.trail or
                    (self.ball.position - self.ball.trail[-1]
                     ).length_squared() > 105):
                self.ball.trail.append(self.ball.position.copy())
                self.ball.trail = self.ball.trail[-6:]
