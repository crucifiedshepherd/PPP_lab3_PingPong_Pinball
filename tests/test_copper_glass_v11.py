"""Проверки паузы, экранных кнопок и звуковых файлов."""

import os
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402
from src.pinball.config import HEIGHT, WIDTH  # noqa: E402
from src.pinball.sound import SOUND_DIR  # noqa: E402


class TestCopperGlassEleven(unittest.TestCase):
    """Проверяет управление паузой и сохранение игровой логики."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def setUp(self):
        """Создаёт отдельный экземпляр игры для теста."""
        self.game = PinballGame()

    def key(self, name, down=True):
        """Создаёт и отправляет событие нажатия клавиши."""
        self.game.handle_event(pygame.event.Event(
            pygame.KEYDOWN if down else pygame.KEYUP,
            {"key": getattr(pygame, name)},
        ))

    def test_escape_opens_and_closes_pause_without_reset(self):
        """Проверяет паузу без потери текущего счёта."""
        self.game.status = "playing"
        self.game.score = 1250
        initial = self.game.ball.position.copy()
        self.key("K_ESCAPE")
        self.assertTrue(self.game.menu_open)
        self.game.update(0.05)
        self.assertEqual(self.game.ball.position.x, initial.x)
        self.assertEqual(self.game.ball.position.y, initial.y)
        self.key("K_ESCAPE")
        self.assertFalse(self.game.menu_open)
        self.assertEqual(self.game.score, 1250)
        self.assertEqual(self.game.lives, 3)

    def test_old_restart_and_pause_shortcuts_are_inactive(self):
        """Проверяет отсутствие действий у старых сочетаний клавиш."""
        self.game.status = "playing"
        self.game.score = 600
        self.key("K_r")
        self.key("K_p")
        self.assertFalse(self.game.menu_open)
        self.assertEqual(self.game.status, "playing")
        self.assertEqual(self.game.score, 600)

    def test_menu_open_blocks_flipper_and_launch_input(self):
        """Проверяет блокировку управления на паузе."""
        self.game._toggle_menu()
        self.key("K_SPACE")
        self.key("K_a")
        self.assertFalse(self.game.charging)
        self.assertFalse(self.game._held_flipper_keys["left"])

    def test_resume_switch_closes_menu(self):
        """Проверяет продолжение игры по кнопке Resume."""
        self.game.status = "playing"
        self.game.score = 3400
        self.game._toggle_menu()
        self.assertEqual(
            self.game._on_end_click(self.game.resume_button().center),
            "resume",
        )
        self.assertFalse(self.game.menu_open)
        self.assertEqual(self.game.score, 3400)
        self.assertEqual(self.game.status, "playing")

    def test_restart_switch_works_on_pause_screen(self):
        """Проверяет перезапуск из меню паузы."""
        self.game.status = "playing"
        self.game.score = 910
        self.game._toggle_menu()
        self.assertEqual(self.game._on_end_click(
            self.game.end_buttons()["restart"].center), "restart")
        self.assertFalse(self.game.menu_open)
        self.assertEqual(self.game.status, "ready")
        self.assertEqual(self.game.score, 0)

    def test_game_over_overlay_and_pause_overlay_share_window_center(self):
        """Проверяет центрирование обеих модальных панелей."""
        button_row = self.game.end_buttons()
        midpoint = (
            button_row["restart"].x +
            button_row["quit"].right
        ) / 2
        self.assertEqual(midpoint, WIDTH / 2)
        self.assertEqual(self.game.resume_button().center[0], WIDTH / 2)
        for rect in button_row.values():
            self.assertGreater(rect.y, 0)
            self.assertLess(rect.bottom, HEIGHT)

    def test_menu_remains_disabled(self):
        """Проверяет, что переход в общее меню ещё отключён."""
        self.game.status = "playing"
        self.game._toggle_menu()
        self.assertIsNone(self.game._on_end_click(
            self.game.end_buttons()["menu"].center))
        self.assertTrue(self.game.menu_open)

    def test_render_at_native_and_shared_sizes_during_pause(self):
        """Проверяет масштабирование меню паузы."""
        self.game._toggle_menu()
        for size in ((WIDTH, HEIGHT), (1000, 700)):
            self.game.draw(pygame.Surface(size))

    def test_original_sounds_are_valid_pcm_wav(self):
        """Проверяет формат и целостность звуков WAV."""
        names = ("flipper", "launch", "pop", "target", "drain",
                 "combo", "button", "lane")
        for name in names:
            with self.subTest(name=name):
                filename = SOUND_DIR / (name + ".wav")
                self.assertTrue(filename.is_file())
                with wave.open(str(filename), "rb") as audio:
                    self.assertEqual(audio.getnchannels(), 1)
                    self.assertGreater(audio.getnframes(), 1000)
                    self.assertLess(audio.getnframes(), 22050)

    def test_combo_scoring_still_works_after_menu(self):
        """Проверяет сохранение множителя при паузе."""
        self.game.status = "playing"
        for _ in range(3):
            self.game._award(100, source="pop")
        remaining = self.game.combo_remaining
        self.game._toggle_menu()
        self.game.update(0.05)
        self.assertEqual(self.game.combo_remaining, remaining)
        self.game._toggle_menu()
        self.game._award(100)
        self.assertEqual(self.game.score, 600)


if __name__ == "__main__":
    unittest.main()
