"""Игровой режим Pinball: флипперы, бамперы, очки и жизни."""

import math

import pygame


SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
GRAVITY = 420
MAX_BALL_SPEED = 560
BALL_RADIUS = 11
FLIPPER_LENGTH = 100
FLIPPER_WIDTH = 20

BG = (10, 14, 25)
FIELD_BG = (21, 31, 51)
CYAN = (67, 211, 244)
WHITE = (238, 246, 255)
MUTED = (137, 158, 183)
GOLD = (255, 208, 87)
PINK = (255, 104, 145)
GREEN = (76, 234, 167)


def collide_segment(ball, start, end, thickness, bounce=0.85):
    """Разрешает столкновение шарика с утолщённым отрезком."""
    direction = end - start
    length_squared = direction.length_squared()
    if length_squared == 0:
        return False

    along = (ball.position - start).dot(direction) / length_squared
    along = max(0.0, min(1.0, along))
    closest = start + direction * along
    offset = ball.position - closest
    limit = ball.radius + thickness / 2

    if offset.length_squared() >= limit * limit:
        return False

    normal = (
        offset.normalize() if offset.length_squared()
        else pygame.Vector2(0, -1)
    )
    ball.position = closest + normal * (limit + 0.5)
    incoming = ball.velocity.dot(normal)
    if incoming >= 0:
        return False

    ball.velocity -= (1 + bounce) * incoming * normal
    return True


class Ball:
    """Хранит положение, скорость и геометрию шарика."""

    def __init__(self, x, y):
        """Создаёт шарик в стартовой позиции."""
        self.radius = BALL_RADIUS
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)

    def launch(self):
        """Запускает шарик вверх и к центру игрового поля."""
        self.velocity.update(-105, -550)

    def update(self, dt, field):
        """Применяет гравитацию и отскоки от трёх стен."""
        self.velocity.y += GRAVITY * dt
        self.limit_speed()
        self.position += self.velocity * dt

        if self.position.x - self.radius < field.left:
            self.position.x = field.left + self.radius
            self.velocity.x = abs(self.velocity.x) * 0.94
        if self.position.x + self.radius > field.right:
            self.position.x = field.right - self.radius
            self.velocity.x = -abs(self.velocity.x) * 0.94
        if self.position.y - self.radius < field.top:
            self.position.y = field.top + self.radius
            self.velocity.y = abs(self.velocity.y) * 0.94

    def limit_speed(self):
        """Ограничивает скорость для удобного управления."""
        if self.velocity.length_squared() > MAX_BALL_SPEED ** 2:
            self.velocity.scale_to_length(MAX_BALL_SPEED)

    def draw(self, surface):
        """Рисует шарик с небольшим световым бликом."""
        center = (round(self.position.x), round(self.position.y))
        pygame.draw.circle(surface, (96, 76, 46), center, self.radius + 5)
        pygame.draw.circle(surface, GOLD, center, self.radius)
        pygame.draw.circle(surface, WHITE, (center[0] - 3, center[1] - 3), 3)


class Flipper:
    """Ракетка, которой игрок отражает падающий шарик."""

    def __init__(self, x, y, direction):
        """Сохраняет точку крепления и сторону флиппера."""
        self.pivot = pygame.Vector2(x, y)
        self.direction = direction
        self.lift = 0.0
        self.pressed = False

    def update(self, dt, pressed):
        """Плавно поворачивает флиппер при нажатии клавиши."""
        self.pressed = bool(pressed)
        change = 10 * dt if self.pressed else -10 * dt
        self.lift = max(0.0, min(1.0, self.lift + change))

    def endpoints(self):
        """Возвращает координаты начала и конца ракетки."""
        start = self.pivot
        end = self.pivot + pygame.Vector2(
            self.direction * FLIPPER_LENGTH,
            18 - 65 * self.lift,
        )
        return start, end

    def hit(self, ball):
        """При попадании по поднятой ракетке подбрасывает шарик."""
        start, end = self.endpoints()
        if not collide_segment(ball, start, end, FLIPPER_WIDTH):
            return
        if self.pressed:
            # Активный удар намного сильнее обычного отскока.
            ball.velocity.x = (
                self.direction * 220 + ball.velocity.x * 0.2
            )
            ball.velocity.y = -max(450, abs(ball.velocity.y) * 0.80)
            ball.limit_speed()

    def draw(self, surface):
        """Рисует ракетку и круглую ось вращения."""
        start, end = self.endpoints()
        color = GREEN if self.pressed else PINK
        pygame.draw.line(surface, color, start, end, FLIPPER_WIDTH)
        for point in (start, end):
            pygame.draw.circle(
                surface, color, (round(point.x), round(point.y)),
                FLIPPER_WIDTH // 2,
            )
        pygame.draw.circle(
            surface, WHITE, (round(start.x), round(start.y)), 5,
        )


class Bumper:
    """Круглое препятствие, при попадании дающее очки."""

    def __init__(self, x, y, radius, color):
        """Создаёт бампер с заданными координатами и цветом."""
        self.center = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.flash = 0.0

    def update(self, dt):
        """Уменьшает время подсветки после удара."""
        self.flash = max(0.0, self.flash - dt)

    def hit(self, ball):
        """Отбивает шарик и сообщает, начислять ли очки."""
        offset = ball.position - self.center
        limit = ball.radius + self.radius
        if offset.length_squared() >= limit * limit:
            return False

        normal = (
            offset.normalize() if offset.length_squared()
            else pygame.Vector2(0, -1)
        )
        ball.position = self.center + normal * (limit + 1)
        if ball.velocity.dot(normal) >= 0:
            return False

        speed = min(500, max(330, ball.velocity.length() * 0.93))
        ball.velocity = normal * speed
        ball.velocity.y -= 30
        ball.limit_speed()

        gained_points = self.flash == 0
        self.flash = 0.16
        return gained_points

    def draw(self, surface):
        """Отображает бампер и подсветку при столкновении."""
        point = (round(self.center.x), round(self.center.y))
        outer = WHITE if self.flash > 0 else self.color
        pygame.draw.circle(surface, (44, 65, 87), point, self.radius + 10)
        pygame.draw.circle(surface, outer, point, self.radius + 4)
        pygame.draw.circle(surface, FIELD_BG, point, self.radius - 4)
        pygame.draw.circle(surface, self.color, point, self.radius - 10)


class PinballGame:
    """Управляет игровым полем, счётом, жизнями и объектами."""

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        """Создаёт всё необходимое для одного игрового режима."""
        if not pygame.font.get_init():
            pygame.font.init()
        self.field = pygame.Rect(width // 2 - 225, 50, 450, height - 95)
        mid = self.field.centerx
        bottom = self.field.bottom
        self.left_flipper = Flipper(mid - 132, bottom - 63, 1)
        self.right_flipper = Flipper(mid + 132, bottom - 63, -1)
        self.bumpers = [
            Bumper(mid, 205, 31, CYAN),
            Bumper(mid - 94, 312, 27, PINK),
            Bumper(mid + 94, 312, 27, GREEN),
            Bumper(mid, 409, 24, GOLD),
        ]
        # Наклонные направляющие ведут шарик к флипперам.
        self.guides = [
            (
                pygame.Vector2(self.field.left + 14, bottom - 190),
                pygame.Vector2(self.left_flipper.pivot.x - 4, bottom - 73),
            ),
            (
                pygame.Vector2(self.field.right - 14, bottom - 190),
                pygame.Vector2(self.right_flipper.pivot.x + 4, bottom - 73),
            ),
        ]
        # Небольшие отбойники защищают боковые проходы внизу.
        self.saver_y = bottom - 49
        self.side_savers = [
            (self.field.left, self.left_flipper.pivot.x + 16),
            (self.right_flipper.pivot.x - 16, self.field.right),
        ]
        self.saver_flash = [0.0, 0.0]
        self.font_big = pygame.font.Font(None, 58)
        self.font = pygame.font.Font(None, 35)
        self.font_small = pygame.font.Font(None, 27)
        self.restart()

    def restart(self):
        """Начинает новую партию с тремя жизнями."""
        self.score = 0
        self.lives = 3
        self.status = "ready"
        self.saver_flash = [0.0, 0.0]
        self._new_ball()

    def _new_ball(self):
        """Готовит следующий шарик к запуску игроком."""
        self.ball = Ball(self.field.centerx + 105, self.field.bottom - 105)
        self.status = "ready"

    def handle_event(self, event):
        """Обрабатывает запуск шарика и перезапуск игры."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_r:
            self.restart()
        elif event.key == pygame.K_SPACE and self.status == "ready":
            self.ball.launch()
            self.status = "playing"

    def _check_side_savers(self):
        """Отбивает шарик от боковых ловушек у нижнего края."""
        ball = self.ball
        if ball.velocity.y <= 0:
            return
        if ball.position.y + ball.radius < self.saver_y:
            return

        for index, (left, right) in enumerate(self.side_savers):
            if left <= ball.position.x <= right:
                # Центр поднимается над планкой, а импульс идёт
                # вверх и внутрь поля, к соответствующему флипперу.
                ball.position.y = self.saver_y - ball.radius - 1
                inward = 155 if index == 0 else -155
                ball.velocity.update(inward, -455)
                self.saver_flash[index] = 0.18
                return

    def update(self, dt):
        """Обновляет управление и физику несколькими подшагами."""
        dt = min(max(dt, 0.0), 0.05)
        keys = pygame.key.get_pressed()
        self.left_flipper.update(
            dt, keys[pygame.K_a] or keys[pygame.K_LEFT],
        )
        self.right_flipper.update(
            dt, keys[pygame.K_d] or keys[pygame.K_RIGHT],
        )
        for bumper in self.bumpers:
            bumper.update(dt)
        self.saver_flash = [max(0.0, t - dt) for t in self.saver_flash]
        if self.status != "playing":
            return

        # Подшаги помогают не пролетать сквозь тонкие препятствия.
        steps = max(1, math.ceil(dt / (1 / 180)))
        step_dt = dt / steps
        for _ in range(steps):
            self.ball.update(step_dt, self.field)
            for bumper in self.bumpers:
                if bumper.hit(self.ball):
                    self.score += 100
            for start, end in self.guides:
                collide_segment(self.ball, start, end, 10)
            self.left_flipper.hit(self.ball)
            self.right_flipper.hit(self.ball)
            self._check_side_savers()
            if self.ball.position.y - self.ball.radius > self.field.bottom:
                self.lives -= 1
                if self.lives > 0:
                    self._new_ball()
                else:
                    self.status = "over"
                break

    def _text(self, surface, content, x, y, font=None, color=WHITE):
        """Рисует одну строку интерфейса с заданной позиции."""
        used_font = font if font is not None else self.font
        surface.blit(used_font.render(content, True, color), (x, y))

    def _message(self, surface, headline, detail):
        """Выводит сообщение посередине игрового поля."""
        panel = pygame.Surface((360, 108), pygame.SRCALPHA)
        panel.fill((9, 16, 31, 228))
        x = self.field.centerx - 180
        y = self.field.centery - 54
        surface.blit(panel, (x, y))
        title = self.font.render(headline, True, GOLD)
        sub = self.font_small.render(detail, True, WHITE)
        surface.blit(
            title, title.get_rect(center=(self.field.centerx, y + 35))
        )
        surface.blit(sub, sub.get_rect(center=(self.field.centerx, y + 76)))

    def draw(self, surface):
        """Рисует игровое поле, бамперы, флипперы и интерфейс."""
        surface.fill(BG)
        for x in range(0, surface.get_width(), 40):
            pygame.draw.line(
                surface, (16, 23, 37), (x, 0), (x, surface.get_height())
            )
        for y in range(0, surface.get_height(), 40):
            pygame.draw.line(
                surface, (16, 23, 37), (0, y), (surface.get_width(), y)
            )

        pygame.draw.rect(surface, FIELD_BG, self.field, border_radius=20)
        pygame.draw.rect(surface, CYAN, self.field, 4, border_radius=20)
        # Нижняя стенка отсутствует: здесь можно потерять шарик.
        pygame.draw.line(
            surface, FIELD_BG, (self.field.left + 4, self.field.bottom),
            (self.field.right - 4, self.field.bottom), 7,
        )
        for start, end in self.guides:
            pygame.draw.line(surface, CYAN, start, end, 10)
            for point in (start, end):
                pygame.draw.circle(
                    surface, CYAN, (round(point.x), round(point.y)), 5
                )

        # Планки внизу боковых дорожек: шарик больше не
        # проваливается мимо ракеток у самых стен.
        for index, (left, right) in enumerate(self.side_savers):
            color = WHITE if self.saver_flash[index] else GOLD
            pygame.draw.line(
                surface, color,
                (round(left), self.saver_y),
                (round(right), self.saver_y), 7,
            )
            for x in (left, right):
                pygame.draw.circle(
                    surface, color, (round(x), self.saver_y), 4,
                )
        for bumper in self.bumpers:
            bumper.draw(surface)
        self.left_flipper.draw(surface)
        self.right_flipper.draw(surface)
        if self.status != "over":
            self.ball.draw(surface)

        self._text(surface, "PINBALL", 28, 55, self.font_big, CYAN)
        self._text(surface, "ARCADE MODE", 30, 111, self.font_small, MUTED)
        self._text(surface, "SCORE", 30, 194, self.font_small, MUTED)
        self._text(surface, str(self.score), 28, 225, self.font_big, GOLD)
        self._text(surface, "BALLS LEFT", 30, 331, self.font_small, MUTED)
        self._text(surface, str(self.lives), 30, 363, self.font_big, WHITE)

        right = self.field.right + 27
        self._text(surface, "CONTROLS", right, 95, self.font, CYAN)
        self._text(surface, "A / LEFT", right, 156, self.font_small)
        self._text(surface, "Left flipper", right, 184, self.font_small, MUTED)
        self._text(surface, "D / RIGHT", right, 249, self.font_small)
        self._text(
            surface, "Right flipper", right, 277, self.font_small, MUTED
        )
        self._text(surface, "SPACE", right, 343, self.font_small)
        self._text(surface, "Launch ball", right, 371, self.font_small, MUTED)
        self._text(surface, "R", right, 437, self.font_small)
        self._text(
            surface, "Restart match", right, 465, self.font_small, MUTED
        )
        self._text(
            surface, "+100 per bumper", right, 551, self.font_small, GOLD
        )
        self._text(
            surface, "Side savers are active", right, 585,
            self.font_small, MUTED,
        )

        if self.status == "ready":
            self._message(surface, "READY TO PLAY", "Press SPACE to launch")
        elif self.status == "over":
            self._message(surface, "GAME OVER", "Press R to play again")


def main():
    """Запускает Pinball отдельно от общего меню двух игр."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pinball Arcade")
    clock = pygame.time.Clock()
    game = PinballGame()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            game.handle_event(event)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
