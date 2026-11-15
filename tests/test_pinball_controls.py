"""Test layout-independent Pinball controls using SDL2 scan codes."""

import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame  # noqa: E402

from src.games.pinball import PinballGame  # noqa: E402


class TestPinballControls(unittest.TestCase):
    """Verify physical keyboard controls on different layouts."""

    @classmethod
    def setUpClass(cls):
        """Initialize Pygame without opening a visible window."""
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        """Release Pygame resources after the tests."""
        pygame.quit()

    def setUp(self):
        """Create a new game for every test."""
        self.game = PinballGame()

    def send(self, event_type, scancode, key=0):
        """Send a synthetic physical key event to the game."""
        event = pygame.event.Event(
            event_type, {"key": key, "scancode": scancode},
        )
        self.game.handle_event(event)
        self.game.update(1 / 60)

    def test_left_flipper_on_russian_layout(self):
        """The A-position key works when the resulting letter is not A."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_A)
        self.assertTrue(self.game.left_flipper.pressed)
        self.assertFalse(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_A)
        self.assertFalse(self.game.left_flipper.pressed)

    def test_right_flipper_on_russian_layout(self):
        """The D-position key works independently of the layout."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_D)
        self.assertTrue(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_D)
        self.assertFalse(self.game.right_flipper.pressed)

    def test_arrow_keys(self):
        """Left and right arrows also move their respective flippers."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_LEFT)
        self.send(pygame.KEYDOWN, pygame.KSCAN_RIGHT)
        self.assertTrue(self.game.left_flipper.pressed)
        self.assertTrue(self.game.right_flipper.pressed)
        self.send(pygame.KEYUP, pygame.KSCAN_LEFT)
        self.assertFalse(self.game.left_flipper.pressed)
        self.assertTrue(self.game.right_flipper.pressed)

    def test_layout_switch_while_pressed(self):
        """A key release uses its physical code after a layout change."""
        self.send(pygame.KEYDOWN, pygame.KSCAN_A, key=pygame.K_a)
        self.send(pygame.KEYUP, pygame.KSCAN_A, key=0)
        self.assertFalse(self.game.left_flipper.pressed)

    def test_restart_and_pause_by_scancode(self):
        """The P and R positions work without English letter keycodes."""
        self.game.status = "playing"
        self.send(pygame.KEYDOWN, pygame.KSCAN_P)
        self.assertEqual(self.game.status, "paused")
        self.send(pygame.KEYDOWN, pygame.KSCAN_R)
        self.assertEqual(self.game.status, "ready")


if __name__ == "__main__":
    unittest.main()
