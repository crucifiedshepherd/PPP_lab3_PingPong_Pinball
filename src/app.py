"""Основное приложение."""

import pygame


class App:
    """Управляет окном и главным циклом приложения."""

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    FPS = 60

    def __init__(self):
        """Инициализирует окно и необходимые объекты."""
        pygame.init()

        pygame.display.set_caption("Ping-Pong and Pinball")

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.is_running = True

    def run(self):
        """Запускает главный игровой цикл."""
        while self.is_running:
            self._handle_events()
            self._update()
            self._draw()

            self.clock.tick(self.FPS)

        pygame.quit()

    def _handle_events(self):
        """Обрабатывает события окна."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False

    def _update(self):
        """Обновляет состояние приложения."""
        pass

    def _draw(self):
        """Отрисовывает содержимое окна."""
        self.screen.fill((0, 0, 0))
        pygame.display.flip()