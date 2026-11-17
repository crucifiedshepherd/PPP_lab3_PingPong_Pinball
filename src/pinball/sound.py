"""Загрузка и воспроизведение звуковых эффектов Pinball."""

from pathlib import Path

import pygame


SOUND_DIR = Path(__file__).resolve().parents[2] / "assets" / "pinball" / "sfx"


class PinballSounds:
    """Управляет короткими игровыми звуками."""

    def __init__(self):
        """Загружает WAV-файлы, если аудиосистема доступна."""
        self.sounds = {}
        try:
            mixer = getattr(pygame, "mixer", None)
            if mixer is None:
                return
            if not mixer.get_init():
                mixer.init()
            for name in ("flipper", "pop", "target", "launch", "drain",
                         "button", "lane", "combo", "perfect",
                         "overheat", "hot_pop", "game_over"):
                path = SOUND_DIR / (name + ".wav")
                if path.is_file():
                    self.sounds[name] = mixer.Sound(str(path))
            for sound in self.sounds.values():
                sound.set_volume(0.27)
        except (pygame.error, OSError, AttributeError):
            # При отсутствии аудиоустройства игра продолжает работать без
            # звука.
            self.sounds.clear()

    def play(self, name):
        """Воспроизводит звук по имени без остановки игры при ошибке."""
        effect = self.sounds.get(name)
        if effect is not None:
            try:
                effect.play()
            except (pygame.error, OSError):
                pass
