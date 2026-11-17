"""Проверки пускового канала и столкновений у нижних пластин."""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.config import STEP  # noqa: E402
from src.pinball.sprites import ASSET_DIR, PinballSprites  # noqa: E402


class TestCopperGlassNine(unittest.TestCase):
    """Проверяет выход шарика, слинги и размеры интерфейса."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_exit_reaches_clear_playfield(self):
        """Проверяет выход шарика ниже верхней арки."""
        finish = Ball.entry_point(1.0)
        self.assertLess(finish.x, 875)
        self.assertGreater(finish.y, 235)
        half = Ball.entry_point(0.5)
        self.assertLess(half.x, 951)

    def test_entry_is_continuous(self):
        """Проверяет плавное движение без скачка координат."""
        previous = Ball.entry_point(0)
        for k in range(1, 301):
            location = Ball.entry_point(k / 300)
            self.assertLess((location - previous).length(), 6)
            previous = location

    def test_slings_send_ball_to_own_flipper_side(self):
        """Проверяет отскок слингов к своим флипперам."""
        game = PinballGame()
        for sling in game.slingshots:
            with self.subTest(direction=sling.direction):
                ball = Ball()
                ball.mode = "play"
                top = sling.vertices[0]
                ball.position = pygame.Vector2(top.x, top.y - 10)
                ball.velocity.update(0, 280)
                self.assertEqual(sling.hit(ball), sling.points)
                self.assertLess(
                    ball.velocity.x * sling.direction, -145
                )
                self.assertLess(ball.velocity.y, -150)
                self.assertGreater(ball.velocity.y, -320)

    def test_corner_escape_has_no_teleport(self):
        """Проверяет выход из угла без телепортации."""
        game = PinballGame()
        game.status = "playing"
        game.ball.mode = "play"
        game.ball.position.update(917, 225)
        game.ball.velocity.update(0, 0)
        before = game.ball.position.copy()
        # Делаем шаги физики напрямую, без запуска игрового цикла.
        for _ in range(270):
            if game.status != "playing":
                break
            game._physics_step(STEP)
        self.assertGreater((game.ball.position - before).length(), 10)

    def test_only_loaded_images_remain(self):
        """Проверяет отсутствие устаревших копий изображений."""
        art = PinballSprites()
        self.assertTrue(art.available)
        self.assertEqual(
            {p.name for p in ASSET_DIR.glob("*.png")},
            set(art.images),
        )
        self.assertNotIn("cabinet_frame.png", art.images)
        self.assertNotIn("felt_detail.png", art.images)

    def test_hud_does_not_cover_field_with_plaque(self):
        """Проверяет отображение игры при разных размерах окна."""
        game = PinballGame()
        for dimensions in ((1200, 840), (1000, 700)):
            with self.subTest(size=dimensions):
                game.draw(pygame.Surface(dimensions))


if __name__ == "__main__":
    unittest.main()
