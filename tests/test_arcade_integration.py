"""Проверки экранов меню и переключения Pong и Pinball."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError:
    pygame = None


@unittest.skipIf(pygame is None, "Для проверки интерфейса нужен Pygame")
class ArcadeIntegrationTests(unittest.TestCase):
    """Проверяет управляющие флаги и меню без запуска главного цикла."""

    @classmethod
    def setUpClass(cls):
        """Создаёт окно в тестовом видеорежиме."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает окно тестового режима."""
        pygame.quit()

    def setUp(self):
        """Создаёт приложение для отдельного теста."""
        from src.app import App
        self.app = App()

    def test_starts_in_menu(self):
        """Приложение сначала показывает экран выбора игры."""
        self.assertEqual(self.app.mode, "menu")
        self.assertIsNone(self.app.game)

    def test_open_pong_and_return(self):
        """Режим Pong корректно открывается и возвращается в меню."""
        self.app._start_game("pong")
        self.assertEqual(self.app.mode, "pong")
        self.assertEqual(self.app.screen.get_size(), (1200, 800))
        self.app.game.menu_requested = True
        self.app._check_game_requests()
        self.assertEqual(self.app.mode, "menu")

    def test_open_pinball_and_return(self):
        """Режим Pinball может вернуться в меню без закрытия окна."""
        self.app._start_game("pinball")
        self.assertEqual(self.app.mode, "pinball")
        self.assertEqual(self.app.screen.get_size(), (1200, 840))
        self.app.game.menu_requested = True
        self.app._check_game_requests()
        self.assertEqual(self.app.mode, "menu")

    def test_escape_opens_pong_pause(self):
        """Escape открывает и закрывает меню паузы Pong."""
        self.app._start_game("pong")
        game = self.app.game
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        game.handle_event(event)
        self.assertTrue(game.is_paused)
        game.handle_event(event)
        self.assertFalse(game.is_paused)

    def test_menu_button_requests_return(self):
        """Кнопка MENU у Pinball возвращает управление App."""
        self.app._start_game("pinball")
        game = self.app.game
        game._on_end_click(game.end_buttons()["menu"].center)
        self.assertTrue(game.menu_requested)
        self.app._check_game_requests()
        self.assertEqual(self.app.mode, "menu")


if __name__ == "__main__":
    unittest.main()
