"""Проверки Perfect Flip, перегрева и всплывающих очков."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402
from src.pinball.objects import Ball, Flipper  # noqa: E402
from src.pinball.effects import HitEffects  # noqa: E402


class TestCopperGlassThirteen(unittest.TestCase):
    """Проверяет бонусы и отображение счёта."""

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

    def test_scoring_label_is_compact_but_amount_stays_correct(self):
        """Проверяет короткую подпись без потери начисленных очков."""
        self.game.combo_remaining = 9.0
        earned = self.game._award(300, source="lane")
        self.assertEqual(earned, 600)
        self.assertEqual(self.game.score, 600)
        self.assertEqual(self.game.message, "300 ×2")
        self.assertEqual(self.game.point_events[-1]["earned"], 600)

    def test_floating_label_matches_compact_hud_text(self):
        """Проверяет совпадение подписей с событием попадания."""
        self.game.combo_remaining = 9.0
        self.game._award(125, source="other", position=(628, 400))
        effects = HitEffects()
        effects.sync(self.game)
        self.assertEqual(effects.active[0]["label"], "125 ×2")
        self.assertEqual(effects.active[0]["points"], 250)

    def test_real_rising_tip_contact_is_marked_perfect(self):
        """Проверяет точный удар поднимающимся флиппером."""
        flipper = Flipper(482, 710, 1, (220, 90, 90))
        ball = Ball()
        flipper.update(0.05, True)
        a, b = flipper.endpoints()
        ball.position = a + (b - a) * 0.76 + pygame.Vector2(0, -17)
        ball.velocity.update(0, 290)
        self.assertTrue(flipper.hit(ball))
        self.assertTrue(flipper.last_hit_perfect)
        self.assertGreaterEqual(flipper.last_hit_fraction, 0.54)

    def test_held_paddle_is_not_perfect(self):
        """Проверяет отсутствие бонуса за удержание флиппера."""
        flipper = Flipper(482, 710, 1, (220, 90, 90))
        ball = Ball()
        flipper.update(0.13, True)
        a, b = flipper.endpoints()
        ball.position = a + (b - a) * 0.76 + pygame.Vector2(0, -17)
        ball.velocity.update(0, 290)
        self.assertTrue(flipper.hit(ball))
        self.assertFalse(flipper.last_hit_perfect)

    def test_heat_activates_on_real_scoring_impacts(self):
        """Проверяет включение перегрева после серии ударов."""
        for _ in range(6):
            self.game._award(100, source="pop")
        self.assertEqual(self.game.overheat_remaining, 6.0)
        self.assertEqual(self.game.heat, 100.0)
        self.assertGreater(self.game.overheat_banner_time, 0)

    def test_bank_bonus_does_not_heat_the_machine(self):
        """Проверяет отсутствие нагрева от награды за группу."""
        self.game._award(850, source="bonus")
        self.assertEqual(self.game.heat, 0.0)

    def test_overheat_pauses_and_cools_down(self):
        """Проверяет паузу, завершение перегрева и перезарядку."""
        self.game.status = "playing"
        for _ in range(6):
            self.game._award(100, source="pop")
        self.game._toggle_menu()
        self.game.update(0.05)
        self.assertEqual(self.game.overheat_remaining, 6.0)
        self.game._toggle_menu()
        self.game.overheat_remaining = 0.03
        self.game.update(0.05)
        self.assertEqual(self.game.overheat_remaining, 0.0)
        self.assertGreater(self.game.overheat_cooldown, 0)

    def test_restart_resets_all_new_features(self):
        """Проверяет сброс новых бонусов при перезапуске."""
        self.game._award(125, source="perfect")
        self.game.overheat_remaining = 5
        self.game.perfect_banner_time = 1
        self.game.restart()
        self.assertEqual(self.game.heat, 0)
        self.assertEqual(self.game.overheat_remaining, 0)
        self.assertEqual(self.game.perfect_banner_time, 0)

    def test_new_hud_draws_at_native_and_shared_sizes(self):
        """Проверяет отрисовку панели при разных разрешениях."""
        for size in ((1200, 840), (1000, 700)):
            self.game.draw(pygame.Surface(size))


if __name__ == "__main__":
    unittest.main()
