"""Проверки падающих мишеней и пружинных пластин."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import Ball, PinballGame  # noqa: E402
from src.pinball.mechanisms import DropTarget, Slingshot  # noqa: E402


class TestStage4Mechanics(unittest.TestCase):
    """Проверяет новые элементы на игровом поле."""

    @classmethod
    def setUpClass(cls):
        """Подготавливает Pygame к тестам без видимого окна."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Освобождает ресурсы Pygame после тестов."""
        pygame.quit()

    def test_drop_target_hits_once_then_disappears(self):
        """Проверяет опускание мишени после попадания."""
        target = DropTarget(620, 470)
        ball = Ball()
        ball.mode = "play"
        ball.position = pygame.Vector2(620, 454)
        ball.velocity = pygame.Vector2(0, 300)
        self.assertEqual(target.hit(ball), 200)
        self.assertLess(ball.velocity.y, 0)
        self.assertFalse(target.active)
        self.assertEqual(target.hit(ball), 0)

    def test_bank_rewards_once_per_ball(self):
        """Проверяет однократную награду за группу мишеней."""
        game = PinballGame()
        game.status = "playing"
        game.ball.mode = "play"
        for target in game.drop_targets:
            game.ball.position = target.center + pygame.Vector2(0, -16)
            game.ball.velocity = pygame.Vector2(0, 330)
            game._physics_step(1 / 240)
        self.assertTrue(all(not x.active for x in game.drop_targets))
        self.assertEqual(game.score, 3 * 200 + 850)
        # Мишени не поднимаются сами даже после долгой игры.
        game.ball.mode = "ready"
        for _ in range(160):
            game.update(0.05)
        self.assertTrue(all(not x.active for x in game.drop_targets))
        self.assertTrue(game.bank_completed)
        self.assertEqual(game.score, 3 * 200 + 850)
        # Группа восстанавливается только при запуске нового шара.
        game._lost_ball()
        self.assertTrue(all(x.active for x in game.drop_targets))
        self.assertFalse(game.bank_completed)

    def test_slingshots_are_physical_and_scoring(self):
        """Проверяет физику и начисление очков у слингов."""
        game = PinballGame()
        self.assertEqual(len(game.slingshots), 2)
        self.assertTrue(all(isinstance(s, Slingshot)
                            for s in game.slingshots))
        for sling in game.slingshots:
            with self.subTest(side=sling.direction):
                ball = Ball()
                ball.mode = "play"
                # Шарик должен столкнуться с верхней гранью слинга.
                top = sling.vertices[0]
                ball.position = pygame.Vector2(top.x, top.y - 10)
                ball.velocity = pygame.Vector2(0, 280)
                self.assertEqual(sling.hit(ball), 125)
                self.assertLess(ball.velocity.y, 0)

    def test_top_three_bonus(self):
        """Проверяет бонус за три верхние мишени."""
        game = PinballGame()
        game.status = "playing"
        game.ball.mode = "play"
        for target in game.targets[:3]:
            game.ball.position = target.center + pygame.Vector2(0, -22)
            game.ball.velocity = pygame.Vector2(0, 320)
            game._physics_step(1 / 240)
        self.assertEqual(game.score, 3 * 150 + 600)
        self.assertEqual(len(game.top_hits), 0)

    def test_draw_scaling_remains_valid(self):
        """Проверяет масштабирование игрового поля."""
        game = PinballGame()
        for dimensions in ((1200, 840), (1000, 700)):
            scene = pygame.Surface(dimensions)
            game.draw(scene)
            self.assertEqual(scene.get_size(), dimensions)


if __name__ == "__main__":
    unittest.main()
