"""Отрисовка игрового поля и интерфейса Pinball."""

import pygame

from src.pinball.config import (
    BOTTOM, BRASS, CREAM, FLOOR, FLOOR_ALT, HEIGHT, INK,
    LEFT, METAL, RED, RIGHT, SHADOW, SOFT, TOP, WIDTH,
)


class PinballRenderer:
    """Отдельные методы визуализации, используемые классом PinballGame."""

    def _text(self, surface, text, x, y, font=None, color=CREAM):
        """Draw one clear HUD label."""
        font = font or self.font_medium
        surface.blit(font.render(str(text), True, color), (x, y))

    def _table_background(self, scene):
        """Draw a restrained retro-industrial table rather than neon lines."""
        scene.fill(INK)
        # Side panel uses a dense matte finish and restrained accents.
        # Боковые панели предназначены для счёта и подсказок.
        pygame.draw.rect(scene, (23, 32, 46), (14, 20, 259, 795),
                         border_radius=12)
        pygame.draw.rect(scene, (23, 32, 46), (1035, 20, 151, 795),
                         border_radius=12)
        pygame.draw.line(scene, BRASS, (28, 242), (250, 242), 3)
        pygame.draw.line(scene, BRASS, (1050, 242), (1170, 242), 3)
        # Layered steel enclosure and inset playfield.
        # Корпус отделён от внутреннего игрового поля.
        pygame.draw.rect(scene, (7, 13, 21),
                         (299, 39, 734, 772), border_radius=29)
        pygame.draw.rect(scene, METAL,
                         (299, 39, 734, 772), 5, border_radius=29)
        pygame.draw.rect(scene, (73, 80, 83),
                         (309, 49, 716, 751), 6, border_radius=25)
        pygame.draw.rect(scene, FLOOR,
                         (316, 63, 702, 728), border_radius=19)
        pygame.draw.rect(scene, FLOOR_ALT,
                         (LEFT, TOP, RIGHT - LEFT, BOTTOM - TOP))
        # Орбитальный рисунок здесь только фон, не препятствие.
        # Thin gold compass / orbital decoration behind the mechanics.
        for radius in (135, 205, 265):
            pygame.draw.circle(scene, (39, 66, 83),
                               (628, 371), radius, 2)
        pygame.draw.line(scene, (39, 66, 83), (628, 114), (628, 628), 2)
        pygame.draw.line(scene, (39, 66, 83), (367, 371), (893, 371), 2)
        for x in range(390, 905, 75):
            pygame.draw.circle(scene, (62, 92, 104), (x, 592), 2)
        # Separate spring channel on the right with an actual divider.
        # Справа изображаем отдельный пусковой канал.
        pygame.draw.rect(scene, (15, 27, 40), (960, 80, 50, 711))
        pygame.draw.line(scene, METAL, (957, 192), (957, 787), 6)
        pygame.draw.line(scene, BRASS, (1008, 104), (1008, 787), 4)
        for y in range(594, 750, 24):
            pygame.draw.line(scene, (95, 112, 123),
                             (971, y + 10), (1000, y), 2)
        # Frame walls are solid in Ball.advance(); drain remains open.
        pygame.draw.line(scene, METAL, (LEFT, TOP), (RIGHT, TOP), 5)
        pygame.draw.line(scene, METAL, (LEFT, TOP), (LEFT, BOTTOM), 5)
        pygame.draw.line(scene, METAL, (RIGHT, TOP), (RIGHT, BOTTOM), 5)
        # The central drain is truly open between the paddle tips.
        # It is drawn from the same collision geometry as the flippers.
        # Центральный слив отслеживает реальное положение ракеток.
        left_tip = self.left_flipper.endpoints()[1]
        right_tip = self.right_flipper.endpoints()[1]
        drain_left = round(left_tip.x + self.left_flipper.thickness / 2)
        drain_right = round(right_tip.x - self.right_flipper.thickness / 2)
        pygame.draw.polygon(
            scene, SHADOW,
            [(drain_left, 746), (drain_right, 746),
             (drain_right + 10, BOTTOM - 2),
             (drain_left - 10, BOTTOM - 2)],
        )
        pygame.draw.line(
            scene, BRASS, (drain_left, 746),
            (drain_left - 10, BOTTOM - 3), 3,
        )
        pygame.draw.line(
            scene, BRASS, (drain_right, 746),
            (drain_right + 10, BOTTOM - 3), 3,
        )
        # Both side drains stay visually open; avoid fake dark blocks.
        for x in (325, 1027):
            for y in (102, 170, 680, 760):
                pygame.draw.circle(scene, BRASS, (x, y), 4)

    def _table_art(self, scene):
        """Draw rails and all physical targets directly on the table."""
        # Сначала направляющие и мишени, затем ракетки и шарик.
        for rail in self.rails:
            rail.draw(scene)
        for bumper in self.bumpers:
            bumper.draw(scene)
        for target in self.targets:
            target.draw(scene)
        for flipper in (self.left_flipper, self.right_flipper):
            flipper.draw(scene)
        self._text(scene, "DRAIN", 598, 762, self.font_small, RED)
        if self.status != "over":
            self.ball.draw(scene)
        # Side drains are real exit zones, not painted obstacles.
        self._text(scene, "SIDE DRAIN", 331, 744,
                   self.font_small, SOFT)
        self._text(scene, "SIDE DRAIN", 836, 744,
                   self.font_small, SOFT)
        # Plunger shows how much energy has been stored.
        pygame.draw.rect(scene, METAL, (976, 696, 20, 73), 2)
        level = round(62 * self.charge)
        pygame.draw.rect(scene, BRASS, (980, 763 - level, 12, level))

    def _hud(self, scene):
        """Draw score, remaining balls, keyboard help, and game messages."""
        self._text(scene, "PINBALL", 32, 74, self.font_large, CREAM)
        self._text(scene, "ARCADE MODE", 34, 132,
                   self.font_small, BRASS)
        # Информационная часть отдельно от физического поля.
        self._text(scene, "SCORE", 33, 267, self.font_small, SOFT)
        self._text(scene, self.score, 30, 302, self.font_large, CREAM)
        self._text(scene, "BEST", 33, 402, self.font_small, SOFT)
        self._text(scene, self.best, 33, 433, self.font_medium, BRASS)
        self._text(scene, "BALLS", 33, 540, self.font_small, SOFT)
        self._text(scene, self.lives, 33, 567, self.font_large, CREAM)
        self._text(scene, "A  /  <-", 1050, 283,
                   self.font_small, CREAM)
        self._text(scene, "LEFT PADDLE", 1050, 311,
                   self.font_small, SOFT)
        self._text(scene, "D  /  ->", 1050, 365,
                   self.font_small, CREAM)
        self._text(scene, "RIGHT PADDLE", 1050, 393,
                   self.font_small, SOFT)
        self._text(scene, "SPACE", 1050, 461,
                   self.font_small, CREAM)
        self._text(scene, "LAUNCH", 1050, 489,
                   self.font_small, SOFT)
        self._text(scene, "P: pause", 1050, 583,
                   self.font_small, CREAM)
        self._text(scene, "R: restart", 1050, 618,
                   self.font_small, CREAM)
        self._text(scene, "+100  POPS", 1050, 730,
                   self.font_small, BRASS)
        self._text(scene, "3 BALLS PER GAME", 1050, 774,
                   self.font_small, SOFT)
        # Текст сообщения зависит от состояния партии.
        if self.status in ("ready", "paused", "over"):
            text = {"ready": "READY - HOLD SPACE AND RELEASE",
                    "paused": "PAUSED - PRESS P",
                    "over": "GAME OVER - PRESS R"}[self.status]
            panel = pygame.Surface((450, 48), pygame.SRCALPHA)
            panel.fill((12, 23, 34, 216))
            scene.blit(panel, (405, 615))
            font = self.font_small
            label = font.render(text, True, CREAM)
            scene.blit(label, label.get_rect(center=(630, 639)))
        elif self.message_timer > 0:
            label = self.font_medium.render(self.message, True, BRASS)
            scene.blit(label, label.get_rect(center=(630, 614)))

    def draw(self, surface):
        """Render the entire game to a host surface of any resolution."""
        scene = self.scene
        self._table_background(scene)
        self._table_art(scene)
        self._hud(scene)
        # Сохраняем совместимость с меньшим окном приложения Влада.
        if surface.get_size() == (WIDTH, HEIGHT):
            surface.blit(scene, (0, 0))
        else:
            scaled = pygame.transform.smoothscale(scene, surface.get_size())
            surface.blit(scaled, (0, 0))
