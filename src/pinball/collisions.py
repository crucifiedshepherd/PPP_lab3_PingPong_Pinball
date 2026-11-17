"""Расчёт столкновений шарика с направляющими и флипперами."""

import math

import pygame


def pos(vector):
    """Преобразует вектор в целочисленные координаты."""
    return round(vector.x), round(vector.y)


def circle_segment(ball, start, end, thickness):
    """Находит точку контакта шарика с отрезком заданной толщины."""
    edge = end - start
    denominator = edge.length_squared()
    if denominator <= 0.000001:
        return None
    # Проецируем центр шарика на линию направляющей.
    along = (ball.position - start).dot(edge) / denominator
    # Точка контакта не должна выходить за концы отрезка.
    along = max(0.0, min(1.0, along))
    nearest = start + edge * along
    difference = ball.position - nearest
    # Учитываем одновременно радиус шарика и толщину направляющей.
    limit = ball.radius + thickness * 0.5
    distance_squared = difference.length_squared()
    if distance_squared > limit * limit:
        return None
    # Нормаль задаёт направление выталкивания шарика.
    if distance_squared > 0.000001:
        normal = difference / math.sqrt(distance_squared)
    else:
        normal = pygame.Vector2(-edge.y, edge.x).normalize()
        if normal.y > 0:
            normal = -normal
    return nearest, normal, limit, along


def reflect_velocity(velocity, normal, bounce):
    """Отражает скорость шарика при движении к поверхности."""
    approach = velocity.dot(normal)
    if approach >= 0:
        return False
    velocity -= (1 + bounce) * approach * normal
    return True
