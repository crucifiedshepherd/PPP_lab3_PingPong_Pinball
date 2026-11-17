"""Проверки звука проигрыша и обновлённого интерфейса."""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402
from src.pinball.sprites import ASSET_DIR  # noqa: E402


class TestCopperGlassFourteen(unittest.TestCase):
    """Проверяет независимость оформления от игровой физики."""

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
        self.played = []
        self.game._play_sound = self.played.append

    def test_game_over_fanfare_once_not_for_every_drain(self):
        """Проверяет звук только после потери последнего шара."""
        self.game._lost_ball()
        self.assertNotIn("game_over", self.played)
        self.game._lost_ball()
        self.assertNotIn("game_over", self.played)
        self.game._lost_ball()
        self.assertEqual(self.played.count("game_over"), 1)
        self.assertEqual(self.game.status, "over")

    def test_audio_file_is_valid_riff_wave(self):
        """Проверяет заголовок и формат звукового файла."""
        path = ASSET_DIR / "sfx" / "game_over.wav"
        self.assertTrue(path.is_file())
        self.assertEqual(path.read_bytes()[:4], b"RIFF")

    def test_engraving_layer_stays_in_playfield(self):
        """Проверяет границы декоративного слоя."""
        image = pygame.image.load(str(ASSET_DIR / "filigree_inlay.png"))
        self.assertEqual(image.get_size(), (630, 704))

    def test_hud_and_overlay_draw_at_both_sizes(self):
        """Проверяет интерфейс в двух размерах окна."""
        for size in ((1200, 840), (1000, 700)):
            self.game.draw(pygame.Surface(size))
            self.game.status = "over"
            self.game.draw(pygame.Surface(size))


if __name__ == "__main__":
    unittest.main()
