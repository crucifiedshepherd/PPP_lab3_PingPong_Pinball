"""Запуск Pinball и совместимость с существующими тестами."""

import pygame

from src.pinball.config import (
    BALL_RADIUS, BOTTOM, FPS, HEIGHT, RED, TEAL, WIDTH,
)
from src.pinball.game import PinballGame
from src.pinball.objects import Ball, Bumper, Flipper, Rail, Standup


def main():
    """Run this game alone without changing Vlad's shared entry point."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pinball Arcade")
    clock = pygame.time.Clock()
    game = PinballGame()
    running = True

    while running:
        # Время между кадрами передаётся физике в секундах.
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (event.type == pygame.KEYDOWN
                  and event.key == pygame.K_ESCAPE):
                running = False
            game.handle_event(event)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
