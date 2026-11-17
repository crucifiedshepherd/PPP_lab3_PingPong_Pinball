"""Проверки выравнивания игрового поля и орнамента."""

import unittest

import pygame

from src.pinball.game import PinballGame
from src.pinball.renderer import PinballRenderer
from src.pinball.sprites import ASSET_DIR, PinballSprites


class TestPinballArtAlignment(unittest.TestCase):
    """Проверяет расположение декора относительно игрового поля."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_decoration_is_centered_on_real_table_axis(self):
        """Проверяет центрирование рисунка без учёта пусковой полосы."""
        start_x, start_y = PinballSprites.INLAY_ORIGIN
        width, height = PinballSprites.INLAY_SIZE
        self.assertEqual((width, height), (630, 704))
        self.assertEqual(start_x + width // 2, 628)
        self.assertEqual(start_y, 88)
        game = PinballGame()
        physical_center = (
            game.left_flipper.pivot.x + game.right_flipper.pivot.x
        ) / 2
        self.assertLessEqual(abs(628 - physical_center), 2)

    def test_title_is_centered_on_left_panel(self):
        """Проверяет положение заголовка на левой панели."""
        self.assertEqual(PinballRenderer.LEFT_PANEL_CENTER_X, 145)
        self.assertEqual(PinballRenderer.TITLE_PLATE_WIDTH, 226)
        self.assertEqual(145 - 226 // 2, 32)

    def test_engraving_is_a_separate_game_asset(self):
        """Проверяет отдельный ресурс декоративного слоя."""
        image = pygame.image.load(str(ASSET_DIR / 'filigree_inlay.png'))
        self.assertEqual(image.get_size(), (630, 704))
        game = PinballGame()
        game.draw(pygame.Surface((1200, 840)))


if __name__ == '__main__':
    unittest.main()
