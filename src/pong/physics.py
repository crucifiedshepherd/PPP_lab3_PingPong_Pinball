"""Математика столкновений и отражения шарика от ракеток."""

import math


def paddle_reflection(contact, speed, direction):
    """Вычисляет скорость отражения с учётом точки удара.

    contact принимает значение от -1 до 1. При ударе по центру
    шарик летит почти горизонтально, у края — под большим углом.
    direction равен 1 для правой стороны и -1 для левой.
    """
    contact = min(1.0, max(-1.0, float(contact)))
    angle = contact * math.radians(62)
    horizontal = abs(math.cos(angle) * speed)
    horizontal *= 1 if direction >= 0 else -1
    vertical = math.sin(angle) * speed
    return horizontal, vertical


def clamp(value, lower, upper):
    """Ограничивает значение заданными границами."""
    return max(lower, min(upper, value))
