"""Интерактивные элементы: падающие мишени, слинги и датчики."""

import pygame

from src.pinball.collisions import circle_segment, reflect_velocity


class DropTarget:
    """Мишень, опускающаяся после первого засчитанного удара."""

    def __init__(self, x, y, points=200):
        """Создаёт мишень центральной группы."""
        self.center = pygame.Vector2(x, y)
        self.width = 44
        self.thickness = 12
        self.points = points
        self.active = True
        self.flash = 0.0

    def reset(self):
        """Поднимает мишень перед следующим шаром."""
        self.active = True
        self.flash = 0.0

    def update(self, dt):
        """Уменьшает время подсветки после удара."""
        self.flash = max(0.0, self.flash - dt)

    def hit(self, ball):
        """Проверяет попадание и опускает активную мишень."""
        if not self.active:
            return 0
        half = self.width * 0.5
        a = self.center + (-half, 0)
        b = self.center + (half, 0)
        contact = circle_segment(ball, a, b, self.thickness)
        if contact is None:
            return 0
        nearest, normal, limit, _ = contact
        # Неподвижный или удаляющийся шарик не засчитывает попадание.
        if ball.velocity.dot(normal) >= 0:
            return 0
        ball.position = nearest + normal * (limit + 0.35)
        reflect_velocity(ball.velocity, normal, 0.82)
        ball.cap_speed()
        self.active = False
        self.flash = 0.32
        return self.points


class Slingshot:
    """Треугольная пружинная пластина с физическим контуром."""

    def __init__(self, vertices, direction, points=125):
        """Создаёт треугольную пластину с направлением отскока."""
        self.vertices = tuple(pygame.Vector2(point) for point in vertices)
        self.center = sum(self.vertices, pygame.Vector2()) / 3
        self.direction = direction
        self.points = points
        self.flash = 0.0
        self.cooldown = 0.0
        self.thickness = 8

    def update(self, dt):
        """Обновляет подсветку и задержку повторного начисления."""
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)

    def _inside(self, point):
        """Проверяет положение шарика внутри треугольника."""
        signs = []
        for index in range(3):
            a = self.vertices[index]
            b = self.vertices[(index + 1) % 3]
            edge = b - a
            offset = point - a
            signs.append(edge.x * offset.y - edge.y * offset.x)
        return all(v >= 0 for v in signs) or all(v <= 0 for v in signs)

    def hit(self, ball):
        """Отражает шарик от пластины с ограниченным импульсом."""
        nearest_contact = None
        minimum_distance = float("inf")
        inside = self._inside(ball.position)
        for index in range(3):
            a = self.vertices[index]
            b = self.vertices[(index + 1) % 3]
            edge = b - a
            along = max(
                0.0,
                min(
                    1.0,
                    (ball.position - a).dot(edge) / edge.length_squared(),
                ),
            )
            nearest = a + edge * along
            distance_sq = (ball.position - nearest).length_squared()
            if distance_sq < minimum_distance:
                minimum_distance = distance_sq
                nearest_contact = (a, b, nearest)

        limit = ball.radius + self.thickness * 0.5
        if minimum_distance > limit * limit and not inside:
            return 0

        a, b, nearest = nearest_contact
        edge = b - a
        normal = pygame.Vector2(-edge.y, edge.x).normalize()
        if normal.dot(nearest - self.center) < 0:
            normal = -normal

        approaching = ball.velocity.dot(normal) < -1.0
        ball.position = nearest + normal * (limit + 0.4)
        if not approaching and not inside:
            return 0

        # На задержке контакт сохраняется, но энергия отскока меньше.
        if self.cooldown > 0:
            reflect_velocity(ball.velocity, normal, 0.33)
            ball.velocity *= 0.88
            return 0

        downwards = ball.velocity.y > 70
        incoming_y = ball.velocity.y
        reflect_velocity(ball.velocity, normal, 0.42)
        if downwards:
            # Направляем шарик к своему флипперу, избегая цикла между слингами.
            ball.velocity.x = (
                -self.direction *
                min(255, max(165, abs(ball.velocity.x) * 0.40 + 155))
            )
            ball.velocity.y = -min(
                300, max(205, incoming_y * 0.48 + 105),
            )
        else:
            ball.velocity.x = (
                ball.velocity.x * 0.60 - self.direction * 60
            )
            ball.velocity.y *= 0.76
        ball.cap_speed()
        self.flash = 0.16
        self.cooldown = 0.55
        return self.points


class LaneSensor:
    """Датчик, направляющий шарик без твёрдого препятствия."""

    def __init__(self, x, y, points=175):
        """Размещает датчик направленного ускорения."""
        self.center = pygame.Vector2(x, y)
        self.direction = 1 if x < 628 else -1
        self.radius = 22
        self.points = points
        self.flash = 0.0
        self.cooldown = 0.0
        self._inside = False

    def reset(self):
        """Сбрасывает состояние входа и время задержки."""
        self.flash = 0.0
        self.cooldown = 0.0
        self._inside = False

    def update(self, dt):
        """Обновляет подсветку и время между срабатываниями."""
        self.flash = max(0.0, self.flash - dt)
        self.cooldown = max(0.0, self.cooldown - dt)

    def hit(self, ball):
        """Направляет шарик при первом входе в область датчика."""
        near = (ball.position - self.center).length_squared() <= (
            self.radius + ball.radius
        ) ** 2
        if not near:
            self._inside = False
            return 0
        # Запоминаем вход и во время задержки: повторный контакт
        # засчитывается лишь после выхода из области датчика.
        if self._inside:
            return 0
        self._inside = True
        if self.cooldown > 0:
            return 0
        self.flash = 0.30
        self.cooldown = 1.0
        # Датчик направляет шарик внутрь поля и ограничивает скорость.
        # Ускорение действует только при первом входе.
        incoming_speed = ball.velocity.length()
        speed = min(620.0, max(380.0, incoming_speed * 1.16))
        ball.velocity.update(
            self.direction * speed * 0.61,
            -speed * 0.7924,
        )
        ball.cap_speed()
        return self.points
