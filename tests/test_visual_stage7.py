"""Проверки оформления корпуса и размеров правой панели."""

import os
from pathlib import Path
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.pinball.sprites import PinballSprites  # noqa: E402


class TestStage7Artwork(unittest.TestCase):
    """Проверяет изображения и читаемость элементов интерфейса."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_integrated_background_matches_table_coordinates(self):
        """Проверяет размеры изображения игрового корпуса."""
        path = (Path(__file__).resolve().parents[1]
                / "assets" / "pinball" / "table_backdrop.png")
        self.assertTrue(path.is_file())
        surface = pygame.image.load(str(path))
        self.assertEqual(surface.get_size(), (742, 782))

    def test_cabinet_does_not_require_a_second_felt_layer(self):
        """Проверяет отсутствие второго слоя покрытия стола."""
        art = PinballSprites()
        surface = pygame.Surface((1200, 840))
        self.assertTrue(art.draw_cabinet(surface))
        self.assertTrue(art.draw_felt(surface))

    def test_right_hud_labels_fit_the_metal_panel(self):
        """Проверяет ширину подписей на правой панели."""
        font = pygame.font.Font(None, 21)
        labels = (
            "CONTROLS", "A / LEFT", "LEFT BAT",
            "D / RIGHT", "RIGHT BAT",
            "LAUNCH", "POWER 100%", "R  RESTART",
            "+100 POP", "+125 SLING", "+175 LANE",
        )
        for label in labels:
            with self.subTest(label=label):
                text = font.render(label, True, (255, 255, 255))
                self.assertLessEqual(text.get_width(), 129)

    def test_all_new_visual_parts_load(self):
        """Проверяет загрузку всех необходимых спрайтов."""
        art = PinballSprites()
        self.assertTrue(art.available)
        for name in (
            "drop_active.png", "drop_down.png", "side_kicker.png",
            "amber_bloom.png", "aqua_bloom.png", "table_backdrop.png",
        ):
            with self.subTest(name=name):
                self.assertIn(name, art.images)


if __name__ == "__main__":
    unittest.main()
