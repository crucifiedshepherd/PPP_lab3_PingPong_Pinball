"""Тесты геометрии отражения и ограничений скорости Pong."""

import math
import unittest

from src.pong.physics import clamp, paddle_reflection


class PongPhysicsTests(unittest.TestCase):
    """Проверяет математическую модель отражения от ракеток."""

    def test_center_hit_bounces_horizontally(self):
        """Удар по центру возвращает шарик горизонтально."""
        vx, vy = paddle_reflection(0, 400, 1)
        self.assertAlmostEqual(vx, 400)
        self.assertAlmostEqual(vy, 0)

    def test_left_paddle_bounces_to_right(self):
        """Левая ракетка направляет шарик вправо."""
        vx, vy = paddle_reflection(.4, 510, 1)
        self.assertGreater(vx, 0)
        self.assertGreater(vy, 0)
        self.assertAlmostEqual(math.hypot(vx, vy), 510)

    def test_right_paddle_bounces_to_left(self):
        """Правая ракетка направляет шарик влево."""
        vx, vy = paddle_reflection(-.7, 450, -1)
        self.assertLess(vx, 0)
        self.assertLess(vy, 0)

    def test_contact_is_limited(self):
        """Выход за край ракетки не даёт угол больше допустимого."""
        a = paddle_reflection(2.4, 500, 1)
        b = paddle_reflection(1.0, 500, 1)
        self.assertEqual(a, b)

    def test_clamp(self):
        """Ограничение скорости и координат работает на границах."""
        self.assertEqual(clamp(-7, 0, 5), 0)
        self.assertEqual(clamp(8, 0, 5), 5)
        self.assertEqual(clamp(3, 0, 5), 3)


if __name__ == "__main__":
    unittest.main()
