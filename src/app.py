"""Общее приложение с выбором Pong и Pinball из главного меню."""

import pygame

from src.games.pong import PongGame
from src.menu.menu import ArcadeMenu, MENU_SIZE
from src.pinball.config import HEIGHT as PINBALL_HEIGHT
from src.pinball.config import WIDTH as PINBALL_WIDTH
from src.pinball.game import PinballGame
from src.pong.audio import PongSounds
from src.pong.config import HEIGHT as PONG_HEIGHT
from src.pong.config import WIDTH as PONG_WIDTH


class App:
    """Управляет окном, игровым циклом и переходами между режимами."""

    FPS = 60

    def __init__(self):
        """Инициализирует Pygame и открывает меню выбора игры."""
        pygame.init()
        self.screen = pygame.display.set_mode(MENU_SIZE)
        pygame.display.set_caption("Ping-Pong & Pinball — Arcade")
        self.clock = pygame.time.Clock()
        self.is_running = True
        self.mode = "menu"
        self.game = None
        self.menu = ArcadeMenu()
        self.menu_sounds = PongSounds()

    def _open_menu(self):
        """Закрывает текущую игру и восстанавливает стартовое меню."""
        self.game = None
        self.mode = "menu"
        self.screen = pygame.display.set_mode(MENU_SIZE)
        pygame.display.set_caption("Ping-Pong & Pinball — Arcade")

    def _start_game(self, name):
        """Создаёт игровое окно нужного разрешения и новый экземпляр игры."""
        if name == "pong":
            self.screen = pygame.display.set_mode(
                (PONG_WIDTH, PONG_HEIGHT),
            )
            self.game = PongGame(self.screen)
            pygame.display.set_caption("Pong — Neon Showdown")
        elif name == "pinball":
            self.screen = pygame.display.set_mode(
                (PINBALL_WIDTH, PINBALL_HEIGHT),
            )
            self.game = PinballGame()
            pygame.display.set_caption("Pinball — Copper Glass")
        else:
            return
        self.mode = name

    def _menu_action(self, name):
        """Выполняет команду главного меню."""
        if name == "quit":
            self.is_running = False
        elif name in ("pong", "pinball"):
            self.menu_sounds.play("select")
            self._start_game(name)

    def _check_game_requests(self):
        """Читает запросы выхода и возврата из текущей игры."""
        if self.game is None:
            return
        if getattr(self.game, "quit_requested", False):
            self.is_running = False
        elif getattr(self.game, "menu_requested", False):
            self._open_menu()

    def _handle_events(self):
        """Направляет события активному экрану и контролирует выход."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                break
            if self.mode == "menu":
                self._menu_action(self.menu.handle_event(event))
                continue
            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_F1
            ):
                self._open_menu()
                continue
            if self.game is not None:
                self.game.handle_event(event)
            self._check_game_requests()
            if not self.is_running:
                break

    def _update(self, dt):
        """Обновляет выбранную игру либо анимации главного меню."""
        if self.mode == "menu":
            self.menu.update(dt)
        elif self.game is not None:
            self.game.update(dt)
            self._check_game_requests()

    def _draw(self):
        """Отрисовывает текущий экран и выводит кадр."""
        if self.mode == "menu":
            self.menu.draw(self.screen)
        elif self.game is not None:
            self.game.draw(self.screen)
        pygame.display.flip()

    def run(self):
        """Выполняет общий игровой цикл до закрытия приложения."""
        while self.is_running:
            dt = self.clock.tick(self.FPS) / 1000.0
            self._handle_events()
            if not self.is_running:
                break
            self._update(dt)
            self._draw()
        pygame.quit()
