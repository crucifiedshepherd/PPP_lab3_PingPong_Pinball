"""Загрузка и кэширование графических ресурсов Pong."""

from pathlib import Path

import pygame

from src.pong.config import HEIGHT, WIDTH

ASSET_DIRECTORY = Path(__file__).resolve().parents[2] / "assets" / "pong"


class PongSprites:
    """Загружает изображения и сохраняет масштабированные копии."""

    def __init__(self):
        """Загружает изображения из папки assets/pong."""
        self.images = {}
        self.scaled = {}
        for name in (
            "court", "ball", "paddle_cyan", "paddle_pink",
            "star_cyan", "star_pink",
        ):
            path = ASSET_DIRECTORY / (name + ".png")
            try:
                self.images[name] = pygame.image.load(str(path))
                self.images[name] = self.images[name].convert_alpha()
            except (pygame.error, OSError, FileNotFoundError):
                self.images[name] = None

    def get(self, name, size=None):
        """Возвращает изображение заданного размера или None."""
        original = self.images.get(name)
        if original is None:
            return None
        if size is None:
            return original
        key = (name, tuple(size))
        if key not in self.scaled:
            self.scaled[key] = pygame.transform.smoothscale(
                original, tuple(size),
            )
        return self.scaled[key]

    def background(self):
        """Возвращает фоновую текстуру размера окна."""
        return self.get("court", (WIDTH, HEIGHT))
