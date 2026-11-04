"""
entities.py — Player basket and FallingItem sprites for Swachh Indore.

All rendering is done with pygame.draw primitives + fonts (no image assets).
"""

import random
import pygame
from constants import ORANGE, WHITE, BLACK


class Player:
    """The player-controlled basket at the bottom of the screen.

    Drawn as a trapezoid with an orange body and lighter top rim.
    """

    _BODY_COLOR  = (211, 84,   0)   # #D35400
    _RIM_COLOR   = (230, 126,  34)  # #E67E22

    def __init__(self, screen_w: int, screen_h: int):
        self.w = 90
        self.h = 55
        self.speed = 9
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.x = screen_w / 2 - self.w / 2
        self.y = screen_h - 110

    # ------------------------------------------------------------------
    def move(self, keys_left: bool, keys_right: bool, screen_w: int) -> None:
        """Move the basket left or right based on pressed keys."""
        if keys_left:
            self.x -= self.speed
        if keys_right:
            self.x += self.speed
        self._clamp(screen_w)

    def set_x(self, x: float) -> None:
        """Set basket x-position directly (mouse/touch control), clamped."""
        self.x = x
        self._clamp(self.screen_w)

    def _clamp(self, screen_w: int) -> None:
        self.x = max(0, min(screen_w - self.w, self.x))

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        """Draw a trapezoid basket with 'CATCH' label."""
        x, y, w, h = int(self.x), int(self.y), self.w, self.h

        # Trapezoid body (wider at bottom)
        inset = 8
        body_points = [
            (x + inset, y),          # top-left
            (x + w - inset, y),      # top-right
            (x + w, y + h),          # bottom-right
            (x, y + h),              # bottom-left
        ]
        pygame.draw.polygon(surface, self._BODY_COLOR, body_points)

        # Lighter top rim
        rim_points = [
            (x + inset - 4, y - 4),
            (x + w - inset + 4, y - 4),
            (x + w - inset, y + 6),
            (x + inset, y + 6),
        ]
        pygame.draw.polygon(surface, self._RIM_COLOR, rim_points)

        # "CATCH" label
        try:
            font = pygame.font.SysFont("Arial", 13, bold=True)
            text = font.render("CATCH", True, WHITE)
            tr   = text.get_rect(center=(x + w // 2, y + h // 2 + 4))
            surface.blit(text, tr)
        except Exception:
            pass

    # ------------------------------------------------------------------
    def get_rect(self) -> pygame.Rect:
        """Return the collision rectangle for the player basket."""
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)


# ============================================================

class FallingItem:
    """A single waste item that falls from the top of the screen.

    Tries to render its emoji; falls back to a colored circle + ASCII label.
    """

    _BIN_COLORS = {
        "GREEN": (46,  204, 113),
        "BLUE":  (52,  152, 219),
        "RED":   (231,  76,  60),
    }

    def __init__(self, data: dict, screen_w: int):
        self.data  = data
        self.x     = random.randint(40, screen_w - 80)
        self.y     = -50
        self.speed = 2.5 + random.random() * 1.5

    # ------------------------------------------------------------------
    def update(self) -> None:
        """Advance the item downward by its speed."""
        self.y += self.speed

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface,
             emoji_font: pygame.font.Font,
             fallback_font: pygame.font.Font,
             fallback_map: dict) -> None:
        """Render the item using emoji_font; fall back to circle+text."""
        emoji   = self.data["emoji"]
        cx, cy  = int(self.x), int(self.y)
        drawn   = False

        if emoji_font is not None:
            try:
                img = emoji_font.render(emoji, True, BLACK)
                # Detect blank/box render: if >95% of non-zero pixels are the
                # same color we likely got a replacement glyph — skip it.
                # Simple heuristic: just try to blit and trust the font.
                rect = img.get_rect(center=(cx, cy))
                surface.blit(img, rect)
                drawn = True
            except Exception:
                drawn = False

        if not drawn:
            # Fallback: colored circle + label text
            color  = self._BIN_COLORS.get(self.data["bin"], (150, 150, 150))
            label  = fallback_map.get(emoji, self.data["name"][:6].upper())
            pygame.draw.circle(surface, color, (cx, cy), 22)
            pygame.draw.circle(surface, WHITE, (cx, cy), 22, 2)
            if fallback_font:
                txt  = fallback_font.render(label, True, WHITE)
                trct = txt.get_rect(center=(cx, cy))
                surface.blit(txt, trct)

    # ------------------------------------------------------------------
    def is_off_screen(self, screen_h: int) -> bool:
        """Return True when the item has scrolled past the bottom."""
        return self.y > screen_h + 60

    def get_rect(self, size: int = 45) -> pygame.Rect:
        """Return the collision rectangle centered on the item."""
        return pygame.Rect(int(self.x) - size // 2,
                           int(self.y) - size // 2,
                           size, size)
