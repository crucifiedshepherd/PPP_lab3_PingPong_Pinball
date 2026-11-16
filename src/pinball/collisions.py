"""Геометрия столкновений шарика с препятствиями."""

import math

import pygame


def pos(vector):
    """Convert a Vector2 into a pair of pixel coordinates."""
    return round(vector.x), round(vector.y)


def circle_segment(ball, start, end, thickness):
    """Return nearest point, outward normal, and distance on contact.

    A flipper or wall is treated as a capsule: a segment with a radius.
    This avoids treating a rotating paddle as an infinitely thin line.
    """
    edge = end - start
    denominator = edge.length_squared()
    if denominator <= 0.000001:
        return None
    # Проекция центра шарика на ближайшую точку отрезка.
    along = (ball.position - start).dot(edge) / denominator
    # Не допускаем выхода проекции за его концы.
    along = max(0.0, min(1.0, along))
    nearest = start + edge * along
    difference = ball.position - nearest
    # Суммарная толщина столкновения учитывает радиус шарика.
    limit = ball.radius + thickness * 0.5
    distance_squared = difference.length_squared()
    if distance_squared > limit * limit:
        return None
    # Нормаль показывает, куда следует вытолкнуть шарик.
    if distance_squared > 0.000001:
        normal = difference / math.sqrt(distance_squared)
    else:
        normal = pygame.Vector2(-edge.y, edge.x).normalize()
        if normal.y > 0:
            normal = -normal
    return nearest, normal, limit, along


def reflect_velocity(velocity, normal, bounce):
    """Reflect velocity only when an object is moving into a wall."""
    approach = velocity.dot(normal)
    if approach >= 0:
        return False
    velocity -= (1 + bounce) * approach * normal
    return True
