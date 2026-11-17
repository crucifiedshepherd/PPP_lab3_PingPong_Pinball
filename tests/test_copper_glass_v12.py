"""Проверки отображения очков и действия множителя."""

import os
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402
from src.pinball.effects import HitEffects  # noqa: E402
from src.pinball.sprites import ASSET_DIR  # noqa: E402


class TestCopperGlassTwelve(unittest.TestCase):
    """Проверяет согласованность очков, эффектов и табло."""

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

    def activate_combo(self):
        """Включает множитель последовательными попаданиями."""
        for _ in range(3):
            self.game._award(100, source="pop", position=(626, 274))

    def test_normal_hit_label_matches_score(self):
        """Проверяет подпись обычного попадания."""
        self.game._award(150, position=(521, 178))
        self.assertEqual(self.game.score, 150)
        self.assertEqual(self.game.message, "+150")
        self.assertEqual(self.game.point_events[-1]["multiplier"], 1)
        self.assertEqual(self.game.point_events[-1]["earned"], 150)

    def test_combo_hit_shows_short_multiplier_not_equation(self):
        """Проверяет короткую подпись при множителе."""
        self.activate_combo()
        self.game._award(150, position=(521, 178))
        self.assertEqual(self.game.score, 700)
        self.assertEqual(self.game.message, "150 ×2")
        event = self.game.point_events[-1]
        self.assertEqual((event["points"], event["multiplier"],
                          event["earned"]), (150, 2, 300))

    def test_combo_activation_has_separate_full_field_banner(self):
        """Проверяет баннер при включении двойных очков."""
        self.activate_combo()
        self.assertEqual(self.game.combo_remaining, 9.0)
        self.assertEqual(self.game.combo_banner_time, 1.9)
        self.assertEqual(self.game.point_events[-1]["earned"], 200)
        self.assertEqual(self.game.message, "100 ×2")

    def test_effect_consumes_real_scoring_event_once(self):
        """Проверяет однократную обработку события начисления."""
        self.activate_combo()
        self.game.point_events.clear()
        self.game._award(175, source="lane", position=(413, 303))
        effects = HitEffects()
        effects.sync(self.game)
        self.assertEqual(len(self.game.point_events), 0)
        self.assertEqual(len(effects.active), 1)
        self.assertEqual(effects.active[0]["label"], "175 ×2")
        self.assertEqual(effects.active[0]["points"], 350)
        effects.sync(self.game)
        self.assertEqual(len(effects.active), 1)

    def test_double_score_expires_without_changing_the_next_hit(self):
        """Проверяет истечение бонуса перед следующим ударом."""
        self.activate_combo()
        self.game.combo_remaining = 0.0
        earned = self.game._award(150)
        self.assertEqual(earned, 150)
        self.assertEqual(self.game.message, "+150")
        self.assertEqual(self.game.point_events[-1]["multiplier"], 1)

    def test_restart_clears_banner_and_impact_history(self):
        """Проверяет очистку эффектов при перезапуске."""
        self.activate_combo()
        self.game.restart()
        self.assertEqual(self.game.combo_remaining, 0.0)
        self.assertEqual(self.game.combo_banner_time, 0.0)
        self.assertEqual(self.game.point_events, [])

    def test_pause_freezes_x2_counter_and_banner(self):
        """Проверяет остановку таймеров множителя на паузе."""
        self.activate_combo()
        self.game.status = "playing"
        self.game._toggle_menu()
        self.game.update(0.05)
        self.assertEqual(self.game.combo_remaining, 9.0)
        self.assertEqual(self.game.combo_banner_time, 1.9)

    def test_new_panels_and_gear_have_correct_dimensions(self):
        """Проверяет размеры изображений боковых панелей."""
        for name, size in (("hud_left.png", (260, 794)),
                           ("hud_right.png", (152, 794)),
                           ("panel_gear.png", (100, 100))):
            with self.subTest(name=name):
                img = pygame.image.load(str(ASSET_DIR / name))
                self.assertEqual(img.get_size(), size)

    def test_renderer_draws_when_multiplier_is_active(self):
        """Проверяет отрисовку игры при активном множителе."""
        self.activate_combo()
        self.game.status = "playing"
        self.game.draw(pygame.Surface((1200, 840)))
        self.game.draw(pygame.Surface((1000, 700)))


if __name__ == "__main__":
    unittest.main()
