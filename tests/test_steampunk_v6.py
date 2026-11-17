"""Проверки пусковой дуги, мишеней и ресурсов графики."""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.config import STEP  # noqa: E402
from src.pinball.sprites import ASSET_DIR  # noqa: E402


class TestStage6DesignAndPhysics(unittest.TestCase):
    """Проверяет физику, расположение и отрисовку объектов."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_guided_entry_has_no_teleport(self):
        """Проверяет непрерывность траектории запуска."""
        for power in (0.0, 0.5, 1.0):
            with self.subTest(power=power):
                ball = Ball()
                ball.launch(power)
                previous = ball.position.copy()
                crossed = False
                for _ in range(500):
                    ball.advance(STEP)
                    if ball.mode == "entry":
                        crossed = True
                    self.assertLess(
                        (ball.position - previous).length(), 15,
                    )
                    previous = ball.position.copy()
                    if ball.mode == "play":
                        break
                self.assertTrue(crossed)
                self.assertEqual(ball.mode, "play")

    def test_charge_still_changes_playfield_entry(self):
        """Проверяет различие скоростей при разном заряде."""
        entries = []
        for charge in (0.0, 1.0):
            ball = Ball()
            ball.launch(charge)
            for _ in range(500):
                ball.advance(STEP)
                if ball.mode == "play":
                    break
            self.assertEqual(ball.mode, "play")
            entries.append(ball.velocity.copy())
        self.assertLess(entries[1].x, entries[0].x - 250)
        self.assertLess(entries[1].y, entries[0].y - 250)

    def test_completed_bank_stays_down_until_next_ball(self):
        """Проверяет мишени до следующего шара."""
        game = PinballGame()
        game.status = "playing"
        game.ball.mode = "play"
        for target in game.drop_targets:
            game.ball.position = target.center + pygame.Vector2(0, -16)
            game.ball.velocity.update(0, 300)
            game._physics_step(STEP)
        self.assertTrue(game.bank_completed)
        self.assertTrue(all(not t.active for t in game.drop_targets))
        score = game.score
        game.ball.mode = "ready"
        for _ in range(300):
            game.update(0.05)
        self.assertEqual(game.score, score)
        self.assertTrue(all(not t.active for t in game.drop_targets))
        game._lost_ball()
        self.assertTrue(all(t.active for t in game.drop_targets))
        self.assertFalse(game.bank_completed)

    def test_art_contains_single_background_and_top_switches(self):
        """Проверяет набор используемых фоновых ресурсов."""
        for filename in (
            "table_backdrop.png", "filigree_inlay.png",
            "top_left.png", "top_left_on.png",
            "top_center.png", "top_center_on.png",
            "top_right.png", "top_right_on.png",
        ):
            with self.subTest(filename=filename):
                path = ASSET_DIR / filename
                self.assertTrue(path.is_file(), str(path))
                self.assertGreater(path.stat().st_size, 500)

    def test_renderer_preserves_host_window_compatibility(self):
        """Проверяет совместимость с общим игровым окном."""
        game = PinballGame()
        for size in ((1200, 840), (1000, 700)):
            with self.subTest(size=size):
                surface = pygame.Surface(size)
                game.draw(surface)
                self.assertEqual(surface.get_size(), size)


if __name__ == "__main__":
    unittest.main()
