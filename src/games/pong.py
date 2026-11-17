
"""Логика игры Ping-Pong."""

import pygame


class Paddle:
    """Игровая ракетка одного из игроков."""

    WIDTH = 15
    HEIGHT = 100
    SPEED = 7
    COLOR = (255, 255, 255)

    def __init__(self, x, y):
        """Создает ракетку в заданной позиции."""
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)

    def move(self, direction, field_height):
        """Перемещает ракетку в пределах игрового поля."""
        self.rect.y += direction * self.SPEED
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(field_height, self.rect.bottom)

    def draw(self, screen):
        """Отрисовывает ракетку."""
        pygame.draw.rect(screen, self.COLOR, self.rect)


class Ball:
    """Мяч и его движение по игровому полю."""

    SIZE = 16
    SPEED_X = 5
    SPEED_Y = 5
    COLOR = (255, 255, 255)

    def __init__(self, x, y):
        """Создает мяч в заданной позиции."""
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = (x, y)
        self.speed_x = self.SPEED_X
        self.speed_y = self.SPEED_Y

    def move(self):
        """Перемещает мяч согласно его скорости."""
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y

    def bounce_vertical(self):
        """Изменяет вертикальное направление движения мяча."""
        self.speed_y *= -1

    def bounce_horizontal(self):
        """Изменяет горизонтальное направление движения мяча."""
        self.speed_x *= -1

    def reset(self, center_x, center_y, direction):
        """Возвращает мяч в центр и задает направление движения."""
        self.rect.center = (center_x, center_y)
        self.speed_x = self.SPEED_X * direction
        self.speed_y = self.SPEED_Y

    def draw(self, screen):
        """Отрисовывает мяч."""
        pygame.draw.rect(screen, self.COLOR, self.rect)


class PongGame:
    """Управляет игровым процессом Ping-Pong."""

    WIN_SCORE = 5

    BACKGROUND_COLOR = (0, 0, 0)
    TEXT_COLOR = (255, 255, 255)

    def __init__(self, screen):
        """Инициализирует игровое поле, ракетки, мяч и счет."""
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.left_paddle = Paddle(
            30,
            self.height // 2 - Paddle.HEIGHT // 2,
        )
        self.right_paddle = Paddle(
            self.width - 30 - Paddle.WIDTH,
            self.height // 2 - Paddle.HEIGHT // 2,
        )

        self.ball = Ball(self.width // 2, self.height // 2)

        self.left_score = 0
        self.right_score = 0
        self.is_finished = False

        self.font = pygame.font.Font(None, 64)
        self.message_font = pygame.font.Font(None, 48)

    def handle_event(self, event):
        """Обрабатывает события клавиатуры."""
        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_r
            and self.is_finished
        ):
            self.restart()

    def handle_input(self):
        """Обрабатывает управление обеими ракетками."""
        keys = pygame.key.get_pressed()

        left_direction = 0
        right_direction = 0

        if keys[pygame.K_w]:
            left_direction = -1
        elif keys[pygame.K_s]:
            left_direction = 1

        if keys[pygame.K_UP]:
            right_direction = -1
        elif keys[pygame.K_DOWN]:
            right_direction = 1

        self.left_paddle.move(left_direction, self.height)
        self.right_paddle.move(right_direction, self.height)

    def update(self):
        """Обновляет состояние игры."""
        if self.is_finished:
            return

        self.handle_input()
        self.ball.move()

        self._check_wall_collision()
        self._check_paddle_collision()
        self._check_score()
        self._check_winner()

    def _check_wall_collision(self):
        """Проверяет столкновение мяча с верхней и нижней стенами."""
        if self.ball.rect.top <= 0:
            self.ball.rect.top = 0
            self.ball.bounce_vertical()

        elif self.ball.rect.bottom >= self.height:
            self.ball.rect.bottom = self.height
            self.ball.bounce_vertical()

    def _check_paddle_collision(self):
        """Проверяет столкновения мяча с ракетками."""
        if (
            self.ball.speed_x < 0
            and self.ball.rect.colliderect(self.left_paddle.rect)
        ):
            self.ball.rect.left = self.left_paddle.rect.right
            self.ball.bounce_horizontal()

        elif (
            self.ball.speed_x > 0
            and self.ball.rect.colliderect(self.right_paddle.rect)
        ):
            self.ball.rect.right = self.right_paddle.rect.left
            self.ball.bounce_horizontal()

    def _check_score(self):
        """Начисляет очки игрокам при пропуске мяча."""
        if self.ball.rect.right < 0:
            self.right_score += 1
            self._reset_ball(1)

        elif self.ball.rect.left > self.width:
            self.left_score += 1
            self._reset_ball(-1)

    def _check_winner(self):
        """Проверяет, достиг ли один из игроков победного счета."""
        if (
            self.left_score >= self.WIN_SCORE
            or self.right_score >= self.WIN_SCORE
        ):
            self.is_finished = True

    def _reset_ball(self, direction):
        """Возвращает мяч в центр после потери очка."""
        self.ball.reset(
            self.width // 2,
            self.height // 2,
            direction,
        )

    def restart(self):
        """Начинает новую партию и обнуляет счет."""
        self.left_score = 0
        self.right_score = 0
        self.is_finished = False

        self.left_paddle.rect.centery = self.height // 2
        self.right_paddle.rect.centery = self.height // 2

        self._reset_ball(1)

    def draw(self):
        """Отрисовывает игровое поле, счет, ракетки и мяч."""
        self.screen.fill(self.BACKGROUND_COLOR)

        pygame.draw.line(
            self.screen,
            self.TEXT_COLOR,
            (self.width // 2, 0),
            (self.width // 2, self.height),
            2,
        )

        self.left_paddle.draw(self.screen)
        self.right_paddle.draw(self.screen)
        self.ball.draw(self.screen)

        left_text = self.font.render(
            str(self.left_score),
            True,
            self.TEXT_COLOR,
        )
        right_text = self.font.render(
            str(self.right_score),
            True,
            self.TEXT_COLOR,
        )

        self.screen.blit(left_text, (self.width // 2 - 80, 30))
        self.screen.blit(right_text, (self.width // 2 + 40, 30))

        if self.is_finished:
            winner = (
                "Player 1 wins!"
                if self.left_score > self.right_score
                else "Player 2 wins!"
            )
            message = self.message_font.render(
                winner,
                True,
                self.TEXT_COLOR,
            )
            message_rect = message.get_rect(
                center=(self.width // 2, self.height // 2),
            )
            self.screen.blit(message, message_rect)

            restart_text = self.message_font.render(
                "Press R to restart",
                True,
                self.TEXT_COLOR,
            )
            restart_rect = restart_text.get_rect(
                center=(self.width // 2, self.height // 2 + 60),
            )
            self.screen.blit(restart_text, restart_rect)
