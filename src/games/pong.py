"""Совместимая точка входа режима Pong.

Реализация игры находится в пакете src.pong.
"""

from src.pong.entities import Ball, Paddle
from src.pong.game import PongGame

__all__ = ("Ball", "Paddle", "PongGame")
