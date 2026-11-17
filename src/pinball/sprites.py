"""Загрузка и отрисовка спрайтов игрового стола."""

from pathlib import Path

import pygame


ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "pinball"


class PinballSprites:
    """Хранит изображения и рисует основные объекты."""

    # Ось игрового поля — x=628; отдельный канал справа её не меняет.
    FIELD_CENTER_X = 628
    INLAY_SIZE = (630, 704)
    INLAY_ORIGIN = (FIELD_CENTER_X - INLAY_SIZE[0] // 2, 88)

    def __init__(self):
        """Подготавливает пути и кэш изображений."""
        self.images = {}
        self._scaled_cache = {}
        self.available = True
        filenames = (
            "table_backdrop.png", "filigree_inlay.png",
            "hud_left.png", "hud_right.png", "panel_gear.png",
            "bumper.png", "bumper_glow.png",
            "target.png", "target_on.png", "ball.png",
            "flipper_left.png", "flipper_right.png",
            "slingshot_left.png", "slingshot_right.png",
            "amber_bloom.png", "aqua_bloom.png",
            "drop_active.png", "drop_down.png",
            "side_kicker.png",
            "top_left.png", "top_left_on.png",
            "top_center.png", "top_center_on.png",
            "top_right.png", "top_right_on.png",
        )
        for filename in filenames:
            path = ASSET_DIR / filename
            if not path.is_file():
                self.available = False
                continue
            image = pygame.image.load(str(path))
            # Для convert_alpha() сначала нужна поверхность окна.
            if pygame.display.get_surface() is not None:
                image = image.convert_alpha()
            self.images[filename] = image

        # Спрайты фиксированного размера храним в кэше.
        if "ball.png" in self.images:
            self.images["ball.png"] = self._scale("ball.png", (30, 28))

    def _scale(self, name, size):
        """Масштабирует изображение до указанного размера."""
        return pygame.transform.smoothscale(self.images[name], size)

    def draw_hud_panels(self, surface):
        """Рисует декоративные подложки боковых панелей."""
        for name, pos in (("hud_left.png", (15, 20)),
                          ("hud_right.png", (1034, 20))):
            skin = self.images.get(name)
            if skin is not None:
                surface.blit(skin, pos)

    def draw_cabinet(self, surface):
        """Рисует общий корпус автомата."""
        artwork = self.images.get("table_backdrop.png")
        if artwork is None:
            return False
        surface.blit(artwork, (293, 35))
        return True

    def draw_felt(self, surface):
        """Рисует основу игрового стола."""
        return "table_backdrop.png" in self.images

    def draw_inlay(self, surface):
        """Добавляет прозрачную гравировку поверх поля."""
        overlay = self.images.get("filigree_inlay.png")
        if overlay is not None:
            surface.blit(overlay, self.INLAY_ORIGIN)

    def _cached_scaled(self, name, size):
        """Возвращает масштабированный спрайт из кэша."""
        key = (name, int(size[0]), int(size[1]))
        if key not in self._scaled_cache:
            image = self.images[name]
            self._scaled_cache[key] = pygame.transform.smoothscale(
                image, (key[1], key[2]),
            )
        return self._scaled_cache[key]

    def _light(self, surface, center, color="amber", size=100):
        """Рисует мягкий световой ореол под объектом."""
        name = "amber_bloom.png" if color == "amber" else "aqua_bloom.png"
        if name not in self.images:
            return
        halo = self._cached_scaled(name, (size, size))
        surface.blit(halo, halo.get_rect(center=center))

    def draw_drop_target(self, surface, target):
        """Рисует мишень центральной группы."""
        name = "drop_active.png" if target.active else "drop_down.png"
        image = self.images.get(name)
        if image is None:
            return False
        center = (round(target.center.x), round(target.center.y))
        if target.active and target.flash > 0:
            self._light(surface, center, "amber", size=80)
        surface.blit(image, image.get_rect(center=center))
        return True

    def draw_side_kicker(self, surface, bumper):
        """Рисует боковой бампер."""
        image = self.images.get("side_kicker.png")
        if image is None:
            return False
        center = (round(bumper.center.x), round(bumper.center.y))
        if bumper.flash > 0:
            self._light(surface, center, "aqua", size=100)
        # Спрайт немного шире радиуса коллайдера за счёт фаски.
        fitted = self._cached_scaled("side_kicker.png", (58, 58))
        surface.blit(fitted, fitted.get_rect(center=center))
        return True

    def draw_top_target(self, surface, target, index, activated=False):
        """Рисует одну из верхних мишеней."""
        kind = ("left", "center", "right")[index]
        name = "top_{}{}.png".format(
            kind, "_on" if target.flash > 0 or activated else ""
        )
        image = self.images.get(name)
        if image is None:
            return self.draw_target(surface, target)
        center = (round(target.center.x), round(target.center.y))
        self._light(surface, center, "aqua" if index == 0 else
                    "amber", size=88)
        surface.blit(image, image.get_rect(center=target.center))
        if target.flash > 0:
            # Свечение появляется только после реального попадания.
            center = (round(target.center.x), round(target.center.y))
            pygame.draw.circle(surface, (255, 228, 140), center, 29, 2)

    def draw_bumper(self, surface, bumper):
        """Рисует круглый бампер с подсветкой."""
        import math

        center = (round(bumper.center.x), round(bumper.center.y))
        # Подсветка располагается под объектом столкновения.
        self._light(surface, center, "amber" if bumper.points >= 100
                    else "aqua", size=round(2 * bumper.radius + 95))
        name = "bumper_glow.png" if bumper.flash > 0 else "bumper.png"
        source = self.images[name]
        diameter = round(2 * bumper.radius + 27)
        height = round(diameter * source.get_height() / source.get_width())
        image = self._cached_scaled(name, (diameter, height))
        surface.blit(image, image.get_rect(center=bumper.center))
        # Движущийся блик имитирует отражение на металлическом куполе.
        moment = pygame.time.get_ticks() * .0015
        angle = moment + bumper.center.x * .007
        r = bumper.radius * .76
        spot = (round(center[0] + r * math.cos(angle)),
                round(center[1] - r * .42 + r * .45 * math.sin(angle)))
        pygame.draw.circle(surface, (255, 238, 188), spot, 2)

    def draw_target(self, surface, target):
        """Рисует небольшую мишень по её координатам."""
        name = "target_on.png" if target.flash > 0 else "target.png"
        source = self.images[name]
        # Спрайт шире физического радиуса мишени (14 пикселей).
        width = target.radius * 3
        height = round(width * source.get_height() / source.get_width())
        image = self._cached_scaled(name, (width, height))
        surface.blit(image, image.get_rect(center=target.center))

    def draw_sling(self, surface, sling):
        """Рисует изображение пружинной пластины."""
        left = sling.direction == 1
        name = "slingshot_left.png" if left else "slingshot_right.png"
        original = self.images[name]
        turned = pygame.transform.rotate(original, -90 if left else 90)
        xs = [point.x for point in sling.vertices]
        ys = [point.y for point in sling.vertices]
        size = (round(max(xs) - min(xs) + 12),
                round(max(ys) - min(ys) + 12))
        sprite = pygame.transform.smoothscale(turned, size)
        center = (round((min(xs) + max(xs)) * 0.5),
                  round((min(ys) + max(ys)) * 0.5))
        surface.blit(sprite, sprite.get_rect(center=center))
        if sling.flash > 0:
            pygame.draw.circle(surface, (255, 222, 145),
                               (round(sling.center.x),
                                round(sling.center.y)), 6)

    def draw_flipper(self, surface, flipper):
        """Поворачивает спрайт вместе с флиппером."""
        left = flipper.direction == 1
        name = "flipper_left.png" if left else "flipper_right.png"
        original = self.images[name]

        # Шарнир расположен у основания каждого флиппера.
        # Длина лопасти на исходном изображении около 140 пикселей.
        factor = flipper.length / 140.0
        width = round(original.get_width() * factor)
        height = round(original.get_height() * factor)
        base = self._cached_scaled(name, (width, height))

        # Спрайт изначально наклонён на 14 градусов.
        # В Pygame положительный угол вращает против часовой стрелки.
        angle = 51.0 * flipper.direction * flipper.lift
        if left:
            angle += 2.0
        rotated = pygame.transform.rotate(base, angle)

        # Положение шарнира задано долями ширины и высоты PNG.
        pivot_fraction = (0.17, 0.32) if left else (0.82, 0.33)
        anchor = pygame.Vector2(
            width * pivot_fraction[0], height * pivot_fraction[1],
        )
        offset = anchor - pygame.Vector2(width / 2, height / 2)
        # Смещение центра вращаем вместе со спрайтом.
        offset = offset.rotate(-angle)
        rotated_center = flipper.pivot - offset
        surface.blit(rotated, rotated.get_rect(center=rotated_center))

    def draw_ball(self, surface, ball):
        """Рисует металлический шарик."""
        for index, point in enumerate(ball.trail):
            strength = (index + 1) / (len(ball.trail) + 1)
            color = (int(55 + 60 * strength),
                     int(115 + 40 * strength),
                     int(111 + 35 * strength))
            pygame.draw.circle(surface, color, point, 2 + index // 3)
        image = self.images["ball.png"]
        center = (round(ball.position.x), round(ball.position.y))
        # Тёмный контур выделяет шарик на ярком фоне.
        pygame.draw.circle(surface, (8, 29, 30),
                           (center[0] + 2, center[1] + 3),
                           ball.radius + 4)
        pygame.draw.circle(surface, (242, 211, 144), center,
                           ball.radius + 2, 2)
        surface.blit(image, image.get_rect(center=center))
