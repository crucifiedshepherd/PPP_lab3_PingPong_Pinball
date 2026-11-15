"""Orbital Workshop pinball: a self-contained two-dimensional arcade table.

The public interface is compatible with the shared Pygame application:
``PinballGame.handle_event(event)``, ``update(dt)``, and ``draw(surface)``.
"""

import math
import pygame


WIDTH = 1200
HEIGHT = 840
FPS = 60
STEP = 1 / 240
GRAVITY = 500.0
TOP_SPEED = 690.0
BALL_RADIUS = 10

LEFT = 320
RIGHT = 950
TOP = 88
BOTTOM = 792
LAUNCH_X = 985
LAUNCH_Y = 741

INK = (15, 22, 34)
FLOOR = (27, 44, 61)
FLOOR_ALT = (32, 54, 74)
METAL = (154, 167, 170)
CREAM = (239, 229, 204)
BRASS = (222, 174, 91)
RED = (212, 83, 91)
TEAL = (84, 187, 183)
BLUE = (97, 140, 184)
SHADOW = (8, 16, 27)
SOFT = (147, 164, 171)


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
    along = (ball.position - start).dot(edge) / denominator
    along = max(0.0, min(1.0, along))
    nearest = start + edge * along
    difference = ball.position - nearest
    limit = ball.radius + thickness * 0.5
    distance_squared = difference.length_squared()
    if distance_squared > limit * limit:
        return None
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


class Ball:
    """Store ball movement, launch state, and motion trail."""

    def __init__(self):
        """Create one ball in its launch trough."""
        self.radius = BALL_RADIUS
        self.position = pygame.Vector2(LAUNCH_X, LAUNCH_Y)
        self.velocity = pygame.Vector2(0, 0)
        self.mode = "ready"
        self.power = 0.0
        self.trail = []

    def reset(self):
        """Place the ball back on the spring without starting it."""
        self.position.update(LAUNCH_X, LAUNCH_Y)
        self.velocity.update(0, 0)
        self.mode = "ready"
        self.trail.clear()

    def launch(self, power):
        """Send the ball up the separate launch lane."""
        self.power = max(0.0, min(1.0, power))
        self.velocity.update(0, -(960 + 150 * self.power))
        self.mode = "lane"
        self.trail.clear()

    def cap_speed(self):
        """Keep the ball fast enough to play but slow enough to follow."""
        length_sq = self.velocity.length_squared()
        if length_sq > TOP_SPEED * TOP_SPEED:
            self.velocity.scale_to_length(TOP_SPEED)

    def advance(self, dt):
        """Integrate gravity, launch lane, and outside walls."""
        if self.mode not in ("lane", "play"):
            return
        self.velocity.y += GRAVITY * dt
        if self.mode == "play":
            self.cap_speed()
        self.position += self.velocity * dt

        if self.mode == "lane":
            self.position.x = LAUNCH_X
            if self.position.y <= 119:
                # The ball leaves the one-way launch lane above the table.
                self.mode = "play"
                self.position.update(891, 137)
                self.velocity.update(-220 - 140 * self.power, 90)
            return

        if self.position.x - self.radius < LEFT:
            self.position.x = LEFT + self.radius
            self.velocity.x = abs(self.velocity.x) * 0.91
        if self.position.x + self.radius > RIGHT:
            self.position.x = RIGHT - self.radius
            self.velocity.x = -abs(self.velocity.x) * 0.91
        if self.position.y - self.radius < TOP:
            self.position.y = TOP + self.radius
            self.velocity.y = abs(self.velocity.y) * 0.91

    def draw(self, surface):
        """Draw a metal ball, a small shine, and a subtle short trail."""
        for index, location in enumerate(self.trail):
            strength = (index + 1) / (len(self.trail) + 1)
            color = (
                int(54 + 58 * strength),
                int(89 + 45 * strength),
                int(106 + 30 * strength),
            )
            pygame.draw.circle(surface, color, pos(location), 3 + index // 3)
        at = pos(self.position)
        pygame.draw.circle(surface, SHADOW, (at[0] + 3, at[1] + 4), 14)
        pygame.draw.circle(surface, METAL, at, self.radius + 1)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 3), 4)


class Rail:
    """A drawn and collidable section of metal guardrail."""

    def __init__(self, a, b, color=METAL, width=7, bounce=0.82):
        """Remember the exact collision segment."""
        self.a = pygame.Vector2(a)
        self.b = pygame.Vector2(b)
        self.color = color
        self.width = width
        self.bounce = bounce

    def hit(self, ball):
        """Separate the ball and reflect it on an incoming impact."""
        contact = circle_segment(ball, self.a, self.b, self.width)
        if contact is None:
            return False
        nearest, normal, distance, _ = contact
        ball.position = nearest + normal * (distance + 0.2)
        return reflect_velocity(ball.velocity, normal, self.bounce)

    def draw(self, surface):
        """Render the metal guardrail with a shadow and highlight."""
        pygame.draw.line(
            surface, SHADOW, self.a + (2, 3), self.b + (2, 3),
            self.width + 6,
        )
        pygame.draw.line(surface, self.color, self.a, self.b, self.width)
        pygame.draw.line(surface, CREAM, self.a, self.b, 2)


class Flipper:
    """Rotating flipper with reliable capsule contact and an active kick."""

    def __init__(self, x, y, direction, color):
        """Set a left or right hinge and its resting angle."""
        self.pivot = pygame.Vector2(x, y)
        self.direction = direction
        self.color = color
        self.length = 112
        self.thickness = 24
        self.lift = 0.0
        self.pressed = False
        self.swinging = False
        self.cooldown = 0.0

    def update(self, dt, pressed):
        """Move the paddle each physics substep, not once per frame."""
        self.pressed = bool(pressed)
        previous = self.lift
        change = (15 if self.pressed else -12) * dt
        self.lift = max(0.0, min(1.0, self.lift + change))
        self.swinging = self.lift > previous + 0.00001
        self.cooldown = max(0.0, self.cooldown - dt)

    def endpoints(self):
        """Return the actual moving collision capsule endpoints."""
        radians = math.radians(14 - 51 * self.lift)
        finish = self.pivot + pygame.Vector2(
            self.direction * self.length * math.cos(radians),
            self.length * math.sin(radians),
        )
        return self.pivot, finish

    def hit(self, ball):
        """Catch a descending ball and kick it into the table.

        Crucially, an active rotating paddle can hit a ball even when the
        latter is not approaching a *stationary* collision normal.
        """
        a, b = self.endpoints()
        contact = circle_segment(ball, a, b, self.thickness)
        if contact is None:
            return False
        nearest, normal, limit, fraction = contact
        ball.position = nearest + normal * (limit + 0.35)
        above = ball.position.y <= nearest.y + 4
        incoming = ball.velocity.dot(normal) < 0

        if (above and (self.pressed or self.swinging)
                and self.cooldown <= 0
                and ball.velocity.y > -180):
            # Timing a swing produces an unmistakable upward shot.
            ball.velocity.x = (
                self.direction * (165 + 220 * fraction)
                + 0.22 * ball.velocity.x
            )
            ball.velocity.y = -min(
                675, max(530, 490 + 220 * fraction),
            )
            self.cooldown = 0.13
            ball.cap_speed()
            return True

        if incoming:
            # A resting paddle can still deflect a ball, with less energy.
            reflect_velocity(ball.velocity, normal, 0.73)
            if above and ball.velocity.y > -215:
                ball.velocity.y = -215
            ball.cap_speed()
            return True
        return False

    def draw(self, surface):
        """Render a physical-looking paddle, tips, hinge, and highlight."""
        a, b = self.endpoints()
        pygame.draw.line(
            surface, SHADOW, a + (3, 5), b + (3, 5),
            self.thickness + 10,
        )
        pygame.draw.line(surface, (67, 75, 84), a, b, self.thickness + 5)
        pygame.draw.line(surface, self.color, a, b, self.thickness)
        for endpoint in (a, b):
            pygame.draw.circle(
                surface, self.color, pos(endpoint), self.thickness // 2,
            )
        pygame.draw.line(surface, CREAM, a, b, 2)
        pygame.draw.circle(surface, SHADOW, pos(a), 10)
        pygame.draw.circle(surface, BRASS, pos(a), 6)


class Bumper:
    """Large spring-loaded pop bumper that awards points on impact."""

    def __init__(self, x, y, radius, color, points=100):
        """Build a circular bumper with a collision radius."""
        self.center = pygame.Vector2(x, y)
        self.radius = radius
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Fade the temporary hit indicator."""
        self.flash = max(0.0, self.flash - dt)

    def hit(self, ball):
        """Apply a radial reflection and return newly scored points."""
        difference = ball.position - self.center
        radius = self.radius + ball.radius
        squared = difference.length_squared()
        if squared > radius * radius:
            return 0
        normal = (difference / math.sqrt(squared)
                  if squared > 0.0001 else pygame.Vector2(0, -1))
        ball.position = self.center + normal * (radius + 0.5)
        approaching = ball.velocity.dot(normal) < 0
        if not approaching:
            return 0
        # A bumper pushes outward without multiplying speed forever.
        incoming = ball.velocity.dot(normal)
        ball.velocity -= 1.6 * incoming * normal
        ball.velocity += normal * 115
        ball.cap_speed()
        if self.flash > 0:
            return 0
        self.flash = 0.11
        return self.points

    def draw(self, surface):
        """Draw a domed metal bumper, not a hollow neon ring."""
        center = pos(self.center)
        rim = CREAM if self.flash else METAL
        pygame.draw.circle(
            surface, SHADOW, (center[0] + 4, center[1] + 5),
            self.radius + 15,
        )
        pygame.draw.circle(surface, rim, center, self.radius + 9)
        pygame.draw.circle(surface, (59, 78, 91), center, self.radius + 3)
        pygame.draw.circle(surface, self.color, center, self.radius - 2)
        pygame.draw.circle(surface, CREAM,
                           (center[0] - 7, center[1] - 8), 7)
        pygame.draw.circle(surface, (58, 65, 77), center, 7)


class Standup:
    """Small upright physical target with per-hit scoring cooldown."""

    def __init__(self, x, y, color, points=150):
        """Create a compact round target."""
        self.center = pygame.Vector2(x, y)
        self.radius = 14
        self.color = color
        self.points = points
        self.flash = 0.0

    def update(self, dt):
        """Count down the target glow."""
        self.flash = max(0, self.flash - dt)

    def hit(self, ball):
        """Bounce the ball and return points for a fresh contact."""
        difference = ball.position - self.center
        distance_sq = difference.length_squared()
        allowed = self.radius + ball.radius
        if distance_sq >= allowed * allowed:
            return 0
        normal = (difference / math.sqrt(distance_sq)
                  if distance_sq > 0.0001 else pygame.Vector2(0, -1))
        ball.position = self.center + normal * (allowed + 0.3)
        if not reflect_velocity(ball.velocity, normal, 0.8):
            return 0
        if self.flash > 0:
            return 0
        self.flash = 0.17
        return self.points

    def draw(self, surface):
        """Draw a bright stand-up lamp mounted on a metal post."""
        at = pos(self.center)
        pygame.draw.circle(surface, SHADOW, (at[0] + 2, at[1] + 3), 19)
        pygame.draw.circle(surface, METAL, at, 17)
        pygame.draw.circle(surface, CREAM if self.flash else self.color,
                           at, 12)
        pygame.draw.circle(surface, CREAM, (at[0] - 3, at[1] - 4), 3)


class PinballGame:
    """One complete single-player pinball mode for the shared app."""

    def __init__(self, width=WIDTH, height=HEIGHT):
        """Create the table, physical objects, HUD, and game state."""
        if not pygame.font.get_init():
            pygame.font.init()
        self.scene = pygame.Surface((WIDTH, HEIGHT))
        self.font_large = pygame.font.Font(None, 60)
        self.font_medium = pygame.font.Font(None, 33)
        self.font_small = pygame.font.Font(None, 26)
        self.ball = Ball()
        self.left_flipper = Flipper(482, 710, 1, RED)
        self.right_flipper = Flipper(772, 710, -1, TEAL)
        # Upper arch and one smooth lower guide on each side.
        # The previous paired guides made V-shaped pockets for the ball.
        self.rails = []
        route_groups = [
            ([(368, 213), (368, 170), (414, 127), (482, 107),
              (776, 107), (845, 126), (897, 185)], BRASS, 8),
            ([(335, 560), (467, 685)], METAL, 8),
            ([(935, 560), (787, 685)], METAL, 8),
        ]
        for points, color, thickness in route_groups:
            for before, after in zip(points, points[1:]):
                self.rails.append(Rail(before, after, color, thickness))
        self.bumpers = [
            Bumper(626, 274, 36, BRASS),
            Bumper(526, 369, 32, RED),
            Bumper(733, 369, 32, TEAL),
        ]
        self._held_flipper_keys = {"left": set(), "right": set()}
        self.targets = [
            Standup(521, 178, BLUE, 150),
            Standup(628, 166, BRASS, 150),
            Standup(736, 178, BLUE, 150),
            Standup(395, 454, RED, 100),
            Standup(865, 454, TEAL, 100),
        ]
        self.restart()

    def restart(self):
        """Reset score and balls while preserving best score."""
        self.best = max(getattr(self, "best", 0),
                        getattr(self, "score", 0))
        self.score = 0
        self.lives = 3
        self.status = "ready"
        self.ball.reset()
        self.charging = False
        self.charge = 0.0
        self.ball_age = 0.0
        self.saver_used = False
        self.message = ""
        self.message_timer = 0.0
        self.left_flipper.lift = 0.0
        self.right_flipper.lift = 0.0

    @staticmethod
    def _flipper_control(event):
        """Identify a flipper by physical key position, not typing layout."""
        scancode = getattr(event, "scancode", None)

        # SDL2 scan codes refer to positions on the physical keyboard.
        # Russian A (Ф) and D (В) share the same positions as Latin A/D.
        if scancode is not None:
            if scancode in (pygame.KSCAN_A, pygame.KSCAN_LEFT):
                return "left"
            if scancode in (pygame.KSCAN_D, pygame.KSCAN_RIGHT):
                return "right"
            return None

        # Compatibility fallback for synthetic events without a scancode.
        if event.key in (pygame.K_a, pygame.K_LEFT):
            return "left"
        if event.key in (pygame.K_d, pygame.K_RIGHT):
            return "right"
        return None

    def handle_event(self, event):
        """Handle input in any keyboard layout using physical key codes."""
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            control = self._flipper_control(event)
            if control is not None:
                scancode = getattr(event, "scancode", None)
                key_id = ("scan", scancode) if scancode is not None else (
                    "key", event.key
                )
                held = self._held_flipper_keys[control]
                if event.type == pygame.KEYDOWN:
                    held.add(key_id)
                else:
                    held.discard(key_id)

            if event.type == pygame.KEYDOWN:
                physical = getattr(event, "scancode", None)
                if (event.key == pygame.K_r
                        or physical == getattr(pygame, "KSCAN_R", 21)):
                    self.restart()
                elif (event.key == pygame.K_p
                        or physical == getattr(pygame, "KSCAN_P", 19)):
                    if self.status == "playing":
                        self.status = "paused"
                    elif self.status == "paused":
                        self.status = "playing"
                elif (event.key == pygame.K_SPACE
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
                        self.charge = 0.0

        # Avoid sticky paddles after switching to another application.
        elif event.type == getattr(pygame, "WINDOWFOCUSLOST", None):
            for held in self._held_flipper_keys.values():
                held.clear()

    def _lost_ball(self):
        """Lose a ball, preserving the accumulated score."""
        self.lives -= 1
        if self.lives <= 0:
            self.status = "over"
            self.message = "GAME OVER"
        else:
            self.ball.reset()
            self.status = "ready"
            self.charging = False
            self.charge = 0.0
            self.message = "BALL LOST"
        self.message_timer = 1.2

    def _award(self, points):
        """Add scored points and activate a brief visual cue."""
        if points:
            self.score += points
            self.best = max(self.score, self.best)
            self.message = "+{}".format(points)
            self.message_timer = 0.65

    def _physics_step(self, dt):
        """Resolve one fixed physics step with moving flippers."""
        self.ball.advance(dt)
        if self.ball.mode != "play":
            return
        for rail in self.rails:
            rail.hit(self.ball)
        for bumper in self.bumpers:
            self._award(bumper.hit(self.ball))
        for target in self.targets:
            self._award(target.hit(self.ball))
        self.left_flipper.hit(self.ball)
        self.right_flipper.hit(self.ball)
        self.ball.cap_speed()
        if self.ball.position.y - self.ball.radius > BOTTOM:
            self._lost_ball()

    def update(self, dt):
        """Update controls and simulation using short physics substeps."""
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
        if self.status == "paused":
            return
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
        for bumper in self.bumpers:
            bumper.update(dt)
        for target in self.targets:
            target.update(dt)
        count = max(1, math.ceil(dt / STEP))
        part = dt / count
        for _ in range(count):
            self.left_flipper.update(part, left_down)
            self.right_flipper.update(part, right_down)
            self._physics_step(part)
            if self.status != "playing":
                break
        if self.status == "playing" and self.ball.mode == "play":
            if (not self.ball.trail or
                    (self.ball.position - self.ball.trail[-1]
                     ).length_squared() > 105):
                self.ball.trail.append(self.ball.position.copy())
                self.ball.trail = self.ball.trail[-6:]

    def _text(self, surface, text, x, y, font=None, color=CREAM):
        """Draw one clear HUD label."""
        font = font or self.font_medium
        surface.blit(font.render(str(text), True, color), (x, y))

    def _table_background(self, scene):
        """Draw a restrained retro-industrial table rather than neon lines."""
        scene.fill(INK)
        # Side panel uses a dense matte finish and restrained accents.
        pygame.draw.rect(scene, (23, 32, 46), (14, 20, 259, 795),
                         border_radius=12)
        pygame.draw.rect(scene, (23, 32, 46), (1035, 20, 151, 795),
                         border_radius=12)
        pygame.draw.line(scene, BRASS, (28, 242), (250, 242), 3)
        pygame.draw.line(scene, BRASS, (1050, 242), (1170, 242), 3)
        # Layered steel enclosure and inset playfield.
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
        # Thin gold compass / orbital decoration behind the mechanics.
        for radius in (135, 205, 265):
            pygame.draw.circle(scene, (39, 66, 83),
                               (628, 371), radius, 2)
        pygame.draw.line(scene, (39, 66, 83), (628, 114), (628, 628), 2)
        pygame.draw.line(scene, (39, 66, 83), (367, 371), (893, 371), 2)
        for x in range(390, 905, 75):
            pygame.draw.circle(scene, (62, 92, 104), (x, 592), 2)
        # Separate spring channel on the right with an actual divider.
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
        if surface.get_size() == (WIDTH, HEIGHT):
            surface.blit(scene, (0, 0))
        else:
            scaled = pygame.transform.smoothscale(scene, surface.get_size())
            surface.blit(scaled, (0, 0))


def main():
    """Run this game alone without changing Vlad's shared entry point."""
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pinball Arcade")
    clock = pygame.time.Clock()
    game = PinballGame()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif (event.type == pygame.KEYDOWN
                  and event.key == pygame.K_ESCAPE):
                running = False
            game.handle_event(event)
        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
