"""Управление игрой, обработка событий и начисление очков."""

import math

import pygame

from src.pinball.config import (
    BLUE, BOTTOM, BRASS, HEIGHT, METAL, RED, STEP, TEAL, WIDTH,
)
from src.pinball.objects import Ball, Bumper, Flipper, Rail, Standup
from src.pinball.mechanisms import DropTarget, LaneSensor, Slingshot
from src.pinball.renderer import PinballRenderer
from src.pinball.sound import PinballSounds


class PinballGame(PinballRenderer):
    """Хранит состояние партии и выполняет шаги игровой логики."""

    def __init__(self, width=WIDTH, height=HEIGHT):
        """Создаёт шарик, флипперы, препятствия и систему очков."""
        if not pygame.font.get_init():
            pygame.font.init()
        # Рисуем в базовом разрешении; окно масштабируется отдельно.
        self.scene = pygame.Surface((WIDTH, HEIGHT))
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 33)
        self.font_small = pygame.font.Font(None, 26)
        # Основные подвижные объекты игрового стола.
        self.ball = Ball()
        self.left_flipper = Flipper(482, 710, 1, RED)
        self.right_flipper = Flipper(772, 710, -1, TEAL)
        # Оставляем по одной нижней направляющей с каждой стороны.
        # Так шарик не застревает между парными ограждениями.
        self.rails = []
        # Верхняя арка состоит из нескольких прямых отрезков.
        route_groups = [
            ([(368, 213), (368, 170), (414, 127), (482, 107),
              (776, 107), (845, 126), (897, 185)], BRASS, 8),
            ([(335, 560), (467, 685)], METAL, 8),
            ([(935, 560), (787, 685)], METAL, 8),
            # Боковые направляющие участвуют в физике и не касаются бамперов.
            ([(410, 432), (447, 476)], TEAL, 6),
            ([(844, 432), (807, 476)], TEAL, 6),
        ]
        for points, color, thickness in route_groups:
            for before, after in zip(points, points[1:]):
                self.rails.append(Rail(before, after, color, thickness))
        # За контакт с каждым бампером начисляются очки.
        self.bumpers = [
            Bumper(626, 274, 36, BRASS),
            Bumper(526, 369, 32, RED),
            Bumper(733, 369, 32, TEAL),
            # Нижние боковые бамперы имеют настоящие коллайдеры.
            Bumper(428, 535, 22, BLUE, points=75),
            Bumper(828, 535, 22, BLUE, points=75),
        ]
        self._held_flipper_keys = {"left": set(), "right": set()}
        # Для каждой мишени задан свой номинал очков.
        self.targets = [
            Standup(521, 178, BLUE, 150),
            Standup(628, 166, BRASS, 150),
            Standup(736, 178, BLUE, 150),
            Standup(395, 454, RED, 100),
            Standup(865, 454, TEAL, 100),
        ]
        # Поражённые мишени не поднимаются до следующего шара.
        self.drop_targets = [
            DropTarget(556, 475),
            DropTarget(626, 475),
            DropTarget(696, 475),
        ]
        # Слинги расположены отдельно от флипперов и направляющих.
        self.slingshots = [
            # Уменьшенные пластины не перекрывают нижние проходы.
            Slingshot(((492, 592), (526, 611), (496, 633)), 1),
            Slingshot(((764, 592), (730, 611), (760, 633)), -1),
        ]
        # Датчики ускоряют шарик при входе, но не создают стенок.
        self.lanes = [
            LaneSensor(413, 303, points=175),
            LaneSensor(843, 303, points=175),
        ]
        self.top_hits = set()
        self.bank_completed = False
        self.sounds = PinballSounds()
        self.ambient_time = 0.0
        self.restart()

    def restart(self):
        """Начинает новую партию с тремя шарами и нулевым счётом."""
        self.best = max(getattr(self, "best", 0),
                        getattr(self, "score", 0))
        self.score = 0
        self.lives = 3
        self.status = "ready"
        self.ball.reset()
        self.charging = False
        self.charge = 0.0
        self.ball_age = 0.0
        self.corner_dwell = 0.0
        self.saver_used = False
        # Состояние серии попаданий и временного множителя очков.
        self.pop_chain = 0
        self.pop_window = 0.0
        self.combo_remaining = 0.0
        self.combo_flash = 0.0
        self.combo_banner_time = 0.0
        # Перегрев меняет только звук и освещение, а не физику шарика.
        self.heat = 0.0
        self.overheat_remaining = 0.0
        self.overheat_cooldown = 0.0
        self.overheat_banner_time = 0.0
        self.perfect_banner_time = 0.0
        self.perfect_side = ""
        self.perfect_label = ""
        # Очередь попаданий читается рендерером один раз за кадр.
        self.point_events = []
        self.game_over_elapsed = 0.0
        self.quit_requested = False
        self.menu_open = False
        self.menu_elapsed = 0.0
        self.score_pulse = 0.0
        self.shake_time = 0.0
        self._held_flipper_keys = {"left": set(), "right": set()}
        self.message = ""
        self.message_timer = 0.0
        self.left_flipper.lift = 0.0
        self.right_flipper.lift = 0.0
        self._reset_features()

    def _reset_features(self):
        """Восстанавливает мишени и датчики перед новым шаром."""
        self.top_hits.clear()
        self.bank_completed = False
        for target in self.drop_targets:
            target.reset()
        for sling in self.slingshots:
            sling.flash = 0.0
            sling.cooldown = 0.0
        for lane in self.lanes:
            lane.reset()

    @staticmethod
    def _flipper_control(event):
        """Определяет флиппер по физическому коду клавиши."""
        scancode = getattr(event, "scancode", None)

        # Скан-коды SDL не зависят от активной раскладки клавиатуры.
        if scancode is not None:
            if scancode in (pygame.KSCAN_A, pygame.KSCAN_LEFT):
                return "left"
            if scancode in (pygame.KSCAN_D, pygame.KSCAN_RIGHT):
                return "right"
            return None

        # Для синтетических событий поддерживаем обычные коды клавиш.
        if event.key in (pygame.K_a, pygame.K_LEFT):
            return "left"
        if event.key in (pygame.K_d, pygame.K_RIGHT):
            return "right"
        return None

    def _play_sound(self, name):
        """Воспроизводит эффект, если звуковая система доступна."""
        sounds = getattr(self, "sounds", None)
        if sounds is not None:
            sounds.play(name)

    def _toggle_menu(self):
        """Переключает экран паузы, не сбрасывая партию."""
        if self.status == "over":
            return
        self.menu_open = not self.menu_open
        self.menu_elapsed = 0.0
        self.charging = False
        for held in self._held_flipper_keys.values():
            held.clear()
        self._play_sound("button")

    def handle_event(self, event):
        """Обрабатывает нажатия клавиш и клики по меню."""
        if (event.type == getattr(pygame, "MOUSEBUTTONDOWN", -100)
                and getattr(event, "button", 0) == 1
                and (self.status == "over" or self.menu_open)):
            self._on_end_click(event.pos)
            return

        if event.type == pygame.KEYDOWN:
            physical = getattr(event, "scancode", None)
            if (event.key == pygame.K_ESCAPE
                    or physical == getattr(pygame, "KSCAN_ESCAPE", 41)):
                self._toggle_menu()
                return

        # На паузе блокируем управление флипперами и запуском.
        if self.menu_open or self.status == "over":
            return
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            control = self._flipper_control(event)
            if control is not None:
                scan = getattr(event, "scancode", None)
                key_id = ("scan", scan) if scan is not None else (
                    "key", event.key
                )
                held = self._held_flipper_keys[control]
                if event.type == pygame.KEYDOWN:
                    if key_id not in held:
                        self._play_sound("flipper")
                    held.add(key_id)
                else:
                    held.discard(key_id)

            # Клавиши P и R не назначены: пауза открывается через Esc.
            if event.type == pygame.KEYDOWN:
                physical = getattr(event, "scancode", None)
                if (event.key == pygame.K_SPACE
                        or physical == getattr(pygame, "KSCAN_SPACE", 44)):
                    if self.status == "ready":
                        self.charging = True
            elif event.type == pygame.KEYUP:
                physical = getattr(event, "scancode", None)
                if ((event.key == pygame.K_SPACE
                     or physical == getattr(pygame, "KSCAN_SPACE", 44))
                        and self.charging):
                    self.charging = False
                    if self.status == "ready":
                        self.ball.launch(self.charge)
                        self.status = "playing"
                        self._play_sound("launch")
                        self.charge = 0.0
        elif event.type == getattr(pygame, "WINDOWFOCUSLOST", None):
            for held in self._held_flipper_keys.values():
                held.clear()

    @staticmethod
    def end_buttons():
        """Возвращает области кнопок Restart, Menu и Quit."""
        return {
            "restart": pygame.Rect(342, 548, 164, 55),
            "menu": pygame.Rect(518, 548, 164, 55),
            "quit": pygame.Rect(694, 548, 164, 55),
        }

    @staticmethod
    def resume_button():
        """Возвращает область кнопки Resume на экране паузы."""
        return pygame.Rect(499, 480, 202, 52)

    @staticmethod
    def scene_mouse(position):
        """Пересчитывает координаты мыши в разрешение игры."""
        host = pygame.display.get_surface()
        if host is None:
            return position
        width, height = host.get_size()
        if width <= 0 or height <= 0:
            return position
        return (position[0] * WIDTH / width,
                position[1] * HEIGHT / height)

    def _on_end_click(self, position):
        """Выполняет действие выбранной кнопки меню."""
        x, y = self.scene_mouse(position)
        buttons = self.end_buttons()
        if (self.status != "over" and self.menu_open
                and self.resume_button().collidepoint(x, y)):
            self.menu_open = False
            self.menu_elapsed = 0.0
            self._play_sound("button")
            return "resume"
        if buttons["restart"].collidepoint(x, y):
            self._play_sound("button")
            self.restart()
            return "restart"
        if buttons["quit"].collidepoint(x, y):
            self._play_sound("button")
            self.quit_requested = True
            pygame.event.post(pygame.event.Event(pygame.QUIT, {}))
            return "quit"
        # Переход в общее меню добавим при объединении двух игр.
        return None

    def _lost_ball(self):
        """Обрабатывает потерю шара и конец партии."""
        self._play_sound("drain")
        self.shake_time = 0.16
        self.lives -= 1
        if self.lives <= 0:
            self.status = "over"
            self.message = "GAME OVER"
            # Мелодию проигрыша включаем только при потере последнего шара.
            self._play_sound("game_over")
        else:
            self.ball.reset()
            self.status = "ready"
            self.charging = False
            self.charge = 0.0
            self.message = "BALL LOST"
        self.message_timer = 1.2
        self.corner_dwell = 0.0
        self.pop_chain = 0
        self.pop_window = 0.0
        self.combo_remaining = 0.0
        self.combo_flash = 0.0
        self.combo_banner_time = 0.0
        self.heat = 0.0
        self.overheat_remaining = 0.0
        self.overheat_cooldown = 0.0
        self.overheat_banner_time = 0.0
        self.perfect_banner_time = 0.0
        self.perfect_label = ""
        self.point_events.clear()
        if self.status == "over":
            self.game_over_elapsed = 0.0
        self._reset_features()

    @staticmethod
    def scoring_label(points, multiplier):
        """Формирует короткую надпись с очками и множителем."""
        if multiplier > 1:
            # Окончательная сумма уже показана на общем табло.
            return "{} ×{}".format(points, multiplier)
        return "+{}".format(points)

    def _add_heat(self, source):
        """Увеличивает нагрев по результативным столкновениям."""
        if (source == "bonus" or self.overheat_remaining > 0
                or self.overheat_cooldown > 0):
            return
        amount = {
            "pop": 18, "perfect": 20, "lane": 11, "other": 9,
        }.get(source, 9)
        self.heat = min(100.0, self.heat + amount)
        if self.heat >= 100:
            self.overheat_remaining = 6.0
            self.overheat_banner_time = 1.55
            self.heat = 100.0
            self._play_sound("overheat")

    def _award(self, points, source="other", position=None):
        """Начисляет очки и сохраняет сведения для визуальных эффектов."""
        if not points:
            return 0

        if source == "pop":
            if self.pop_window <= 0:
                self.pop_chain = 0
            self.pop_chain += 1
            self.pop_window = 6.0
            if self.pop_chain >= 3:
                self.pop_chain = 0
                self.combo_remaining = 9.0
                self.combo_flash = 1.0
                self.combo_banner_time = 1.9
                self._play_sound("combo")
        elif source != "perfect":
            # Бонус за точный удар не сбрасывает текущую серию.
            self.pop_chain = 0
            self.pop_window = 0.0

        # Нагрев растёт от попаданий, а не от прошедшего времени.
        self._add_heat(source)
        factor = 2 if self.combo_remaining > 0 else 1
        earned = points * factor
        self.score += earned
        self.score_pulse = 0.20
        self.best = max(self.score, self.best)

        if position is None:
            position = (628, 530)
        # Координаты храним обычным кортежем, без зависимости от Pygame.
        try:
            center = (round(position.x), round(position.y))
        except AttributeError:
            center = (round(position[0]), round(position[1]))
        self.point_events.append({
            "center": center,
            "points": points,
            "multiplier": factor,
            "earned": earned,
            "source": source,
        })
        # Ограничиваем историю событий, даже если кадры не рисуются.
        self.point_events = self.point_events[-36:]

        if source == "pop":
            self._play_sound("hot_pop" if self.overheat_remaining > 0
                             else "pop")
            self.shake_time = max(self.shake_time, 0.09)
        elif source == "perfect":
            self._play_sound("perfect")
            self.shake_time = max(self.shake_time, 0.13)
        elif source == "lane":
            self._play_sound("lane")
        else:
            self._play_sound("target")
        if earned >= 600:
            self.shake_time = max(self.shake_time, 0.15)

        # Эффект использует исходные очки и множитель на момент удара.
        # Фактически начисленная сумма сохраняется отдельно.
        self.message = self.scoring_label(points, factor)
        self.message_timer = 0.78
        return earned

    def _physics_step(self, dt):
        """Выполняет один шаг расчёта движения и столкновений."""
        self.ball.advance(dt)
        if self.ball.mode != "play":
            return
        # Каждый вид препятствий обрабатывается своим коллайдером.
        for rail in self.rails:
            rail.hit(self.ball)
        for bumper in self.bumpers:
            self._award(bumper.hit(self.ball),
                        source="pop" if bumper.points >= 100 else "other",
                        position=bumper.center)
        for index, target in enumerate(self.targets):
            points = target.hit(self.ball)
            self._award(points, position=target.center)
            # Три разные верхние мишени дают дополнительный бонус.
            if points and index < 3:
                self.top_hits.add(index)
                if len(self.top_hits) == 3:
                    self._award(600, source="bonus",
                                position=self.targets[1].center)
                    self.message = "TOP THREE " + self.scoring_label(
                        600, 2 if self.combo_remaining > 0 else 1,
                    )
                    self.top_hits.clear()
        # Награда за всю группу мишеней выдаётся один раз за шар.
        for target in self.drop_targets:
            self._award(target.hit(self.ball), position=target.center)
        if (not self.bank_completed and
                all(not target.active for target in self.drop_targets)):
            self._award(850, source="bonus", position=(628, 475))
            self.message = "BANK COMPLETE " + self.scoring_label(
                850, 2 if self.combo_remaining > 0 else 1,
            )
            self.bank_completed = True
        # Магнитные датчики изменяют скорость без твёрдой стенки.
        for lane in self.lanes:
            self._award(lane.hit(self.ball), source="lane",
                        position=lane.center)
        # У слингов ограниченная сила отскока, чтобы не зациклить шар.
        for sling in self.slingshots:
            self._award(sling.hit(self.ball), position=sling.center)
        # Perfect Flip засчитывается при активном ударе концом флиппера.
        for flipper, side in ((self.left_flipper, "LEFT"),
                              (self.right_flipper, "RIGHT")):
            if flipper.hit(self.ball) and flipper.last_hit_perfect:
                self._award(125, source="perfect",
                            position=self.ball.position)
                self.perfect_banner_time = 1.15
                self.perfect_side = side
                self.perfect_label = self.scoring_label(
                    125, 2 if self.combo_remaining > 0 else 1,
                )
        # Из тесного угла выталкиваем шарик, не телепортируя его.
        in_corner = (
            874 < self.ball.position.x < 951
            and 90 < self.ball.position.y < 233
        )
        self.corner_dwell = (
            self.corner_dwell + dt if in_corner else 0.0
        )
        if self.corner_dwell > 0.95:
            self.ball.velocity.x = min(self.ball.velocity.x, -270)
            self.ball.velocity.y = max(self.ball.velocity.y, 180)
            self.corner_dwell = 0.0
        self.ball.cap_speed()
        if self.ball.position.y - self.ball.radius > BOTTOM:
            self._lost_ball()

    def update(self, dt):
        """Обновляет игру и выполняет несколько шагов физики."""
        dt = max(0.0, min(dt, 0.050))
        keys = pygame.key.get_pressed()
        left_down = (
            bool(self._held_flipper_keys["left"])
            or keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        right_down = (
            bool(self._held_flipper_keys["right"])
            or keys[pygame.K_d] or keys[pygame.K_RIGHT]
        )
        # На паузе останавливаем физику и таймеры бонусов.
        if self.menu_open:
            self.menu_elapsed = min(8.0, self.menu_elapsed + dt)
            return
        if self.status == "over":
            self.game_over_elapsed = min(8.0, self.game_over_elapsed + dt)
            return
        self.ambient_time += dt
        self.score_pulse = max(0.0, self.score_pulse - dt)
        self.shake_time = max(0.0, self.shake_time - dt)
        if self.status == "ready":
            if self.charging:
                self.charge = min(1.0, self.charge + dt / 0.85)
            self.left_flipper.update(dt, left_down)
            self.right_flipper.update(dt, right_down)
            return
        if self.status != "playing":
            return
        self.ball_age += dt
        self.message_timer = max(0.0, self.message_timer - dt)
        self.pop_window = max(0.0, self.pop_window - dt)
        if self.pop_window <= 0 and self.combo_remaining <= 0:
            self.pop_chain = 0
        self.combo_remaining = max(0.0, self.combo_remaining - dt)
        self.combo_flash = max(0.0, self.combo_flash - dt * 1.4)
        self.combo_banner_time = max(0.0, self.combo_banner_time - dt)
        self.perfect_banner_time = max(0.0,
                                       self.perfect_banner_time - dt)
        self.overheat_banner_time = max(0.0,
                                        self.overheat_banner_time - dt)
        self.overheat_cooldown = max(0.0,
                                     self.overheat_cooldown - dt)
        if self.overheat_remaining > 0:
            self.overheat_remaining = max(0.0,
                                          self.overheat_remaining - dt)
            if self.overheat_remaining == 0:
                self.heat = 22.0
                self.overheat_cooldown = 7.0
        else:
            self.heat = max(0.0, self.heat - 4.0 * dt)
        for bumper in self.bumpers:
            bumper.update(dt)
        for target in self.targets:
            target.update(dt)
        for target in self.drop_targets:
            target.update(dt)
        for sling in self.slingshots:
            sling.update(dt)
        for lane in self.lanes:
            lane.update(dt)
        # Мишени остаются опущенными до следующего шара.
        # Подшаги физики уменьшают риск проскока сквозь препятствия.
        count = max(1, math.ceil(dt / STEP))
        part = dt / count
        for _ in range(count):
            self.left_flipper.update(part, left_down)
            self.right_flipper.update(part, right_down)
            self._physics_step(part)
            if self.status != "playing":
                break
        # След обновляется, только когда шарик движется по полю.
        if self.status == "playing" and self.ball.mode == "play":
            if (not self.ball.trail or
                    (self.ball.position - self.ball.trail[-1]
                     ).length_squared() > 105):
                self.ball.trail.append(self.ball.position.copy())
                self.ball.trail = self.ball.trail[-6:]
