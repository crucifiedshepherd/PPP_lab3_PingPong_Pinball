"""Отрисовка игрового поля, интерфейса и анимаций."""

import math

import pygame

from src.pinball.config import (
    BOTTOM, CREAM, LEFT, RIGHT, SOFT, TOP, WIDTH, HEIGHT,
)
from src.pinball.effects import HitEffects
from src.pinball.sprites import PinballSprites

DARK = (12, 21, 24)
PANEL = (21, 41, 40)
GLASS = (7, 25, 26)
COPPER = (171, 91, 40)
COPPER_DARK = (73, 38, 25)
GOLD = (229, 173, 78)
FELT = (12, 82, 76)
AMBER = (255, 181, 53)
TURQUOISE = (96, 215, 194)


class PinballRenderer:
    """Рисует автомат, интерфейс и игровые эффекты."""

    # Левая панель занимает x=15..275; её центр находится в x=145.
    LEFT_PANEL_CENTER_X = 145
    TITLE_PLATE_WIDTH = 226

    def _art(self):
        """Возвращает объект с загруженными спрайтами."""
        if not hasattr(self, "_pinball_sprites"):
            self._pinball_sprites = PinballSprites()
        return self._pinball_sprites

    def _effects(self):
        """Возвращает менеджер визуальных эффектов."""
        if not hasattr(self, "_pinball_effects"):
            self._pinball_effects = HitEffects()
        return self._pinball_effects

    def _text(self, surface, text, x, y, font=None, color=CREAM):
        """Рисует надпись заданным шрифтом и цветом."""
        used_font = font or self.font_medium
        image = used_font.render(str(text), True, color)
        surface.blit(image, (x, y))

    def _theme_font(self, family, size, bold=False):
        """Подбирает системный шрифт для интерфейса."""
        aliases = {
            "Copperplate": "Georgia",
            "Palatino": "Avenir Next",
            "Menlo": "Avenir Next",
        }
        chosen = aliases.get(family, family)
        cache = self.__dict__.setdefault("_theme_font_cache", {})
        key = (chosen, size, bold)
        if key not in cache:
            cache[key] = pygame.font.SysFont(chosen, size, bold=bold)
        return cache[key]

    def _fitted_font(self, family, text, max_width, size, minimum=13):
        """Подбирает размер шрифта под доступную ширину."""
        for point_size in range(size, minimum - 1, -1):
            font = self._theme_font(family, point_size, True)
            if font.size(str(text))[0] <= max_width:
                return font
        return self._theme_font(family, minimum, True)

    @staticmethod
    def _centered_text(surface, text, rect, font, color):
        """Рисует текст с выравниванием по центру."""
        label = font.render(str(text), True, color)
        surface.blit(label, label.get_rect(center=rect.center))

    @staticmethod
    def _bolt(scene, x, y):
        """Рисует декоративную металлическую заклёпку."""
        pygame.draw.circle(scene, COPPER_DARK, (x + 2, y + 2), 7)
        pygame.draw.circle(scene, (205, 146, 77), (x, y), 6)
        pygame.draw.circle(scene, CREAM, (x - 2, y - 2), 2)
        pygame.draw.line(scene, COPPER_DARK, (x - 3, y + 2),
                         (x + 3, y - 2), 2)

    @staticmethod
    def _plate(scene, rect, border=GOLD, fill=GLASS, radius=9):
        """Рисует прямоугольную панель с объёмной рамкой."""
        pygame.draw.rect(scene, COPPER_DARK, rect.inflate(6, 6),
                         border_radius=radius + 2)
        pygame.draw.rect(scene, border, rect.inflate(2, 2), 2,
                         border_radius=radius)
        pygame.draw.rect(scene, fill, rect, border_radius=radius)
        pygame.draw.line(scene, (62, 96, 90),
                         (rect.x + 7, rect.y + 5),
                         (rect.right - 7, rect.y + 5), 1)

    def _cabinet(self, scene):
        """Рисует боковые панели и корпус автомата."""
        scene.fill(DARK)
        art = self._art()
        # Каждая панель HUD использует собственную цельную подложку.
        art.draw_hud_panels(scene)
        # В изображение корпуса уже включены металл, эмаль и подсветка.
        if not art.draw_cabinet(scene):
            pygame.draw.rect(scene, COPPER_DARK, (293, 35, 742, 782),
                             border_radius=25)
            pygame.draw.rect(scene, GOLD, (296, 38, 736, 776), 4,
                             border_radius=25)

    def _table_background(self, scene):
        """Рисует поле и декоративную гравировку."""
        self._cabinet(scene)
        art = self._art()
        if art.draw_felt(scene) is False:
            pygame.draw.rect(scene, FELT,
                             (LEFT, TOP, RIGHT - LEFT, BOTTOM - TOP))

        # Орнамент центрирован по оси игрового поля x=628.
        # Пусковой канал справа не должен сдвигать этот рисунок.
        art.draw_inlay(scene)

        # Метки центральной группы нанесены под стеклом.
        # Они не являются отдельными препятствиями.
        for x in (598, 628, 658):
            pygame.draw.circle(scene, (30, 107, 100), (x, 556), 5)
            pygame.draw.circle(scene, (130, 113, 72), (x, 556), 2)

        # Декоративные шестерёнки уже есть на фоновом изображении.

        # Во время паузы время анимации не увеличивается.
        beat = (math.sin(self.ambient_time * 2.4) + 1) * .5
        intensity = round(122 + 45 * beat)
        for x, y in ((394, 220), (865, 220), (398, 665), (854, 665)):
            pygame.draw.circle(scene, (33, intensity, 107), (x, y), 2)

        # Три лампы повторяют состояние центральной группы мишеней.
        for index, target in enumerate(self.drop_targets):
            x = round(target.center.x)
            lit = not target.active
            pygame.draw.circle(scene, COPPER_DARK, (x, 430), 9)
            pygame.draw.circle(scene, GOLD, (x, 430), 7, 2)
            pygame.draw.circle(scene, AMBER if lit else (31, 83, 78),
                               (x, 430), 4)
        # Внешний контур уже нарисован в фоне; не дублируем рамку.

        # Пусковой канал отделён от поля только гравировкой
        # и латунной направляющей, а не вторым фоном.
        pygame.draw.line(scene, (63, 125, 109), (957, 290),
                         (957, 785), 1)
        for y in (385, 530, 654):
            pygame.draw.lines(scene, (170, 116, 63), False,
                              [(975, y + 8), (984, y),
                               (993, y + 8)], 2)

        # Стеклянная трубка повторяет траекторию выхода шарика.
        self._draw_launch_exit(scene)
        # За ожидающим шариком показываем пусковую пружину.
        self._draw_plunger(scene)
        self._animated_light_tubes(scene)

        # Слив уже изображён на фоне; лишние накладки не нужны.

    @staticmethod
    def _draw_launch_exit(scene):
        """Рисует стеклянный выход пускового канала."""
        from src.pinball.objects import Ball

        tube = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Пусковой канал остаётся частью общего бирюзового покрытия.
        pygame.draw.line(tube, (7, 37, 35, 33),
                         (985, 134), (985, 767), 25)
        pygame.draw.line(tube, (135, 231, 202, 66),
                         (973, 143), (973, 755), 2)
        pygame.draw.line(tube, (220, 208, 135, 39),
                         (998, 143), (998, 755), 2)
        # Показываем лишь короткий изгиб стеклянной трубки.
        short = [Ball.entry_point(.18 * i / 12) for i in range(13)]
        coords = [(round(point.x), round(point.y)) for point in short]
        pygame.draw.lines(tube, (58, 179, 163, 40),
                          False, coords, 18)
        pygame.draw.lines(tube, (219, 213, 152, 65),
                          False, coords, 2)
        # У выхода трубка плавно становится прозрачнее.
        for index in range(5):
            t = .18 + .015 * index
            point = Ball.entry_point(t)
            alpha = round(48 * (1 - index / 5))
            pygame.draw.circle(tube, (106, 218, 194, alpha),
                               (round(point.x), round(point.y)), 3)
        scene.blit(tube, (0, 0))

    @staticmethod
    def _glass_reflection(scene):
        """Добавляет отблеск на стеклянной поверхности."""
        glass = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(glass, (209, 250, 236, 24),
                         (977, 150), (977, 747), 4)
        scene.blit(glass, (0, 0))

    def _animated_light_tubes(self, scene):
        """Рисует пульсирующие лампы по краям поля."""
        t = self.ambient_time
        glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        for x in (317, 1013):
            for y0, y1, phase in ((215, 315, 0.0), (385, 506, 1.5)):
                beat = (math.sin(t * 2.1 + phase + x / 300) + 1) * .5
                alpha = round(16 + 48 * beat)
                pygame.draw.line(glow, (255, 170, 51, alpha),
                                 (x, y0), (x, y1), 12)
                pygame.draw.line(glow, (255, 239, 170, alpha // 2),
                                 (x, y0 + 8), (x, y1 - 8), 2)
        scene.blit(glow, (0, 0))

    def _animated_hud_gears(self, scene):
        """Анимирует шестерёнки на боковых панелях."""
        art = self._art()
        gear = art.images.get("panel_gear.png")
        if gear is None:
            return
        for x, y, size, direction in (
            (142, 211, 74, 1),
            (1110, 176, 64, -1),
        ):
            # Шестерёнки на HUD анимируются отдельно от рисунка поля.
            base = art._cached_scaled("panel_gear.png", (size, size))
            angle = self.ambient_time * 28 * direction
            rotated = pygame.transform.rotate(base, angle)
            scene.blit(rotated, rotated.get_rect(center=(x, y)))
            # При активном множителе центральная лампа мигает.
            if self.combo_remaining > 0:
                pulse = (math.sin(self.ambient_time * 7.0) + 1) * .5
                color = (round(167 + 72 * pulse), 196, 108)
                pygame.draw.circle(scene, color, (x, y), 5)

    def _combo_ambience(self, scene):
        """Усиливает подсветку, пока действует множитель очков."""
        if self.combo_remaining <= 0 or self.status == "over":
            return
        phase = (math.sin(self.ambient_time * 8.0) + 1) * .5
        layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Полупрозрачная подсветка не скрывает шарик и мишени.
        layer.fill((221, 133, 39, round(3 + 8 * phase)))
        # Янтарные полосы подсвечивают внешние края корпуса.
        for x in (298, 1024):
            strength = round(22 + 48 * phase)
            pygame.draw.line(layer, (255, 180, 61, strength),
                             (x, 58), (x, 801), 10)
        # При двойных очках пульсируют и боковые панели.
        for rect in (pygame.Rect(18, 24, 254, 786),
                     pygame.Rect(1038, 24, 144, 786)):
            pygame.draw.rect(layer, (255, 208, 92, round(27 + 55 * phase)),
                             rect, 3, border_radius=12)
        scene.blit(layer, (0, 0))

    def _combo_banner(self, scene):
        """Показывает надпись о включении двойных очков."""
        left = getattr(self, "combo_banner_time", 0.0)
        if left <= 0 or self.menu_open or self.status == "over":
            return
        opacity = min(1.0, left / .35)
        # Табличка ненадолго появляется и затем затухает.
        y = round(319 - 7 * (1.0 - opacity))
        pane = pygame.Surface((484, 104), pygame.SRCALPHA)
        pane.fill((8, 32, 34, round(222 * opacity)))
        pygame.draw.rect(pane, (239, 183, 82, round(235 * opacity)),
                         pygame.Rect(3, 3, 478, 98), 3, border_radius=14)
        pygame.draw.rect(pane, (36, 159, 137, round(132 * opacity)),
                         pygame.Rect(10, 10, 464, 84), 2, border_radius=10)
        scene.blit(pane, (386, y))
        big = pygame.font.Font(None, 52)
        small = pygame.font.Font(None, 24)
        title = big.render("DOUBLE SCORE  x2", True, (255, 217, 133))
        sub = small.render("ALL POINTS DOUBLED  /  9 SECONDS", True,
                           (147, 240, 211))
        if hasattr(title, "set_alpha"):
            title.set_alpha(round(255 * opacity))
            sub.set_alpha(round(255 * opacity))
        scene.blit(title, title.get_rect(center=(628, y + 43)))
        scene.blit(sub, sub.get_rect(center=(628, y + 79)))

    @staticmethod
    def _draw_rail(scene, rail):
        """Рисует направляющую по координатам коллайдера."""
        pygame.draw.line(scene, (11, 29, 29), rail.a + (3, 5),
                         rail.b + (3, 5), rail.width + 8)
        pygame.draw.line(scene, COPPER_DARK, rail.a, rail.b,
                         rail.width + 6)
        pygame.draw.line(scene, (192, 121, 52), rail.a, rail.b,
                         rail.width + 2)
        pygame.draw.line(scene, GOLD, rail.a, rail.b, 2)
        if max(rail.a.y, rail.b.y) < 220:
            midpoint = (rail.a + rail.b) * 0.5
            at = (round(midpoint.x), round(midpoint.y))
            pygame.draw.circle(scene, COPPER_DARK, at, 7)
            pygame.draw.circle(scene, AMBER, at, 4)
            pygame.draw.circle(scene, (255, 240, 184),
                               (at[0] - 1, at[1] - 1), 1)
        # Боковые направляющие показаны как короткие рычаги.
        if rail.width == 6 and rail.a.y > 400:
            for endpoint in (rail.a, rail.b):
                at = (round(endpoint.x), round(endpoint.y))
                pygame.draw.circle(scene, COPPER_DARK, at, 9)
                pygame.draw.circle(scene, GOLD, at, 6, 2)
                pygame.draw.circle(scene, TURQUOISE, at, 3)

    @staticmethod
    def _draw_kicker(scene, bumper):
        """Рисует боковой бампер в его физической позиции."""
        x, y = round(bumper.center.x), round(bumper.center.y)
        lit = bumper.flash > 0
        color = (255, 225, 153) if lit else TURQUOISE
        # Декор не должен скрывать круговую зону контакта.
        pygame.draw.polygon(scene, (5, 33, 34),
                            [(x + 4, y - 28), (x + 30, y + 5),
                             (x + 4, y + 32), (x - 23, y + 5)])
        pygame.draw.polygon(scene, COPPER_DARK,
                            [(x, y - 29), (x + 25, y),
                             (x, y + 29), (x - 25, y)])
        pygame.draw.polygon(scene, GOLD,
                            [(x, y - 26), (x + 22, y),
                             (x, y + 26), (x - 22, y)], 3)
        pygame.draw.circle(scene, (20, 81, 78), (x, y), 17)
        pygame.draw.circle(scene, color, (x, y), 13, 3)
        pygame.draw.circle(scene, GOLD, (x, y), 5)
        pygame.draw.circle(scene, (255, 244, 192), (x - 2, y - 2), 2)

    @staticmethod
    def _draw_sling(scene, sling):
        """Рисует треугольную пружинную пластину."""
        vertices = [(round(p.x), round(p.y)) for p in sling.vertices]
        shadow = [(x + 4, y + 6) for x, y in vertices]
        pygame.draw.polygon(scene, (5, 27, 28), shadow)
        pygame.draw.polygon(scene, COPPER_DARK, vertices)
        pygame.draw.polygon(scene, GOLD, vertices, 5)
        center = sling.center
        inner = []
        for point in sling.vertices:
            inner.append((round(center.x + (point.x - center.x) * 0.72),
                          round(center.y + (point.y - center.y) * 0.72)))
        pygame.draw.polygon(scene, (35, 147, 135) if sling.flash
                            else (21, 96, 91), inner)
        pygame.draw.polygon(scene, TURQUOISE if sling.flash else
                            (76, 171, 154), inner, 2)
        # Положение болтов совпадает с границами слинга.
        for index, (x, y) in enumerate(vertices):
            pygame.draw.circle(scene, COPPER_DARK, (x, y), 7)
            pygame.draw.circle(scene, GOLD, (x, y), 4)
            if index == 1:
                pygame.draw.circle(scene, (255, 238, 160) if sling.flash
                                   else (236, 159, 71), (x, y), 3)

    @staticmethod
    def _draw_lane(scene, lane):
        """Рисует магнитный датчик и стрелку направления."""
        x, y = round(lane.center.x), round(lane.center.y)
        active = lane.flash > 0
        gold = (255, 218, 136) if active else GOLD
        glow = (177, 254, 228) if active else TURQUOISE
        # Декоративное кольцо не увеличивает радиус коллайдера.
        pygame.draw.circle(scene, (8, 38, 41), (x + 2, y + 3), 29)
        pygame.draw.circle(scene, COPPER_DARK, (x, y), 27)
        pygame.draw.circle(scene, gold, (x, y), 24, 3)
        pygame.draw.circle(scene, (12, 71, 70), (x, y), 19)
        pygame.draw.circle(scene, glow, (x, y), 17, 2)
        # Стрелка показывает направление ускорения внутрь поля.
        direction = lane.direction
        start = (x - direction * 9, y + 9)
        tip = (x + direction * 10, y - 10)
        pygame.draw.line(scene, glow, start, tip, 4)
        pygame.draw.lines(scene, glow, False,
                          [(tip[0] - direction * 10, tip[1] - 1), tip,
                           (tip[0] - direction * 1, tip[1] + 10)], 3)
        pygame.draw.circle(scene, (255, 242, 197),
                           (x - 7, y - 12), 2)

    @staticmethod
    def _draw_corner_gears(scene):
        """Рисует декоративные шестерёнки у верхней арки."""
        for cx, cy in ((407, 232), (856, 232)):
            pygame.draw.circle(scene, (11, 58, 57), (cx, cy), 25)
            pygame.draw.circle(scene, (101, 70, 39), (cx, cy), 23, 2)
            pygame.draw.circle(scene, (195, 134, 57), (cx, cy), 16, 2)
            pygame.draw.circle(scene, (16, 66, 63), (cx, cy), 9)
            pygame.draw.circle(scene, GOLD, (cx, cy), 5, 2)
            # Верхние шестерёнки нарисованы на поверхности стола.
            for dx, dy in ((0, -22), (22, 0), (0, 22), (-22, 0),
                           (16, 16), (-16, 16), (16, -16), (-16, -16)):
                pygame.draw.circle(scene, (150, 111, 57),
                                   (cx + dx, cy + dy), 3)

    def _draw_plunger(self, scene):
        """Рисует пружину и шарик в пусковом канале."""
        charge = self.charge if self.status == "ready" else 0.0
        x = 985
        bottom = 781
        top = 745 + round(20 * charge)
        # Небольшой стеклянный канал прилегает к поверхности стола.
        assembly = pygame.Surface((54, 90), pygame.SRCALPHA)
        pygame.draw.rect(assembly, (5, 26, 30, 155),
                         (10, 2, 34, 87), border_radius=12)
        pygame.draw.rect(assembly, (170, 117, 55, 125),
                         (10, 2, 34, 87), 2, border_radius=12)
        pygame.draw.line(assembly, (140, 219, 202, 78),
                         (16, 11), (16, 79), 2)
        scene.blit(assembly, (x - 27, 700))

        # При удержании пробела пружина сжимается.
        pts = []
        for i in range(15):
            y = top + (bottom - top) * i / 14
            pts.append((x + (8 if i % 2 else -8), round(y)))
        pygame.draw.lines(scene, (37, 29, 20), False,
                          [(a + 1, b + 1) for a, b in pts], 5)
        pygame.draw.lines(scene, (194, 123, 51), False, pts, 3)
        pygame.draw.line(scene, (250, 216, 126),
                         (x - 10, top - 1), (x + 10, top - 1), 3)
        pygame.draw.circle(scene, (255, 214, 118), (x, bottom), 5)

    @staticmethod
    def _draw_drop(scene, target):
        """Рисует поднятую или опущенную мишень."""
        x, y = round(target.center.x), round(target.center.y)
        rect = pygame.Rect(x - 27, y - 17, 54, 34)
        pygame.draw.rect(scene, (7, 29, 29), rect.move(3, 5),
                         border_radius=6)
        pygame.draw.rect(scene, COPPER_DARK, rect, border_radius=6)
        pygame.draw.rect(scene, GOLD, rect, 3, border_radius=6)
        if target.active:
            lamp = (255, 239, 153) if target.flash else (238, 96, 48)
            pygame.draw.rect(scene, (149, 49, 31), rect.inflate(-10, -11),
                             border_radius=3)
            pygame.draw.rect(scene, lamp, rect.inflate(-19, -15),
                             border_radius=3)
            pygame.draw.line(scene, (255, 213, 117),
                             (x - 14, y - 10), (x + 14, y - 10), 2)
        else:
            # После попадания изображаем прорезь опущенной мишени.
            pygame.draw.rect(scene, (10, 39, 38), rect.inflate(-8, -9),
                             border_radius=3)
            pygame.draw.line(scene, TURQUOISE, (x - 12, y),
                             (x + 12, y), 3)

    def _table_art(self, scene):
        """Собирает все визуальные слои игрового поля."""
        art = self._art()
        effects = self._effects()
        effects.sync(self)
        effects.draw_lighting(scene)
        for rail in self.rails:
            self._draw_rail(scene, rail)
        for bumper in self.bumpers:
            if bumper.points == 75:
                if not art.draw_side_kicker(scene, bumper):
                    self._draw_kicker(scene, bumper)
            elif art.available:
                art.draw_bumper(scene, bumper)
                # Латунный обод уже входит в изображение спрайта.
            else:
                bumper.draw(scene)
        # Слинги, боковые бамперы и группа мишеней работают в физике.
        for target in self.drop_targets:
            if not art.draw_drop_target(scene, target):
                self._draw_drop(scene, target)
        for sling in self.slingshots:
            if art.available:
                art.draw_sling(scene, sling)
                # Медная рамка уже нарисована внутри спрайта.
            else:
                self._draw_sling(scene, sling)
        for index, target in enumerate(self.targets):
            if art.available and index < 3:
                art.draw_top_target(scene, target, index,
                                    activated=index in self.top_hits)
            elif art.available:
                art.draw_target(scene, target)
            else:
                target.draw(scene)
        for lane in self.lanes:
            self._draw_lane(scene, lane)
        for flipper in (self.left_flipper, self.right_flipper):
            if art.available:
                art.draw_flipper(scene, flipper)
            else:
                flipper.draw(scene)
            # Подсветка вращается вместе с шарниром флиппера.
            at = (round(flipper.pivot.x - 2),
                  round(flipper.pivot.y - 3))
            pygame.draw.circle(scene, (255, 244, 201), at, 2)
            if flipper.swinging:
                start, finish = flipper.endpoints()
                # Блик появляется на подвижном флиппере, а не по всему полю.
                a = start + (finish - start) * 0.18
                b = start + (finish - start) * 0.78
                pygame.draw.line(scene, (255, 240, 173), a, b, 3)
                pygame.draw.circle(scene, (255, 242, 203), a, 4)
        if self.status != "over":
            if art.available:
                art.draw_ball(scene, self.ball)
            else:
                self.ball.draw(scene)

        if self.ball.mode in ("lane", "entry", "ready"):
            self._glass_reflection(scene)
        effects.draw(scene, self.font_small)

        # Подсвечиваем только настоящие мишени.
        bank_label = (
            "BANK CLEARED" if self.bank_completed else "DROP BANK +200"
        )
        self._centered_text(scene, bank_label,
                            pygame.Rect(533, 518, 188, 25),
                            self._fitted_font("Avenir Next", bank_label,
                                              194, 19), GOLD)
        # Слив расположен между двумя флипперами.

        # Шкала заряда находится на боковой панели.

    def _hud(self, scene):
        """Рисует очки, шары, заряд запуска и подсказки."""
        self._animated_hud_gears(scene)
        # Название размещено на отдельной эмалированной табличке.
        header = pygame.Rect(
            self.LEFT_PANEL_CENTER_X - self.TITLE_PLATE_WIDTH // 2,
            104, self.TITLE_PLATE_WIDTH, 58,
        )
        self._plate(scene, header, border=(216, 149, 71),
                    fill=(7, 38, 37), radius=11)
        title_font = self._fitted_font("Georgia", "PINBALL", 195, 37, 27)
        self._centered_text(scene, "PINBALL", header, title_font,
                            (255, 213, 131))
        for px in (header.x + 12, header.right - 12):
            pygame.draw.circle(scene, (149, 91, 43),
                               (px, header.centery), 3)
        # Выбираем шрифт с хорошо различимыми цифрами.
        label_face = "Avenir Next"
        left_x = 49
        label_font = self._theme_font(label_face, 18, True)
        self._text(scene, "SCORE", left_x, 262, label_font, CREAM)
        score_box = pygame.Rect(33, 293, 227, 68)
        self._plate(scene, score_box)
        pulse = getattr(self, "score_pulse", 0.0)
        nudge = round(2 * math.sin(pulse * 93) * min(1, pulse * 5))
        score_text = "{:06d}".format(self.score)
        self._centered_text(scene, score_text,
                            score_box.move(0, nudge),
                            self._fitted_font(label_face, score_text, 208,
                                              40, 24),
                            (255, 222, 161))
        self._text(scene, "BEST", left_x, 408, label_font, CREAM)
        best_box = pygame.Rect(33, 439, 227, 53)
        self._plate(scene, best_box)
        best_text = "{:06d}".format(self.best)
        self._centered_text(scene, best_text, best_box,
                            self._fitted_font(label_face, best_text, 205,
                                              26, 18), GOLD)
        self._text(scene, "BALLS LEFT", left_x, 514, label_font, CREAM)
        # Три гнезда показывают количество оставшихся шаров.
        lamp_box = pygame.Rect(37, 551, 222, 67)
        self._plate(scene, lamp_box, border=(164, 99, 49),
                    fill=(7, 34, 33), radius=13)
        for index in range(3):
            x, y = 80 + 69 * index, 585
            on = index < self.lives
            pygame.draw.circle(scene, (5, 21, 22), (x + 2, y + 3), 26)
            pygame.draw.circle(scene, (105, 54, 30), (x, y), 24)
            pygame.draw.circle(scene, (225, 162, 73), (x, y), 21, 4)
            pygame.draw.circle(scene, (53, 39, 25), (x, y), 17)
            pygame.draw.circle(scene, (255, 185, 57) if on
                               else (38, 70, 66), (x, y), 14)
            pygame.draw.circle(scene, (255, 233, 160) if on
                               else (80, 110, 101), (x - 4, y - 5), 4)
        ball_text = "{}/3 BALLS".format(self.lives)
        self._centered_text(scene, ball_text,
                            pygame.Rect(38, 624, 220, 22),
                            self._theme_font(label_face, 16, True), CREAM)

        # Тёмная вставка отделяет статистику от яркого орнамента.
        # Все строки имеют одинаковый левый отступ.
        stats_rect = pygame.Rect(33, 652, 226, 128)
        stats = pygame.Surface((stats_rect.width, stats_rect.height),
                               pygame.SRCALPHA)
        stats.fill((5, 28, 28, 217))
        pygame.draw.rect(stats, (177, 111, 53, 170),
                         pygame.Rect(0, 0, 225, 127), 1,
                         border_radius=9)
        scene.blit(stats, (stats_rect.x, stats_rect.y))
        stat_font = self._theme_font(label_face, 16, True)
        drop_count = sum(not target.active for target in self.drop_targets)
        lines = [
            ("TOP LAMPS  {}/3".format(len(self.top_hits)), GOLD),
            (("BANK DONE +850" if self.bank_completed else
              "DROP BANK  {}/3".format(drop_count)), TURQUOISE),
            (("X2 COMBO  {:.1f}s".format(self.combo_remaining)
              if self.combo_remaining > 0 else
              "POP CHAIN  {}/3".format(self.pop_chain)), SOFT),
            (("OVERHEAT  {:.1f}s".format(self.overheat_remaining)
              if self.overheat_remaining > 0 else
              "HEAT  {}%".format(round(self.heat))), AMBER),
        ]
        for index, (label, color) in enumerate(lines):
            font = self._fitted_font(label_face, label, 203, 16, 13)
            self._text(scene, label, left_x, 664 + index * 25,
                       font, color)
        pygame.draw.rect(scene, (49, 73, 68),
                         (47, 763, 196, 7), border_radius=3)
        heat_fill = round(192 * self.heat / 100)
        if heat_fill:
            pygame.draw.rect(scene,
                             AMBER if self.overheat_remaining > 0 else
                             (122, 220, 182),
                             (49, 765, heat_fill, 3), border_radius=2)

        # Правая панель узкая: подписи подгоняются под её ширину.
        rx, right_edge = 1059, 1172
        usable = right_edge - rx
        header_label = "CONTROLS"
        header_font = self._fitted_font("Georgia", header_label, usable,
                                        21, 14)
        self._centered_text(scene, header_label,
                            pygame.Rect(1055, 267, 122, 27),
                            header_font, GOLD)
        pygame.draw.line(scene, COPPER,
                         (rx, 298), (right_edge, 298), 1)
        for headline, detail, y in (
                ("A / LEFT", "LEFT BAT", 317),
                ("D / RIGHT", "RIGHT BAT", 392),
                ("SPACE", "LAUNCH", 467)):
            self._text(scene, headline, rx, y,
                       self._fitted_font(label_face, headline, usable,
                                         18, 13), CREAM)
            self._text(scene, detail, rx, y + 25,
                       self._fitted_font(label_face, detail, usable,
                                         16, 13), SOFT)
        gauge = pygame.Rect(1059, 552, 109, 20)
        self._plate(scene, gauge, border=COPPER)
        displayed_charge = (self.charge if self.status == "ready"
                            else self.ball.power)
        fill = round(99 * displayed_charge)
        if fill:
            pygame.draw.rect(scene, AMBER,
                             (gauge.x + 5, gauge.y + 5, fill, 10),
                             border_radius=3)
        power_text = "POWER {}%".format(round(displayed_charge * 100))
        self._centered_text(scene, power_text,
                            pygame.Rect(1055, 576, 118, 29),
                            self._fitted_font(label_face, power_text,
                                              108, 16, 12), GOLD)
        self._text(scene, "ESC", rx, 635,
                   self._theme_font(label_face, 18, True), CREAM)
        pause_text = "PAUSE / MENU"
        self._text(scene, pause_text, rx, 662,
                   self._fitted_font(label_face, pause_text, usable,
                                     16, 12), TURQUOISE)

        # Подсказка запуска показывается без непрозрачной плашки.
        if self.status == "ready" and not self.menu_open:
            message, color = "HOLD + RELEASE", CREAM
        elif self.message_timer > 0:
            message, color = self.message, GOLD
        else:
            message = None
        if message:
            font = self._fitted_font("Georgia", message, 300, 25, 16)
            label = font.render(message, True, color)
            label_rect = label.get_rect(center=(628, 604))
            shadow = font.render(message, True, (5, 24, 23))
            scene.blit(shadow, label_rect.move(2, 2))
            scene.blit(label, label_rect)

    def _skill_and_heat_feedback(self, scene):
        """Показывает Perfect Flip и состояние перегрева."""
        age = self.ambient_time
        if self.overheat_remaining > 0 and self.status != "over":
            level = (math.sin(age * 8) + 1) * .5
            glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            glow.fill((228, 92, 33, round(3 + level * 9)))
            for x in (310, 1018):
                pygame.draw.line(glow,
                                 (255, 107, 41, round(35 + 65 * level)),
                                 (x, 110), (x, 770), 11)
            for x, y in ((626, 274), (526, 369), (733, 369)):
                pygame.draw.circle(glow,
                                   (255, 146, 45, round(15 + 20 * level)),
                                   (x, y), 65)
            scene.blit(glow, (0, 0))
        if getattr(self, "overheat_banner_time", 0) > 0:
            title = self._theme_font("Copperplate", 41, True)
            text = title.render("OVERHEAT!", True, (255, 167, 86))
            rect = text.get_rect(center=(628, 454))
            shadow = title.render("OVERHEAT!", True, (33, 21, 20))
            scene.blit(shadow, rect.move(3, 4))
            scene.blit(text, rect)
        if getattr(self, "perfect_banner_time", 0) > 0:
            font = self._theme_font("Copperplate", 29, True)
            words = "PERFECT FLIP  {}".format(
                getattr(self, "perfect_label", "+125")
            )
            text = font.render(words, True, (159, 247, 228))
            rect = text.get_rect(center=(628, 662))
            shadow = font.render(words, True, (9, 35, 34))
            scene.blit(shadow, rect.move(2, 3))
            scene.blit(text, rect)

    @staticmethod
    def _end_button(scene, rect, caption, enabled, hovered):
        """Рисует кнопку на экране паузы или конца партии."""
        shadow = rect.move(0, 5)
        pygame.draw.rect(scene, (7, 17, 17), shadow,
                         border_radius=10)
        outer = (244, 190, 97) if hovered and enabled else (174, 110, 51)
        inside = ((24, 104, 92) if hovered else (17, 67, 65))
        if not enabled:
            outer, inside = (79, 72, 58), (31, 40, 40)
        pygame.draw.rect(scene, (73, 41, 27), rect,
                         border_radius=10)
        pygame.draw.rect(scene, outer, rect, 3,
                         border_radius=10)
        inset = rect.inflate(-9, -10)
        pygame.draw.rect(scene, inside, inset,
                         border_radius=6)
        pygame.draw.line(scene,
                         (255, 240, 160) if enabled else (91, 87, 71),
                         (inset.x + 9, inset.y + 3),
                         (inset.right - 9, inset.y + 3), 2)
        for x in (rect.x + 10, rect.right - 10):
            pygame.draw.circle(scene, (198, 144, 70)
                               if enabled else (76, 71, 63),
                               (x, rect.centery), 3)
        font = pygame.font.Font(None, 28)
        color = (255, 232, 172) if enabled else (124, 125, 114)
        label = font.render(caption, True, color)
        scene.blit(label, label.get_rect(center=rect.center))

    def _modal_overlay(self, scene, finished):
        """Рисует центральную панель паузы или Game Over."""
        age = (self.game_over_elapsed if finished
               else getattr(self, "menu_elapsed", 0.0))
        fade = min(1.0, age / 0.35)
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((2, 10, 13, round(199 * fade)))
        scene.blit(veil, (0, 0))

        # Центр общего окна: (600, 420), а не центр игрового поля.
        panel = pygame.Rect(267, 192, 666, 456)
        pygame.draw.rect(scene, (2, 13, 15), panel.move(5, 8),
                         border_radius=23)
        pygame.draw.rect(scene, (92, 48, 28), panel,
                         border_radius=23)
        pygame.draw.rect(scene, (241, 174, 79), panel, 5,
                         border_radius=23)
        inner = panel.inflate(-18, -19)
        pygame.draw.rect(scene, (11, 41, 42), inner,
                         border_radius=17)
        pygame.draw.rect(scene, (49, 125, 108), inner, 2,
                         border_radius=17)
        for x in (panel.x + 20, panel.right - 20):
            for y in (panel.y + 20, panel.bottom - 20):
                pygame.draw.circle(scene, (181, 117, 59), (x, y), 6)
                pygame.draw.circle(scene, (245, 212, 149),
                                   (x - 1, y - 1), 2)

        # Небольшие лампы расположены по верхней дуге меню.
        for n in range(9):
            x = 368 + n * 58
            brightness = (math.sin(age * 4 + n * .78) + 1) * .5
            warm = round(120 + 130 * brightness)
            pygame.draw.circle(scene, (warm, round(warm * .68), 46),
                               (x, 231), 4)

        title = "GAME OVER" if finished else "PAUSED"
        self._centered_text(scene, title,
                            pygame.Rect(329, 242, 542, 59),
                            self._theme_font("Georgia", 54, True),
                            (255, 211, 129))
        self._centered_text(scene, "FINAL SCORE" if finished
                            else "CURRENT SCORE",
                            pygame.Rect(432, 306, 336, 27),
                            pygame.font.Font(None, 25),
                            (149, 214, 194))
        progress = (min(1.0, max(0.0, (age - .15) / 1.05))
                    if finished else 1.0)
        shown = round(self.score * (1 - (1-progress) ** 3))
        score_plate = pygame.Rect(420, 346, 360, 79)
        self._plate(scene, score_plate, border=(245, 186, 87))
        self._centered_text(scene, "{:06d}".format(shown),
                            score_plate, pygame.font.Font(None, 62),
                            (255, 232, 176))
        self._centered_text(scene, "BEST {:06d}".format(self.best),
                            pygame.Rect(444, 434, 312, 28),
                            pygame.font.Font(None, 24),
                            (142, 212, 196))

        # Resume работает только на экране паузы.
        pointer = getattr(pygame, "mouse", None)
        try:
            mouse = (self.scene_mouse(pointer.get_pos())
                     if pointer else None)
        except (AttributeError, TypeError):
            mouse = None
        if not finished:
            resume = self.resume_button()
            hover = mouse is not None and resume.collidepoint(mouse)
            self._end_button(scene, resume, "RESUME GAME", True, hover)

        for name, text in (("restart", "RESTART"),
                           ("menu", "MENU"),
                           ("quit", "QUIT GAME")):
            rect = self.end_buttons()[name]
            enabled = name != "menu"
            hovered = (enabled and mouse is not None
                       and rect.collidepoint(mouse))
            self._end_button(scene, rect, text, enabled, hovered)
        info = ("ESC - RESUME GAME" if not finished
                else "PRESS RESTART FOR A NEW ROUND")
        self._centered_text(scene, info,
                            pygame.Rect(361, 613, 478, 25),
                            pygame.font.Font(None, 21),
                            (129, 170, 156))

    def _game_over_overlay(self, scene):
        """Сохраняет интерфейс вызова экрана Game Over."""
        self._modal_overlay(scene, finished=True)

    def draw(self, surface):
        """Рисует кадр и масштабирует его под размер окна."""
        scene = self.scene
        self._table_background(scene)
        self._table_art(scene)
        self._hud(scene)
        self._combo_ambience(scene)
        self._skill_and_heat_feedback(scene)
        self._combo_banner(scene)
        if self.status == "over":
            self._game_over_overlay(scene)
        elif self.menu_open:
            self._modal_overlay(scene, finished=False)

        # Небольшое смещение кадра подчёркивает сильные удары.
        shake = getattr(self, "shake_time", 0.0)
        dx = round(2 * math.sin(shake * 117)) if shake > 0 else 0
        dy = round(2 * math.sin(shake * 83)) if shake > 0 else 0
        if surface.get_size() == (WIDTH, HEIGHT):
            surface.fill(DARK)
            surface.blit(scene, (dx, dy))
        else:
            scaled = pygame.transform.smoothscale(scene, surface.get_size())
            surface.fill(DARK)
            surface.blit(scaled, (dx, dy))
