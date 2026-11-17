"""Проверки управления Pinball при разных раскладках клавиатуры."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402


class TestPinballControls(unittest.TestCase):
    """Проверяет клавиши управления через скан-коды SDL."""

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

    def send(self, event_type, scancode, key=0):
        """Отправляет синтетическое событие нажатия клавиши."""
        event = pygame.event.Event(
            event_type, {"key": key, "scancode": scancode},
        )
        self.game.handle_event(event)
        self.game.update(1 / 60)

    def test_left_flipper_on_russian_layout(self):
        """Проверяет левый флиппер при русской раскладке."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_A)
        self.assertTrue(self.game.left_flipper.pressed)
        self.assertFalse(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_A)
        self.assertFalse(self.game.left_flipper.pressed)

    def test_right_flipper_on_russian_layout(self):
        """Проверяет правый флиппер при русской раскладке."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_D)
        self.assertTrue(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_D)
        self.assertFalse(self.game.right_flipper.pressed)

    def test_arrow_keys(self):
        """Проверяет управление флипперами стрелками."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_LEFT)
        self.send(pygame.KEYDOWN, pygame.KSCAN_RIGHT)
        self.assertTrue(self.game.left_flipper.pressed)
        self.assertTrue(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_LEFT)
        self.assertFalse(self.game.left_flipper.pressed)
        self.assertTrue(self.game.right_flipper.pressed)

    def test_layout_switch_while_pressed(self):
        """Проверяет отпускание клавиши после смены раскладки."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_A, key=pygame.K_a)
        self.send(pygame.KEYUP, pygame.KSCAN_A, key=0)
        self.assertFalse(self.game.left_flipper.pressed)

    def test_escape_menu_replaces_old_pause_and_restart_hotkeys(self):
        """Проверяет управление паузой только через Esc."""
        self.game.status = "playing"
        self.send(pygame.KEYDOWN, pygame.KSCAN_P, key=pygame.K_p)
        self.assertFalse(self.game.menu_open)
        self.send(pygame.KEYDOWN, pygame.KSCAN_R, key=pygame.K_r)
        self.assertEqual(self.game.status, "playing")
        self.send(pygame.KEYDOWN, 41, key=pygame.K_ESCAPE)
        self.assertTrue(self.game.menu_open)
        self.send(pygame.KEYDOWN, 41, key=pygame.K_ESCAPE)
        self.assertFalse(self.game.menu_open)


if __name__ == "__main__":
    unittest.main()
