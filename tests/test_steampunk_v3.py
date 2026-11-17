"""Проверки запуска, боковых бамперов и размера игрового окна."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.config import BALL_RADIUS  # noqa: E402


class TestSteampunkStage3(unittest.TestCase):
    """Проверяет базовые механики и визуализацию."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_ball_is_larger(self):
        """Проверяет физический размер шарика."""
        self.assertEqual(BALL_RADIUS, 12)
        self.assertEqual(Ball().radius, 12)

    def test_charge_changes_launch_speed_and_entry(self):
        """Проверяет зависимость запуска от силы заряда."""
        initial = []
        table_entry = []
        for power in (0.0, 0.5, 1.0):
            ball = Ball()
            ball.launch(power)
            initial.append(abs(ball.velocity.y))
            for _ in range(400):
                ball.advance(1 / 240)
                if ball.mode == "play":
                    break
            self.assertEqual(ball.mode, "play")
            table_entry.append((ball.velocity.x, ball.velocity.y))
        self.assertGreater(initial[2] - initial[0], 300)
        self.assertLess(table_entry[2][0], table_entry[0][0] - 250)
        self.assertLess(table_entry[2][1], table_entry[0][1] - 250)

    def test_both_side_bumpers_are_physical(self):
        """Проверяет коллайдеры обоих боковых бамперов."""
        game = PinballGame()
        sides = [bumper for bumper in game.bumpers if bumper.points == 75]
        self.assertEqual(len(sides), 2)
        self.assertLess(sides[0].center.x, 500)
        self.assertGreater(sides[1].center.x, 750)
        for bumper in sides:
            with self.subTest(x=bumper.center.x):
                ball = Ball()
                ball.mode = "play"
                ball.position = (
                    bumper.center + pygame.Vector2(0, -30)
                )
                ball.velocity.update(0, 250)
                self.assertEqual(bumper.hit(ball), 75)
                self.assertLess(ball.velocity.y, 0)

    def test_side_rails_are_real(self):
        """Проверяет физические боковые направляющие."""
        game = PinballGame()
        self.assertTrue(any(
            abs(rail.a.x - 410) < 1 and abs(rail.b.x - 447) < 1
            for rail in game.rails
        ))
        self.assertTrue(any(
            abs(rail.a.x - 844) < 1 and abs(rail.b.x - 807) < 1
            for rail in game.rails
        ))

    def test_render_at_both_window_sizes(self):
        """Проверяет два поддерживаемых разрешения окна."""
        game = PinballGame()
        for size in ((1200, 840), (1000, 700)):
            surface = pygame.Surface(size)
            game.draw(surface)
            self.assertEqual(surface.get_size(), size)


if __name__ == "__main__":
    unittest.main()
