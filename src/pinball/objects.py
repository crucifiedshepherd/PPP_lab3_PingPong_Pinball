"""Шарик, флипперы, направляющие и мишени Pinball."""

import math

import pygame

from src.pinball.collisions import (
    circle_segment,
    pos,
    reflect_velocity,
)
from src.pinball.config import (
    BALL_RADIUS, BRASS, CREAM, GRAVITY, LAUNCH_X, LAUNCH_Y,
    LEFT, METAL, RIGHT, SHADOW, TOP, TOP_SPEED,
)


class Ball:
    """Store ball movement, launch state, and motion trail."""

    def __init__(self):
        """Create one ball in its launch trough."""
        self.radius = BALL_RADIUS
        self.position = pygame.Vector2(LAUNCH_X, LAUNCH_Y)
        self.velocity = pygame.Vector2(0, 0)
        self.mode = "ready"
        self.power = 0.0
        self.trail = []

    def reset(self):
        """Place the ball back on the spring without starting it."""
        self.position.update(LAUNCH_X, LAUNCH_Y)
        self.velocity.update(0, 0)
        self.mode = "ready"
        self.trail.clear()

    def launch(self, power):
        """Send the ball up the separate launch lane."""
        self.power = max(0.0, min(1.0, power))
        self.velocity.update(0, -(960 + 150 * self.power))
        self.mode = "lane"
        self.trail.clear()

    def cap_speed(self):
        """Keep the ball fast enough to play but slow enough to follow."""
        length_sq = self.velocity.length_squared()
        if length_sq > TOP_SPEED * TOP_SPEED:
            self.velocity.scale_to_length(TOP_SPEED)

    def advance(self, dt):
        """Integrate gravity, launch lane, and outside walls."""
        if self.mode not in ("lane", "play"):
            return
        # Гравитация изменяет вертикальную составляющую скорости.
        self.velocity.y += GRAVITY * dt
        if self.mode == "play":
            self.cap_speed()
        # Обновляем положение после изменения скорости.
        self.position += self.velocity * dt

        # Из пускового канала шарик попадает в верхнюю часть поля.
        if self.mode == "lane":
            self.position.x = LAUNCH_X
            if self.position.y <= 119:
                # The ball leaves the one-way launch lane above the table.
                self.mode = "play"
                self.position.update(891, 137)
                self.velocity.update(-220 - 140 * self.power, 90)
            return

        # Отражение от левой границы игрового поля.
        if self.position.x - self.radius < LEFT:
            self.position.x = LEFT + self.radius
            self.velocity.x = abs(self.velocity.x) * 0.91
        # Отражение от правой границы.
        if self.position.x + self.radius > RIGHT:
            self.position.x = RIGHT - self.radius
            self.velocity.x = -abs(self.velocity.x) * 0.91
        # Отражение от верхней границы.
        if self.position.y - self.radius < TOP:
            self.position.y = TOP + self.radius
            self.velocity.y = abs(self.velocity.y) * 0.91

    def draw(self, surface):
        """Draw a metal ball, a small shine, and a subtle short trail."""
        for index, location in enumerate(self.trail):
            strength = (index + 1) / (len(self.trail) + 1)
            color = (
                int(54 + 58 * strength),
                int(89 + 45 * strength),
                int(106 + 30 * strength),
            )
            pygame.draw.circle(surface, color, pos(location), 3 + index // 3)
        at = pos(self.position)
        pygame.draw.circle(surface, SHADOW, (at[0] + 3, at[1] + 4), 14)
        pygame.draw.circle(surface, METAL, at, self.radius + 1)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 3), 4)


class Rail:
    """A drawn and collidable section of metal guardrail."""

    def __init__(self, a, b, color=METAL, width=7, bounce=0.82):
        """Remember the exact collision segment."""
        self.a = pygame.Vector2(a)
        self.b = pygame.Vector2(b)
        self.color = color
        self.width = width
        self.bounce = bounce

    def hit(self, ball):
        """Separate the ball and reflect it on an incoming impact."""
        contact = circle_segment(ball, self.a, self.b, self.width)
        if contact is None:
            return False
        nearest, normal, distance, _ = contact
        # Устраняем пересечение шарика с направляющей.
        ball.position = nearest + normal * (distance + 0.2)
        return reflect_velocity(ball.velocity, normal, self.bounce)

    def draw(self, surface):
        """Render the metal guardrail with a shadow and highlight."""
        pygame.draw.line(
            surface, SHADOW, self.a + (2, 3), self.b + (2, 3),
            self.width + 6,
        )
        pygame.draw.line(surface, self.color, self.a, self.b, self.width)
        pygame.draw.line(surface, CREAM, self.a, self.b, 2)


class Flipper:
    """Rotating flipper with reliable capsule contact and an active kick."""

    def __init__(self, x, y, direction, color):
        """Set a left or right hinge and its resting angle."""
        self.pivot = pygame.Vector2(x, y)
        self.direction = direction
        self.color = color
        self.length = 112
        self.thickness = 24
        self.lift = 0.0
        self.pressed = False
        self.swinging = False
        self.cooldown = 0.0

    def update(self, dt, pressed):
        """Move the paddle each physics substep, not once per frame."""
        self.pressed = bool(pressed)
        previous = self.lift
        # Подъём и возврат ракетки происходят с разной скоростью.
        change = (15 if self.pressed else -12) * dt
        self.lift = max(0.0, min(1.0, self.lift + change))
        self.swinging = self.lift > previous + 0.00001
        self.cooldown = max(0.0, self.cooldown - dt)

    def endpoints(self):
        """Return the actual moving collision capsule endpoints."""
        radians = math.radians(14 - 51 * self.lift)
        finish = self.pivot + pygame.Vector2(
            self.direction * self.length * math.cos(radians),
            self.length * math.sin(radians),
        )
        return self.pivot, finish

    def hit(self, ball):
        """Catch a descending ball and kick it into the table.

        Crucially, an active rotating paddle can hit a ball even when the
        latter is not approaching a *stationary* collision normal.
        """
        a, b = self.endpoints()
        contact = circle_segment(ball, a, b, self.thickness)
        if contact is None:
            return False
        nearest, normal, limit, fraction = contact
        # Разделяем соприкоснувшиеся поверхности до расчёта удара.
        ball.position = nearest + normal * (limit + 0.35)
        above = ball.position.y <= nearest.y + 4
        incoming = ball.velocity.dot(normal) < 0

        if (above and (self.pressed or self.swinging)
                and self.cooldown <= 0
                and ball.velocity.y > -180):
            # Timing a swing produces an unmistakable upward shot.
            ball.velocity.x = (
                self.direction * (165 + 220 * fraction)
                + 0.22 * ball.velocity.x
            )
            ball.velocity.y = -min(
                675, max(530, 490 + 220 * fraction),
            )
            self.cooldown = 0.13
            ball.cap_speed()
            return True

        # Пассивный отскок менее сильный, чем активный удар.
        if incoming:
            # A resting paddle can still deflect a ball, with less energy.
            reflect_velocity(ball.velocity, normal, 0.73)
            if above and ball.velocity.y > -215:
                ball.velocity.y = -215
            ball.cap_speed()
            return True
        return False

    def draw(self, surface):
        """Render a physical-looking paddle, tips, hinge, and highlight."""
        a, b = self.endpoints()
        pygame.draw.line(
            surface, SHADOW, a + (3, 5), b + (3, 5),
            self.thickness + 10,
        )
        pygame.draw.line(surface, (67, 75, 84), a, b, self.thickness + 5)
        pygame.draw.line(surface, self.color, a, b, self.thickness)
        for endpoint in (a, b):
            pygame.draw.circle(
                surface, self.color, pos(endpoint), self.thickness // 2,
            )
        pygame.draw.line(surface, CREAM, a, b, 2)
        pygame.draw.circle(surface, SHADOW, pos(a), 10)
        pygame.draw.circle(surface, BRASS, pos(a), 6)


class Bumper:
    """Large spring-loaded pop bumper that awards points on impact."""

    def __init__(self, x, y, radius, color, points=100):
        """Build a circular bumper with a collision radius."""
        self.center = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Fade the temporary hit indicator."""
        self.flash = max(0.0, self.flash - dt)

    def hit(self, ball):
        """Apply a radial reflection and return newly scored points."""
        difference = ball.position - self.center
        radius = self.radius + ball.radius
        squared = difference.length_squared()
        if squared > radius * radius:
            return 0
        normal = (difference / math.sqrt(squared)
                  if squared > 0.0001 else pygame.Vector2(0, -1))
        ball.position = self.center + normal * (radius + 0.5)
        approaching = ball.velocity.dot(normal) < 0
        if not approaching:
            return 0
        # A bumper pushes outward without multiplying speed forever.
        incoming = ball.velocity.dot(normal)
        ball.velocity -= 1.6 * incoming * normal
        ball.velocity += normal * 115
        ball.cap_speed()
        # Не начисляем очки повторно за непрерывный контакт.
        if self.flash > 0:
            return 0
        self.flash = 0.11
        return self.points

    def draw(self, surface):
        """Draw a domed metal bumper, not a hollow neon ring."""
        center = pos(self.center)
        rim = CREAM if self.flash else METAL
        pygame.draw.circle(
            surface, SHADOW, (center[0] + 4, center[1] + 5),
            self.radius + 15,
        )
        pygame.draw.circle(surface, rim, center, self.radius + 9)
        pygame.draw.circle(surface, (59, 78, 91), center, self.radius + 3)
        pygame.draw.circle(surface, self.color, center, self.radius - 2)
        pygame.draw.circle(surface, CREAM,
                           (center[0] - 7, center[1] - 8), 7)
        pygame.draw.circle(surface, (58, 65, 77), center, 7)


class Standup:
    """Small upright physical target with per-hit scoring cooldown."""

    def __init__(self, x, y, color, points=150):
        """Create a compact round target."""
        self.center = pygame.Vector2(x, y)
        self.radius = 14
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Count down the target glow."""
        self.flash = max(0, self.flash - dt)

    def hit(self, ball):
        """Bounce the ball and return points for a fresh contact."""
        difference = ball.position - self.center
        distance_sq = difference.length_squared()
        allowed = self.radius + ball.radius
        if distance_sq >= allowed * allowed:
            return 0
        normal = (difference / math.sqrt(distance_sq)
                  if distance_sq > 0.0001 else pygame.Vector2(0, -1))
        ball.position = self.center + normal * (allowed + 0.3)
        if not reflect_velocity(ball.velocity, normal, 0.8):
            return 0
        # Подсветка одновременно предотвращает повторный счёт.
        if self.flash > 0:
            return 0
        self.flash = 0.17
        return self.points

    def draw(self, surface):
        """Draw a bright stand-up lamp mounted on a metal post."""
        at = pos(self.center)
        pygame.draw.circle(surface, SHADOW, (at[0] + 2, at[1] + 3), 19)
        pygame.draw.circle(surface, METAL, at, 17)
        pygame.draw.circle(surface, CREAM if self.flash else self.color,
                           at, 12)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 4), 3)
