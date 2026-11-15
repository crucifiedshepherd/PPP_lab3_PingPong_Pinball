
"""Игровой режим Pinball с движением шарика."""

import pygame


# Размеры игрового окна.
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700

# Физические параметры шарика.
BALL_RADIUS = 12
GRAVITY = 780

# Цвета элементов.
BACKGROUND_COLOR = (15, 18, 30)
FIELD_COLOR = (25, 35, 55)
BORDER_COLOR = (80, 200, 255)
BALL_COLOR = (255, 210, 80)
TEXT_COLOR = (255, 255, 255)


class Ball:
    """Описывает шарик и его движение по игровому полю."""

    def __init__(self, x, y):
        """Создаёт шарик с начальными координатами."""
        self.radius = BALL_RADIUS
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(200, -500)

    def reset(self, x, y):
        """Возвращает шарик в начальное положение."""
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(200, -500)

    def update(self, dt, field):
        """Обновляет движение и отскоки от границ поля."""
        # Гравитация увеличивает скорость движения вниз.
        self.velocity.y += GRAVITY * dt

        # Перемещаем шарик с учётом прошедшего времени.
        self.position += self.velocity * dt

        # Столкновение с левой границей.
        if self.position.x - self.radius < field.left:
            self.position.x = field.left + self.radius
            self.velocity.x = abs(self.velocity.x)

        # Столкновение с правой границей.
        if self.position.x + self.radius > field.right:
            self.position.x = field.right - self.radius
            self.velocity.x = -abs(self.velocity.x)

        # Столкновение с верхней границей.
        if self.position.y - self.radius < field.top:
            self.position.y = field.top + self.radius
            self.velocity.y = abs(self.velocity.y)

        # Временный отскок от нижней границы.
        if self.position.y + self.radius > field.bottom:
            self.position.y = field.bottom - self.radius
            self.velocity.y = -abs(self.velocity.y)

    def draw(self, surface):
        """Рисует шарик на поверхности Pygame."""
        center = (
            round(self.position.x),
            round(self.position.y),
        )

        pygame.draw.circle(
            surface,
            BALL_COLOR,
            center,
            self.radius,
        )


class PinballGame:
    """Управляет игровым полем и шариком Pinball."""

    def __init__(self, width=SCREEN_WIDTH, height=SCREEN_HEIGHT):
        """Создаёт игровое поле и основные объекты."""
        self.field = pygame.Rect(
            width // 2 - 280,
            45,
            560,
            height - 90,
        )

        self.ball = Ball(
            self.field.centerx,
            self.field.bottom - 80,
        )

        self.font = pygame.font.Font(None, 32)

    def handle_event(self, event):
        """Обрабатывает нажатия клавиш игрока."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.ball.reset(
                    self.field.centerx,
                    self.field.bottom - 80,
                )

    def update(self, dt):
        """Обновляет физику игры."""
        dt = min(dt, 0.05)
        self.ball.update(dt, self.field)

    def draw(self, surface):
        """Отрисовывает игровое поле и шарик."""
        surface.fill(BACKGROUND_COLOR)

        pygame.draw.rect(
            surface,
            FIELD_COLOR,
            self.field,
            border_radius=15,
        )

        pygame.draw.rect(
            surface,
            BORDER_COLOR,
            self.field,
            width=4,
            border_radius=15,
        )

        self.ball.draw(surface)

        title = self.font.render(
            "PINBALL - Press R to restart",
            True,
            TEXT_COLOR,
        )

        surface.blit(title, (20, 10))


def main():
    """Запускает отдельную демонстрацию режима Pinball."""
    pygame.init()

    screen = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT)
    )

    pygame.display.set_caption("Pinball")
    clock = pygame.time.Clock()
    game = PinballGame()

    running = True

    while running:
        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_ESCAPE
            ):
                running = False

            game.handle_event(event)

        game.update(dt)
        game.draw(screen)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
