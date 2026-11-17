"""Физические объекты игрового поля и их отрисовка."""

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
    """Хранит положение, скорость и состояние игрового шарика."""

    def __init__(self):
        """Создаёт шарик в пусковом канале."""
        self.radius = BALL_RADIUS
        self.position = pygame.Vector2(LAUNCH_X, LAUNCH_Y)
        self.velocity = pygame.Vector2(0, 0)
        self.mode = "ready"
        self.power = 0.0
        self.entry_t = 0.0
        self.trail = []

    def reset(self):
        """Возвращает шарик в исходное положение."""
        self.position.update(LAUNCH_X, LAUNCH_Y)
        self.velocity.update(0, 0)
        self.mode = "ready"
        self.entry_t = 0.0
        self.trail.clear()

    def launch(self, power):
        """Запускает шарик с силой, зависящей от заряда."""
        self.power = max(0.0, min(1.0, power))
        # Даже небольшой заряд выводит шарик на поле; полный ускоряет его.
        self.velocity.update(0, -(850 + 330 * self.power))
        self.mode = "lane"
        self.entry_t = 0.0
        self.trail.clear()

    def cap_speed(self):
        """Ограничивает скорость шарика допустимым значением."""
        length_sq = self.velocity.length_squared()
        if length_sq > TOP_SPEED * TOP_SPEED:
            self.velocity.scale_to_length(TOP_SPEED)

    @staticmethod
    def entry_point(progress):
        """Вычисляет точку на кривой выхода из пускового канала."""
        t = max(0.0, min(1.0, progress))
        points = ((LAUNCH_X, 128), (987, 159),
                  (927, 221), (861, 242))
        start, c1, c2, end = (pygame.Vector2(p) for p in points)
        u = 1.0 - t
        return (start * (u ** 3) + c1 * (3 * u * u * t)
                + c2 * (3 * u * t * t) + end * (t ** 3))

    def advance(self, dt):
        """Перемещает шарик и применяет гравитацию."""
        if self.mode not in ("lane", "entry", "play"):
            return

        if self.mode == "entry":
            # До выхода на поле шарик движется по заданной кривой.
            self.entry_t = min(1.0, self.entry_t + dt / 0.28)
            self.position = self.entry_point(self.entry_t)
            if self.entry_t >= 1.0:
                self.mode = "play"
                # Заряд определяет скорость при переходе к обычной физике.
                self.velocity.update(
                    -170 - 280 * self.power,
                    170 - 270 * self.power,
                )
            return

        # После выхода на поле на шарик действует гравитация.
        self.velocity.y += GRAVITY * dt
        if self.mode == "play":
            self.cap_speed()
        self.position += self.velocity * dt

        if self.mode == "lane":
            self.position.x = LAUNCH_X
            if self.position.y <= 128:
                # Выход начинается с конца траектории без скачка координат.
                self.mode = "entry"
                self.entry_t = 0.0
                self.position = self.entry_point(0.0)
            return

        if self.position.x - self.radius < LEFT:
            self.position.x = LEFT + self.radius
            self.velocity.x = abs(self.velocity.x) * 0.91
        if self.position.x + self.radius > RIGHT:
            self.position.x = RIGHT - self.radius
            self.velocity.x = -abs(self.velocity.x) * 0.91
        if self.position.y - self.radius < TOP:
            self.position.y = TOP + self.radius
            self.velocity.y = abs(self.velocity.y) * 0.91

    def draw(self, surface):
        """Рисует металлический шарик и след его движения."""
        for index, location in enumerate(self.trail):
            strength = (index + 1) / (len(self.trail) + 1)
            color = (
                int(54 + 58 * strength),
                int(89 + 45 * strength),
                int(106 + 30 * strength),
            )
            pygame.draw.circle(surface, color, pos(location), 3 + index // 3)
        at = pos(self.position)
        pygame.draw.circle(surface, SHADOW, (at[0] + 3, at[1] + 4), 17)
        pygame.draw.circle(surface, METAL, at, self.radius + 1)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 3), 4)


class Rail:
    """Направляющая, отражающая шарик от своего отрезка."""

    def __init__(self, a, b, color=METAL, width=7, bounce=0.82):
        """Создаёт направляющую между двумя точками."""
        self.a = pygame.Vector2(a)
        self.b = pygame.Vector2(b)
        self.color = color
        self.width = width
        self.bounce = bounce

    def hit(self, ball):
        """Проверяет столкновение шарика с направляющей."""
        contact = circle_segment(ball, self.a, self.b, self.width)
        if contact is None:
            return False
        nearest, normal, distance, _ = contact
        # Устраняем проникновение шарика внутрь направляющей.
        ball.position = nearest + normal * (distance + 0.2)
        return reflect_velocity(ball.velocity, normal, self.bounce)

    def draw(self, surface):
        """Рисует металлическую направляющую."""
        pygame.draw.line(
            surface, SHADOW, self.a + (2, 3), self.b + (2, 3),
            self.width + 6,
        )
        pygame.draw.line(surface, self.color, self.a, self.b, self.width)
        pygame.draw.line(surface, CREAM, self.a, self.b, 2)


class Flipper:
    """Управляемая ракетка с вращением вокруг шарнира."""

    def __init__(self, x, y, direction, color):
        """Задаёт шарнир, направление и цвет флиппера."""
        self.pivot = pygame.Vector2(x, y)
        self.direction = direction
        self.color = color
        self.length = 112
        self.thickness = 24
        self.lift = 0.0
        self.pressed = False
        self.swinging = False
        self.cooldown = 0.0
        # Событие точного удара хранится только в пределах одного шага.
        self.last_hit_perfect = False
        self.last_hit_fraction = 0.0

    def update(self, dt, pressed):
        """Обновляет угол наклона флиппера."""
        self.pressed = bool(pressed)
        previous = self.lift
        # Флиппер поднимается быстрее, чем опускается.
        change = (15 if self.pressed else -12) * dt
        self.lift = max(0.0, min(1.0, self.lift + change))
        self.swinging = self.lift > previous + 0.00001
        self.cooldown = max(0.0, self.cooldown - dt)

    def endpoints(self):
        """Вычисляет концы физического контура флиппера."""
        radians = math.radians(14 - 51 * self.lift)
        finish = self.pivot + pygame.Vector2(
            self.direction * self.length * math.cos(radians),
            self.length * math.sin(radians),
        )
        return self.pivot, finish

    def hit(self, ball):
        """Обрабатывает удар шарика о движущийся флиппер."""
        # Сбрасываем отметку Perfect Flip перед новой проверкой контакта.
        self.last_hit_perfect = False
        a, b = self.endpoints()
        contact = circle_segment(ball, a, b, self.thickness)
        if contact is None:
            return False
        nearest, normal, limit, fraction = contact
        # Сначала разделяем пересёкшиеся поверхности.
        ball.position = nearest + normal * (limit + 0.35)
        above = ball.position.y <= nearest.y + 4
        incoming = ball.velocity.dot(normal) < 0

        if (above and (self.pressed or self.swinging)
                and self.cooldown <= 0
                and ball.velocity.y > -180):
            # Для Perfect Flip нужен поднимающийся флиппер,
            # контакт ближе к его концу и падающий шарик.
            self.last_hit_fraction = fraction
            self.last_hit_perfect = (
                self.pressed and self.swinging
                and 0.54 <= fraction <= 0.95
                and 0.12 <= self.lift <= 0.94
                and ball.velocity.y > 35
            )
            # Активный взмах передаёт шарику дополнительный импульс.
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

        # Пассивный флиппер отражает шарик слабее активного.
        if incoming:
            # Удерживаемый флиппер не должен постоянно спасать шарик
            # сильным автоматическим подбросом.
            reflect_velocity(ball.velocity, normal, 0.63)
            ball.cap_speed()
            return True
        return False

    def draw(self, surface):
        """Рисует флиппер с шарниром и подсветкой."""
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
    """Круглый бампер с отскоком и начислением очков."""

    def __init__(self, x, y, radius, color, points=100):
        """Задаёт положение, радиус и награду за удар."""
        self.center = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Обновляет подсветку и задержку между попаданиями."""
        self.flash = max(0.0, self.flash - dt)

    def hit(self, ball):
        """Отталкивает шарик и отмечает засчитанный удар."""
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
        # Отскок не должен бесконечно наращивать скорость.
        incoming = ball.velocity.dot(normal)
        ball.velocity -= 1.6 * incoming * normal
        ball.velocity += normal * 115
        ball.cap_speed()
        # Повторное начисление блокируется на время контакта.
        if self.flash > 0:
            return 0
        self.flash = 0.11
        return self.points

    def draw(self, surface):
        """Рисует купол бампера и световой обод."""
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
    """Небольшая мишень с задержкой повторного срабатывания."""

    def __init__(self, x, y, color, points=150):
        """Создаёт мишень с заданным количеством очков."""
        self.center = pygame.Vector2(x, y)
        self.radius = 14
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Уменьшает время подсветки и задержки."""
        self.flash = max(0, self.flash - dt)

    def hit(self, ball):
        """Обрабатывает попадание шарика в мишень."""
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
        # Время подсветки одновременно служит защитой от повторного счёта.
        if self.flash > 0:
            return 0
        self.flash = 0.17
        return self.points

    def draw(self, surface):
        """Рисует мишень и её индикатор."""
        at = pos(self.center)
        pygame.draw.circle(surface, SHADOW, (at[0] + 2, at[1] + 3), 19)
        pygame.draw.circle(surface, METAL, at, 17)
        pygame.draw.circle(surface, CREAM if self.flash else self.color,
                           at, 12)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 4), 3)
