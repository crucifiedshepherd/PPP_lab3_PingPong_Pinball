"""Проверки ширины сливов и геометрии нижней части стола."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import (  # noqa: E402
    BALL_RADIUS,
    BOTTOM,
    PinballGame,
)


class TestPinballGeometry(unittest.TestCase):
    """Проверяет проходы между флипперами и направляющими."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_center_gap_is_wider_than_ball(self):
        """Проверяет ширину центрального слива."""
        game = PinballGame()
        left_tip = game.left_flipper.endpoints()[1]
        right_tip = game.right_flipper.endpoints()[1]
        free_width = (
            right_tip.x - left_tip.x - game.left_flipper.thickness
        )
        self.assertGreater(free_width, 2 * BALL_RADIUS + 20)

    def test_center_gap_remains_open_while_flippers_rise(self):
        """Проверяет слив при поднятых флипперах."""
        game = PinballGame()
        game.left_flipper.update(0.2, True)
        game.right_flipper.update(0.2, True)
        left_tip = game.left_flipper.endpoints()[1]
        right_tip = game.right_flipper.endpoints()[1]
        free_width = (
            right_tip.x - left_tip.x - game.left_flipper.thickness
        )
        self.assertGreater(free_width, 2 * BALL_RADIUS + 20)

    def test_single_lower_guide_per_side(self):
        """Проверяет число нижних боковых направляющих."""
        game = PinballGame()
        lower = [
            rail for rail in game.rails
            if max(rail.a.y, rail.b.y) > 600
        ]
        self.assertEqual(len(lower), 2)
        self.assertLess(lower[0].a.x, game.left_flipper.pivot.x)
        self.assertGreater(lower[1].a.x, game.right_flipper.pivot.x)

    def test_central_and_side_drains_consume_a_ball(self):
        """Проверяет потерю шара через нижние проходы."""
        for x in (355, 628, 913):
            with self.subTest(x=x):
                game = PinballGame()
                game.status = "playing"
                game.ball.mode = "play"
                game.ball.position = pygame.Vector2(x, 720)
                game.ball.velocity = pygame.Vector2(0, 330)
                for _ in range(250):
                    game._physics_step(1 / 240)
                    if game.status != "playing":
                        break
                self.assertEqual(game.lives, 2)
                self.assertEqual(game.status, "ready")

    def test_ball_leaves_the_previous_side_pockets(self):
        """Проверяет отсутствие застревания у нижних направляющих."""
        for x, y in ((429, 637), (447, 660), (845, 637)):
            with self.subTest(x=x, y=y):
                game = PinballGame()
                game.status = "playing"
                game.ball.mode = "play"
                start = pygame.Vector2(x, y)
                game.ball.position = start.copy()
                game.ball.velocity = pygame.Vector2(0, 80)
                furthest = 0.0
                for _ in range(480):
                    if game.status != "playing":
                        break
                    game._physics_step(1 / 240)
                    distance = (game.ball.position - start).length()
                    furthest = max(furthest, distance)
                self.assertGreater(furthest, 80)

    def test_draw_scales_to_shared_application(self):
        """Проверяет отображение в общем окне игры."""
        game = PinballGame()
        surface = pygame.Surface((1000, 700))
        game.draw(surface)
        self.assertEqual(surface.get_size(), (1000, 700))


if __name__ == "__main__":
    unittest.main()
