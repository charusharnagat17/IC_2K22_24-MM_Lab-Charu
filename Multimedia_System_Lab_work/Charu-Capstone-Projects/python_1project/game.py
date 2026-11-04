"""
game.py — Main Game class for Swachh Indore - Waste Sorting Hero.

Orchestrates the game loop, state machine, input handling, physics and
rendering by composing the modules: entities, ui, sound, constants, data.
"""

from __future__ import annotations
import sys
import random
import pygame

from constants import (
    SCREEN_W, SCREEN_H, FPS,
    GREEN, BLUE, RED, YELLOW, WHITE, BLACK, DARK,
    STATE_START, STATE_PLAYING, STATE_POPUP, STATE_PAUSED, STATE_GAMEOVER,
    HIGH_SCORE_FILE,
)
from data      import WASTE_ITEMS, EMOJI_FALLBACK
from entities  import Player, FallingItem
from sound     import SoundManager
import ui


class Game:
    """Top-level game object.  Owns the pygame window, clock, and state machine."""

    # ──────────────────────────────────────────────────────────────────────
    # Construction / init
    # ──────────────────────────────────────────────────────────────────────

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Swachh Indore - Waste Sorting Hero")
        self.clock = pygame.time.Clock()

        # Fonts ─────────────────────────────────────────────────────────
        self.emoji_font   = self._load_emoji_font(52)
        self.emoji_font_sm = self._load_emoji_font(32)   # for popup left col
        self.font_ui      = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_big     = pygame.font.SysFont("Arial", 54, bold=True)
        self.font_mid     = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_small   = pygame.font.SysFont("Arial", 22)
        self.font_toast   = pygame.font.SysFont("Arial", 20, bold=True)
        self.font_fallback = pygame.font.SysFont("Arial", 11, bold=True)

        # Sound, score, state ────────────────────────────────────────────
        self.sound      = SoundManager()
        self.high_score = self.load_high_score()
        self.state      = STATE_START

        # Player
        self.player = Player(SCREEN_W, SCREEN_H)

        # Mutable game state (populated by reset())
        self.score       = 0
        self.lives       = 3
        self.base_speed  = 2.5
        self.frames      = 0
        self.active_items: list[FallingItem] = []
        self.caught_item: dict | None        = None

        # Toast list: [(message, color, alpha, timer_frames)]
        self.toasts: list[list] = []

        # Popup button rects (updated each frame popup is drawn)
        self._popup_rects: tuple | None = None

    # ──────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────

    @staticmethod
    def _load_emoji_font(size: int) -> pygame.font.Font | None:
        """Try to load an emoji-capable font; return None on failure."""
        for name in ("Segoe UI Emoji", "Apple Color Emoji",
                     "Noto Color Emoji", "Symbola"):
            try:
                f = pygame.font.SysFont(name, size)
                # Quick sanity: render a known emoji and check non-blank
                img = f.render("🍌", True, (0, 0, 0))
                if img.get_width() > 4:
                    return f
            except Exception:
                continue
        return None

    # ──────────────────────────────────────────────────────────────────────
    # State management
    # ──────────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset all mutable game state and enter PLAYING."""
        self.score      = 0
        self.lives      = 3
        self.base_speed = 2.5
        self.frames     = 0
        self.active_items.clear()
        self.caught_item = None
        self.toasts.clear()
        self.player.x = SCREEN_W / 2 - self.player.w / 2
        self.state = STATE_PLAYING

    def open_popup(self) -> None:
        """Pause the game and show the bin-selection popup."""
        self.state = STATE_POPUP

    def end_game(self) -> None:
        """Save high score and transition to GAMEOVER."""
        self.save_high_score()
        self.state = STATE_GAMEOVER

    # ──────────────────────────────────────────────────────────────────────
    # High score I/O
    # ──────────────────────────────────────────────────────────────────────

    def load_high_score(self) -> int:
        """Read persisted high score; return 0 if file absent or unreadable."""
        try:
            with open(HIGH_SCORE_FILE, "r") as fh:
                return int(fh.read().strip())
        except Exception:
            return 0

    def save_high_score(self) -> None:
        """Write current high score to disk."""
        try:
            with open(HIGH_SCORE_FILE, "w") as fh:
                fh.write(str(self.high_score))
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────
    # Spawning
    # ──────────────────────────────────────────────────────────────────────

    def spawn_item(self) -> None:
        """Pick a random waste item and add it to active_items."""
        data = random.choice(WASTE_ITEMS)
        item = FallingItem(data, SCREEN_W)
        # Apply current speed level
        item.speed += max(0, self.base_speed - 2.5)
        self.active_items.append(item)

    # ──────────────────────────────────────────────────────────────────────
    # Toast
    # ──────────────────────────────────────────────────────────────────────

    def add_toast(self, message: str, color: tuple) -> None:
        """Queue a fading toast notification (90 frames ≈ 1.5 s at 60 fps)."""
        self.toasts.append([message, color, 255, 90])

    # ──────────────────────────────────────────────────────────────────────
    # Bin checking
    # ──────────────────────────────────────────────────────────────────────

    def check_bin(self, selected_bin: str) -> None:
        """Evaluate the player's bin selection against the caught item."""
        if self.caught_item is None:
            return

        correct_bin = self.caught_item["bin"]
        if selected_bin == correct_bin:
            self.score += 10
            self.sound.play("correct")
            self.add_toast("✓ Correct! +10", GREEN)
            # Speed up every 100 points
            if self.score > 0 and self.score % 100 == 0:
                self.base_speed += 0.5
                self.add_toast("Speed Up! ⚡", YELLOW)
        else:
            self.score = max(0, self.score - 5)
            self.lives -= 1
            self.sound.play("wrong")
            self.add_toast(f"✗ Wrong! -{5}  →  {correct_bin.capitalize()} bin", RED)

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

        self.caught_item = None

        if self.lives <= 0:
            self.end_game()
        else:
            self.state = STATE_PLAYING

    # ──────────────────────────────────────────────────────────────────────
    # Event handling
    # ──────────────────────────────────────────────────────────────────────

    def handle_events(self) -> None:
        """Process all pygame events for the current frame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_high_score()
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                self._on_keydown(event.key)

            elif event.type == pygame.MOUSEMOTION:
                if self.state == STATE_PLAYING:
                    self.player.set_x(event.pos[0] - self.player.w // 2)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.state == STATE_POPUP:
                    self._on_popup_click(event.pos)

    def _on_keydown(self, key: int) -> None:
        """Handle a KEYDOWN event."""
        if key == pygame.K_SPACE:
            if self.state in (STATE_START, STATE_GAMEOVER):
                self.reset()
        elif key == pygame.K_p:
            if self.state == STATE_PLAYING:
                self.state = STATE_PAUSED
            elif self.state == STATE_PAUSED:
                self.state = STATE_PLAYING
        elif key == pygame.K_ESCAPE:
            if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_POPUP):
                self.state = STATE_START
                self.active_items.clear()
                self.caught_item = None

        # Popup bin selection
        if self.state == STATE_POPUP:
            if key == pygame.K_g:
                self.check_bin("GREEN")
            elif key == pygame.K_b:
                self.check_bin("BLUE")
            elif key == pygame.K_r:
                self.check_bin("RED")

    def _on_popup_click(self, pos: tuple) -> None:
        """Handle a mouse click while the popup is visible."""
        if self._popup_rects is None:
            return
        green_rect, blue_rect, red_rect = self._popup_rects
        if green_rect.collidepoint(pos):
            self.check_bin("GREEN")
        elif blue_rect.collidepoint(pos):
            self.check_bin("BLUE")
        elif red_rect.collidepoint(pos):
            self.check_bin("RED")

    # ──────────────────────────────────────────────────────────────────────
    # Update
    # ──────────────────────────────────────────────────────────────────────

    def update(self) -> None:
        """Advance game logic one frame (only when STATE_PLAYING)."""
        if self.state != STATE_PLAYING:
            return

        self.frames += 1

        # Player keyboard movement
        keys = pygame.key.get_pressed()
        self.player.move(
            keys[pygame.K_LEFT]  or keys[pygame.K_a],
            keys[pygame.K_RIGHT] or keys[pygame.K_d],
            SCREEN_W,
        )

        # Spawn rate decreases (speeds up) as score grows
        spawn_rate = max(50, 110 - self.score // 20)
        if self.frames % spawn_rate == 0:
            self.spawn_item()

        # Update items
        player_rect = self.player.get_rect()
        to_remove   = []
        for item in self.active_items:
            item.update()
            if item.get_rect().colliderect(player_rect):
                self.sound.play("catch")
                self.caught_item = item.data
                to_remove.append(item)
                self.open_popup()
                break                   # handle one catch per frame
            elif item.is_off_screen(SCREEN_H):
                to_remove.append(item)

        for item in to_remove:
            if item in self.active_items:
                self.active_items.remove(item)

    # ──────────────────────────────────────────────────────────────────────
    # Draw
    # ──────────────────────────────────────────────────────────────────────

    def draw(self) -> None:
        """Render the full frame."""
        # Background + environment
        ui.draw_background(self.screen, SCREEN_W, SCREEN_H)
        ui.draw_bins(self.screen, self.font_ui, SCREEN_W, SCREEN_H)

        # Falling items
        for item in self.active_items:
            item.draw(self.screen, self.emoji_font,
                      self.font_fallback, EMOJI_FALLBACK)

        # Player basket
        self.player.draw(self.screen)

        # Toasts
        offset = 0
        for toast in list(self.toasts):
            adjusted_surf = pygame.Surface((SCREEN_W, 50), pygame.SRCALPHA)
            ui.draw_toast(self.screen, self.font_toast,
                          toast[0], toast[1], int(toast[2]))
            # Stack multiple toasts
            toast[2] = max(0, toast[2] - 255 / toast[3])  # fade per frame
            toast[3] -= 1

        # Prune dead toasts
        self.toasts = [t for t in self.toasts if t[3] > 0]

        # HUD (always on top of game world)
        ui.draw_hud(self.screen, self.font_ui,
                    self.score, self.high_score, self.lives)

        # Overlay screens
        if self.state in (STATE_START, STATE_PAUSED, STATE_GAMEOVER):
            ui.draw_screen_overlay(self.screen, self.font_big, self.font_small,
                                   self.state, self.score)

        # Popup
        if self.state == STATE_POPUP and self.caught_item is not None:
            rects = ui.draw_popup(
                self.screen, self.caught_item,
                self.font_mid, self.font_small,
                SCREEN_W, SCREEN_H,
                emoji_font=self.emoji_font_sm,
            )
            self._popup_rects = rects

        pygame.display.flip()

    # ──────────────────────────────────────────────────────────────────────
    # Main loop
    # ──────────────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Start and run the main game loop."""
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
