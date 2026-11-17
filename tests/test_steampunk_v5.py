"""Проверки слингов, датчиков ускорения и пассивных флипперов."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.config import BALL_RADIUS, STEP  # noqa: E402
from src.pinball.mechanisms import LaneSensor  # noqa: E402


class TestStage5Fixes(unittest.TestCase):
    """Проверяет устойчивость шарика возле нижних механизмов."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    @staticmethod
    def _point_segment_distance(point, start, end):
        """Вычисляет расстояние от точки до отрезка."""
        edge = end - start
        scale = max(0.0, min(1.0, (
            (point - start).dot(edge) / edge.length_squared()
        )))
        return (point - (start + edge * scale)).length()

    def test_slings_are_smaller_and_clear_of_side_guides(self):
        """Проверяет зазор между слингами и направляющими."""
        game = PinballGame()
        self.assertEqual(len(game.slingshots), 2)
        for sling in game.slingshots:
            xs = [v.x for v in sling.vertices]
            ys = [v.y for v in sling.vertices]
            self.assertLessEqual(max(xs) - min(xs), 45)
            self.assertLessEqual(max(ys) - min(ys), 50)
            relevant = [r for r in game.rails if r.a.y >= 500]
            for rail in relevant:
                gap = min(self._point_segment_distance(
                    vertex, rail.a, rail.b
                ) for vertex in sling.vertices)
                self.assertGreater(gap, 2 * BALL_RADIUS + 18)

    def test_slings_do_not_force_a_high_velocity_launch(self):
        """Проверяет ограничение силы отскока от слинга."""
        game = PinballGame()
        for sling in game.slingshots:
            with self.subTest(direction=sling.direction):
                top = sling.vertices[0]
                ball = Ball()
                ball.mode = "play"
                ball.position = pygame.Vector2(top.x, top.y - 10)
                ball.velocity = pygame.Vector2(0, 280)
                self.assertEqual(sling.hit(ball), sling.points)
                self.assertLess(ball.velocity.y, -150)
                self.assertGreater(ball.velocity.y, -360)
                self.assertEqual(sling.hit(ball), 0)

    def test_rollover_steers_without_teleporting_the_ball(self):
        """Проверяет ускорение без скачка координат."""
        lane = LaneSensor(430, 305)
        ball = Ball()
        ball.mode = "play"
        ball.position = pygame.Vector2(lane.center)
        ball.velocity = pygame.Vector2(-200, 150)
        old_position = ball.position.copy()
        self.assertEqual(lane.hit(ball), 175)
        self.assertEqual((ball.position - old_position).length_squared(), 0)
        self.assertGreater(ball.velocity.x, 0)
        self.assertLess(ball.velocity.y, 0)
        self.assertGreater(ball.velocity.length(), 250)
        self.assertEqual(lane.hit(ball), 0)
        lane.update(1.1)
        ball.position.update(500, 500)
        lane.hit(ball)
        ball.position.update(430, 305)
        self.assertEqual(lane.hit(ball), 175)

    def test_rollover_pair_participates_in_game_scoring(self):
        """Проверяет очки от обоих датчиков."""
        game = PinballGame()
        self.assertEqual(len(game.lanes), 2)
        game.status = "playing"
        game.ball.mode = "play"
        for lane in game.lanes:
            game.ball.position = lane.center.copy()
            game.ball.velocity = pygame.Vector2(0, 0)
            game._physics_step(STEP)
        self.assertGreaterEqual(game.score, 2 * 175)

    def test_passive_flipper_does_not_guarantee_an_upward_kick(self):
        """Проверяет слабый отскок от неподвижного флиппера."""
        game = PinballGame()
        flipper = game.left_flipper
        start, end = flipper.endpoints()
        midpoint = start + (end - start) * 0.50
        ball = Ball()
        ball.mode = "play"
        ball.position = midpoint + pygame.Vector2(0, -20)
        ball.velocity = pygame.Vector2(0, 80)
        self.assertTrue(flipper.hit(ball))
        self.assertGreater(ball.velocity.y, -200)

    def test_no_key_input_reaches_a_drain_near_slings(self):
        """Проверяет возможность слива без нажатий."""
        for x, y in ((512, 572), (744, 572), (500, 640), (759, 640)):
            with self.subTest(x=x, y=y):
                game = PinballGame()
                game.status = "playing"
                game.ball.mode = "play"
                game.ball.position = pygame.Vector2(x, y)
                game.ball.velocity = pygame.Vector2(0, 280)
                for _ in range(12 * 240):
                    game._physics_step(STEP)
                    if game.status != "playing":
                        break
                self.assertEqual(game.status, "ready")
                self.assertEqual(game.lives, 2)


if __name__ == "__main__":
    unittest.main()
