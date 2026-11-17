"""Визуальные эффекты попаданий, не влияющие на физику игры."""

import math

import pygame


class HitEffects:
    """Хранит и рисует кратковременные эффекты от столкновений."""

    def __init__(self):
        """Создаёт очередь эффектов попаданий."""
        self.active = []
        self._previous_contacts = set()
        self._previous_time = None

    def _trigger(self, obj, color):
        """Добавляет анимацию в точке столкновения."""
        self.active.append({
            "center": pygame.Vector2(obj.center),
            "age": 0.0,
            "ttl": 0.52,
            "points": obj.points,
            "label": "+{}".format(obj.points),
            "color": color,
        })
        # Ограничиваем очередь, чтобы эффекты не накапливались бесконечно.
        self.active = self.active[-18:]

    def sync(self, game):
        """Создаёт вспышки по зарегистрированным игровым событиям."""
        now = pygame.time.get_ticks() * 0.001
        dt = 0.0 if self._previous_time is None else min(
            0.05, max(0.0, now - self._previous_time),
        )
        self._previous_time = now

        queue = getattr(game, "point_events", None)
        if queue is not None:
            palette = {
                "pop": (255, 188, 85),
                "lane": (104, 238, 207),
                "other": (255, 181, 106),
            }
            for item in queue:
                color = palette.get(item["source"], palette["other"])
                factor = item["multiplier"]
                label = ("{} ×{}".format(item["points"], factor)
                         if factor > 1 else "+{}".format(item["earned"]))
                self.active.append({
                    "center": pygame.Vector2(item["center"]),
                    "age": 0.0,
                    "ttl": 0.80 if factor > 1 else 0.52,
                    "points": item["earned"],
                    "label": label,
                    "color": color,
                })
            queue.clear()
            self.active = self.active[-24:]
        else:
            # Поддержка тестов, в которых очередь событий не используется.
            contacts = set()
            for objects, color in ((game.bumpers, (255, 185, 83)),
                                   (game.targets, (101, 226, 205))):
                for obj in objects:
                    if obj.flash > 0:
                        ident = id(obj)
                        contacts.add(ident)
                        if ident not in self._previous_contacts:
                            self._trigger(obj, color)
            self._previous_contacts = contacts

        for effect in self.active:
            effect["age"] += dt
        self.active = [effect for effect in self.active
                       if effect["age"] < effect["ttl"]]

    def draw_lighting(self, surface):
        """Рисует мягкую подсветку вокруг недавних попаданий."""
        for effect in self.active:
            amount = max(0.0, 1.0 - effect["age"] / effect["ttl"])
            if amount <= 0:
                continue
            size = 228
            lamp = pygame.Surface((size, size), pygame.SRCALPHA)
            rgb = effect["color"]
            for radius, alpha in ((109, 8), (87, 13),
                                  (65, 19), (43, 25), (24, 28)):
                opacity = round(alpha * amount)
                pygame.draw.circle(lamp, (*rgb, opacity),
                                   (size // 2, size // 2), radius)
            center = effect["center"]
            surface.blit(lamp, (round(center.x) - size // 2,
                                round(center.y) - size // 2))

    def draw(self, surface, font):
        """Рисует искры, кольца и всплывающие очки."""
        for effect in self.active:
            progress = effect["age"] / effect["ttl"]
            alpha = round(185 * (1.0 - progress))
            center = effect["center"]
            color = effect["color"]

            # Отдельный слой с альфа-каналом обеспечивает плавное затухание.
            halo = pygame.Surface((164, 164), pygame.SRCALPHA)
            radius = round(23 + 46 * progress)
            pygame.draw.circle(
                halo, (*color, alpha), (82, 82), radius, 3,
            )
            pygame.draw.circle(
                halo, (*color, alpha // 3), (82, 82), radius + 7, 8,
            )
            surface.blit(
                halo, (round(center.x) - 82, round(center.y) - 82),
            )

            # Искры расходятся от места настоящего столкновения.
            for i in range(9):
                angle = i * 2 * math.pi / 9 + 0.14
                start = 24 + 28 * progress
                finish = start + 8 * (1.0 - progress)
                a = (round(center.x + math.cos(angle) * start),
                     round(center.y + math.sin(angle) * start))
                b = (round(center.x + math.cos(angle) * finish),
                     round(center.y + math.sin(angle) * finish))
                if progress < 0.75:
                    pygame.draw.line(surface, color, a, b, 2)

            # Количество очков берётся из события, а не из рисунка.
            text = effect.get("label", "+{}".format(effect["points"]))
            label = font.render(text, True, (255, 233, 171))
            rect = label.get_rect(
                center=(round(center.x), round(center.y - 60 - 32 * progress)),
            )
            shadow = font.render(text, True, (18, 27, 25))
            surface.blit(shadow, rect.move(1, 2))
            surface.blit(label, rect)
