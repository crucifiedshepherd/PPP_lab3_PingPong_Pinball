"""Проверки боковых ускорителей и графических ресурсов."""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.mechanisms import LaneSensor  # noqa: E402


class TestSteampunkStage8(unittest.TestCase):
    """Проверяет направляющие датчики и визуальные слои."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_left_and_right_lanes_steer_inward_and_up(self):
        """Проверяет направление движения от обоих датчиков."""
        for x, direction in ((413, 1), (843, -1)):
            with self.subTest(x=x):
                lane = LaneSensor(x, 303)
                ball = Ball()
                ball.mode = "play"
                ball.position.update(x, 303)
                ball.velocity.update(0, 180)
                origin = ball.position.copy()
                self.assertEqual(lane.hit(ball), 175)
                self.assertEqual(ball.position.x, origin.x)
                self.assertEqual(ball.position.y, origin.y)
                self.assertGreater(ball.velocity.x * direction, 0)
                self.assertLess(ball.velocity.y, 0)
                self.assertGreater(ball.velocity.length(), 350)

    def test_boosters_have_entry_gate_and_cooldown(self):
        """Проверяет задержку между ускорениями."""
        lane = LaneSensor(413, 303)
        ball = Ball()
        ball.position.update(413, 303)
        ball.velocity.update(20, 160)
        self.assertEqual(lane.hit(ball), 175)
        previous = ball.velocity.copy()
        for _ in range(10):
            self.assertEqual(lane.hit(ball), 0)
        self.assertEqual(ball.velocity.x, previous.x)
        self.assertEqual(ball.velocity.y, previous.y)
        lane.update(1.1)
        self.assertEqual(lane.hit(ball), 0)

    def test_velocity_is_bounded_even_from_fast_impact(self):
        """Проверяет ограничение скорости после усилителя."""
        lane = LaneSensor(843, 303)
        ball = Ball()
        ball.position.update(843, 303)
        ball.velocity.update(690, 100)
        lane.hit(ball)
        self.assertLessEqual(ball.velocity.length(), 620.1)

    def test_render_assets_preserve_physical_layout(self):
        """Проверяет неизменность расположения коллайдеров."""
        game = PinballGame()
        self.assertEqual(len(game.slingshots), 2)
        self.assertEqual(len(game.drop_targets), 3)
        self.assertEqual(len(game.lanes), 2)
        self.assertEqual([bumper.points for bumper in game.bumpers],
                         [100, 100, 100, 75, 75])

    def test_background_and_panels_exist_as_real_images(self):
        """Проверяет наличие фоновых изображений и панелей."""
        from src.pinball.sprites import ASSET_DIR
        for name in ("table_backdrop.png", "hud_left.png",
                     "hud_right.png"):
            with self.subTest(name=name):
                self.assertTrue((Path(ASSET_DIR) / name).is_file())


if __name__ == "__main__":
    unittest.main()
