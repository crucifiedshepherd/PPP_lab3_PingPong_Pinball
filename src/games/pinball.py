"""Отдельный запуск Pinball для проверки и отладки."""

import pygame

from src.pinball.config import (
    BALL_RADIUS, BOTTOM, FPS, HEIGHT, RED, TEAL, WIDTH,
)
from src.pinball.game import PinballGame
from src.pinball.objects import Ball, Bumper, Flipper, Rail, Standup


def main():
    """Запускает игровое окно без общего меню проекта."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pinball Arcade")
    clock = pygame.time.Clock()
    game = PinballGame()
    running = True

    while running:
        # В игровую физику передаём время кадра в секундах.
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle_event(event)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
