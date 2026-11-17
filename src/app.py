
"""Основное приложение."""

import pygame

from src.games.pong import PongGame


class App:
    """Управляет окном и главным циклом приложения."""

    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    FPS = 60

    def __init__(self):
        """Инициализирует окно и игровые объекты."""
        pygame.init()

        pygame.display.set_caption("Ping-Pong and Pinball")

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        )

        self.clock = pygame.time.Clock()
        self.is_running = True

        self.game = PongGame(self.screen)

    def run(self):
        """Запускает главный игровой цикл."""
        while self.is_running:
            self._handle_events()
            self._update()
            self._draw()

            self.clock.tick(self.FPS)

        pygame.quit()

    def _handle_events(self):
        """Обрабатывает события приложения и текущей игры."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            else:
                self.game.handle_event(event)

    def _update(self):
        """Обновляет состояние текущей игры."""
        self.game.update()

    def _draw(self):
        """Отрисовывает текущую игру и обновляет экран."""
        self.game.draw()
        pygame.display.flip()
