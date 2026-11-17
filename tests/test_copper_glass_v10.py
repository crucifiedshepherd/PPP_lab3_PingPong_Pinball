"""Проверки множителя очков и меню завершения партии."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.config import HEIGHT, WIDTH  # noqa: E402


class TestCopperGlassTen(unittest.TestCase):
    """Проверяет серию попаданий и экран Game Over."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_three_pop_hits_unlock_nine_second_multiplier(self):
        """Проверяет включение множителя за три удара по бамперам."""
        game = PinballGame()
        game._award(100, source="pop")
        game._award(100, source="pop")
        self.assertEqual(game.pop_chain, 2)
        self.assertEqual(game.combo_remaining, 0)
        game._award(100, source="pop")
        self.assertEqual(game.combo_remaining, 9.0)
        self.assertEqual(game.pop_chain, 0)
        self.assertEqual(game.score, 400)
        game._award(150)
        self.assertEqual(game.score, 700)

    def test_other_hit_resets_incomplete_chain(self):
        """Проверяет прерывание серии другим попаданием."""
        game = PinballGame()
        game._award(100, source="pop")
        game._award(150)
        self.assertEqual(game.pop_chain, 0)
        game._award(100, source="pop")
        self.assertEqual(game.pop_chain, 1)
        self.assertEqual(game.combo_remaining, 0.0)

    def test_game_restart_resets_combo_and_animation(self):
        """Проверяет сброс множителя при перезапуске."""
        game = PinballGame()
        for _ in range(3):
            game._award(100, source="pop")
        game.status = "over"
        game.game_over_elapsed = 5.0
        game.restart()
        self.assertEqual(game.combo_remaining, 0)
        self.assertEqual(game.pop_chain, 0)
        self.assertEqual(game.game_over_elapsed, 0)
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.status, "ready")

    def test_game_over_buttons_have_separate_hitboxes(self):
        """Проверяет раздельные области трёх кнопок меню."""
        regions = PinballGame.end_buttons()
        self.assertEqual(set(regions), {"restart", "menu", "quit"})
        prev = None
        for name in ("restart", "menu", "quit"):
            rect = regions[name]
            self.assertGreater(rect.x, 320)
            self.assertLess(rect.right, 950)
            self.assertLess(rect.bottom, HEIGHT)
            if prev is not None:
                self.assertGreater(rect.x, prev.right)
            prev = rect

    def test_restart_button_works_with_mouse(self):
        """Проверяет перезапуск партии по клику мыши."""
        game = PinballGame()
        game.status = "over"
        game.lives = 0
        game.score = 5700
        button = game.end_buttons()["restart"]
        result = game._on_end_click(button.center)
        self.assertEqual(result, "restart")
        self.assertEqual(game.status, "ready")
        self.assertEqual(game.lives, 3)
        self.assertEqual(game.score, 0)

    def test_menu_button_is_inactive_until_shared_app_ready(self):
        """Проверяет отключённое состояние общего меню."""
        game = PinballGame()
        game.status = "over"
        button = game.end_buttons()["menu"]
        result = game._on_end_click(button.center)
        self.assertIsNone(result)
        self.assertEqual(game.status, "over")

    def test_quit_button_requests_window_close(self):
        """Проверяет отправку события закрытия окна."""
        game = PinballGame()
        game.status = "over"
        button = game.end_buttons()["quit"]
        with patch.object(pygame.event, "post", create=True) as post:
            self.assertEqual(game._on_end_click(button.center), "quit")
            self.assertTrue(game.quit_requested)
            post.assert_called_once()

    def test_overlay_draws_at_native_and_shared_window_sizes(self):
        """Проверяет масштабирование экрана завершения партии."""
        game = PinballGame()
        game.status = "over"
        game.game_over_elapsed = 1.8
        for size in ((WIDTH, HEIGHT), (1000, 700)):
            game.draw(pygame.Surface(size))

    def test_return_tube_is_short_and_continuous(self):
        """Проверяет непрерывную кривую выхода шарика."""
        previous = Ball.entry_point(0)
        for index in range(1, 241):
            current = Ball.entry_point(index / 240)
            self.assertLess((current - previous).length(), 3)
            previous = current
        self.assertLess(previous.x, 875)
        self.assertGreater(previous.y, 235)


if __name__ == "__main__":
    unittest.main()
