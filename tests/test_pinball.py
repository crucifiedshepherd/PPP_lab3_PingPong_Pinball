"""Базовые проверки физики и правил Pinball."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import (  # noqa: E402
    BALL_RADIUS,
    BOTTOM,
    RED,
    TEAL,
    Ball,
    Bumper,
    Flipper,
    PinballGame,
    Rail,
    Standup,
)


class TestPinballPhysics(unittest.TestCase):
    """Проверяет запуск, столкновения, очки и завершение партии."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_launch_reaches_playfield(self):
        """Проверяет выход шарика из пускового канала."""
        for power in (0.0, 0.5, 1.0):
            with self.subTest(power=power):
                ball = Ball()
                ball.launch(power)
                for _ in range(400):
                    ball.advance(1 / 240)
                    if ball.mode == "play":
                        break
                self.assertEqual(ball.mode, "play")

    def test_active_left_and_right_flipper(self):
        """Проверяет удары обоими активными флипперами."""
        cases = ((1, 482, RED), (-1, 772, TEAL))
        for direction, x, color in cases:
            with self.subTest(direction=direction):
                flipper = Flipper(x, 710, direction, color)
                flipper.update(1 / 240, True)
                start, end = flipper.endpoints()
                contact_point = start + (end - start) * 0.50
                ball = Ball()
                ball.mode = "play"
                ball.position = pygame.Vector2(
                    contact_point.x, contact_point.y - 18
                )
                ball.velocity = pygame.Vector2(0, 480)
                for _ in range(20):
                    flipper.update(1 / 240, True)
                    ball.advance(1 / 240)
                    flipper.hit(ball)
                    if ball.velocity.y < 0:
                        break
                self.assertLess(ball.velocity.y, 0)

    def test_rail_reflects_a_ball(self):
        """Проверяет отражение шарика от направляющей."""
        rail = Rail((400, 450), (650, 450))
        ball = Ball()
        ball.mode = "play"
        ball.position = pygame.Vector2(500, 441)
        ball.velocity = pygame.Vector2(0, 230)
        self.assertTrue(rail.hit(ball))
        self.assertLess(ball.velocity.y, 0)

    def test_bumper_awards_once_per_contact(self):
        """Проверяет задержку начисления очков у бампера."""
        bumper = Bumper(500, 250, 30, TEAL)
        ball = Ball()
        ball.mode = "play"
        ball.position = pygame.Vector2(500, 215)
        ball.velocity = pygame.Vector2(0, 300)
        self.assertEqual(bumper.hit(ball), 100)
        self.assertEqual(bumper.hit(ball), 0)

    def test_target_awards_points(self):
        """Проверяет отражение и награду за попадание в мишень."""
        target = Standup(550, 400, RED, points=150)
        ball = Ball()
        ball.position = pygame.Vector2(550, 380)
        ball.velocity = pygame.Vector2(0, 200)
        self.assertEqual(target.hit(ball), 150)

    def test_ball_drain_consumes_life(self):
        """Проверяет потерю шара при попадании в слив."""
        game = PinballGame()
        game.status = "playing"
        game.ball.mode = "play"
        game.ball.position = pygame.Vector2(625, BOTTOM + BALL_RADIUS + 5)
        game.ball.velocity = pygame.Vector2(0, 200)
        game._physics_step(1 / 240)
        self.assertEqual(game.lives, 2)
        self.assertEqual(game.status, "ready")

    def test_last_ball_ends_game(self):
        """Проверяет завершение партии после третьего шара."""
        game = PinballGame()
        game.lives = 1
        game.status = "playing"
        game.ball.mode = "play"
        game.ball.position = pygame.Vector2(625, BOTTOM + BALL_RADIUS + 5)
        game.ball.velocity = pygame.Vector2(0, 200)
        game._physics_step(1 / 240)
        self.assertEqual(game.lives, 0)
        self.assertEqual(game.status, "over")

    def test_restart_resets_match(self):
        """Проверяет восстановление начального состояния игры."""
        game = PinballGame()
        game.score = 1400
        game.lives = 0
        game.restart()
        self.assertEqual(game.score, 0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.ball.mode, "ready")

    def test_draw_is_compatible_with_shared_window(self):
        """Проверяет отрисовку в окне общего приложения."""
        game = PinballGame()
        surface = pygame.Surface((1000, 700))
        game.draw(surface)
        self.assertEqual(surface.get_size(), (1000, 700))


if __name__ == "__main__":
    unittest.main()
