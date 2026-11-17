"""Звуковые эффекты неонового Pong."""

from pathlib import Path

import pygame

SOUND_DIRECTORY = (
    Path(__file__).resolve().parents[2] / "assets" / "pong" / "sfx"
)


class PongSounds:
    """Безопасно воспроизводит эффекты при наличии аудиоустройства."""

    def __init__(self):
        """Загружает короткие звуки ударов, очков и меню."""
        self.effects = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            for name in ("paddle", "wall", "score", "select", "pause", "win"):
                path = SOUND_DIRECTORY / (name + ".wav")
                if path.is_file():
                    self.effects[name] = pygame.mixer.Sound(str(path))
        except (pygame.error, OSError):
            self.effects.clear()

    def play(self, name):
        """Воспроизводит короткий эффект, если он доступен."""
        sound = self.effects.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass
