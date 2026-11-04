"""
ui.py — All UI / HUD rendering functions for Swachh Indore - Waste Sorting Hero.

Every public function accepts a pygame.Surface as its first argument and uses
only pygame.draw primitives + fonts (no external image assets).
"""

from __future__ import annotations
import pygame
from constants import (
    SKY, ROAD, ROAD_MARK, BUILDING_DARK,
    GREEN, BLUE, RED, YELLOW, WHITE, BLACK,
    DARK, ORANGE, LIGHT,
    STATE_START, STATE_PAUSED, STATE_GAMEOVER,
    BIN_DEFINITIONS,
)

# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _rounded_rect(surface: pygame.Surface, color, rect, radius: int = 12,
                  alpha: int = 255) -> None:
    """Draw a solid rounded rectangle, optionally semi-transparent."""
    if alpha < 255:
        tmp = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*color[:3], alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
        surface.blit(tmp, (rect[0], rect[1]))
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)


def _center_text(surface: pygame.Surface, font: pygame.font.Font,
                 text: str, color, cx: int, cy: int) -> pygame.Rect:
    """Render text centered at (cx, cy) and return the rect."""
    img  = font.render(text, True, color)
    rect = img.get_rect(center=(cx, cy))
    surface.blit(img, rect)
    return rect


# ──────────────────────────────────────────────────────────────────────────────
# Background
# ──────────────────────────────────────────────────────────────────────────────

def draw_background(surface: pygame.Surface, W: int, H: int) -> None:
    """Draw the city-scene background (sky, hills, buildings, road, markings)."""

    # Sky
    surface.fill(SKY)

    # Hills / distant mountains
    hill_color = (100, 180, 210)
    hill_pts = [
        (0, H),
        (0, 360), (60, 300), (130, 340),
        (210, 270), (310, 330), (390, 260),
        (480, 310), (560, 250), (650, 300),
        (740, 260), (820, 310), (900, 280),
        (W, 360), (W, H),
    ]
    pygame.draw.polygon(surface, hill_color, hill_pts)

    # Buildings (positions mirror the HTML canvas version)
    buildings = [
        (80,  330, 90,  170),
        (200, 280, 110, 220),
        (500, 380, 130, 120),
        (700, 310, 100, 190),
    ]
    for bx, by, bw, bh in buildings:
        pygame.draw.rect(surface, BUILDING_DARK, (bx, by, bw, bh))
        # Simple windows
        win_color = (241, 196, 15, 160)
        for wy in range(by + 15, by + bh - 20, 28):
            for wx in range(bx + 10, bx + bw - 10, 22):
                if (wx + wy) % 3 != 0:          # random-ish lit windows
                    pygame.draw.rect(surface, (241, 196, 15), (wx, wy, 10, 14))

    # Road
    pygame.draw.rect(surface, ROAD, (0, 500, W, H - 500))

    # Road markings — dashed white line at y=545
    dash_w, dash_h, gap = 50, 8, 40
    for dx in range(0, W, dash_w + gap):
        pygame.draw.rect(surface, ROAD_MARK, (dx, 545, dash_w, dash_h))


# ──────────────────────────────────────────────────────────────────────────────
# Bins
# ──────────────────────────────────────────────────────────────────────────────

def draw_bins(surface: pygame.Surface, font: pygame.font.Font,
              W: int, H: int) -> None:
    """Draw the three color-coded waste bins near the bottom of the screen."""
    bin_y = 425
    bin_h = 75

    configs = [
        (100,  "WET", GREEN),
        (415,  "DRY", BLUE),
        (730,  "HAZ", RED),
    ]

    for bx, label, color in configs:
        bw = 70
        # Bin body
        pygame.draw.rect(surface, color, (bx, bin_y, bw, bin_h), border_radius=8)
        # Darker lid
        lid_color = tuple(max(0, c - 30) for c in color)
        pygame.draw.rect(surface, lid_color, (bx - 4, bin_y - 8, bw + 8, 14), border_radius=5)
        # Label
        txt  = font.render(label, True, WHITE)
        trct = txt.get_rect(center=(bx + bw // 2, bin_y + bin_h // 2))
        surface.blit(txt, trct)


# ──────────────────────────────────────────────────────────────────────────────
# HUD
# ──────────────────────────────────────────────────────────────────────────────

def draw_hud(surface: pygame.Surface, font: pygame.font.Font,
             score: int, high_score: int, lives: int) -> None:
    """Draw score / high-score panel (top-left) and lives panel (top-right)."""

    # -- Score panel (top-left)
    score_txt = f"Score: {score}  |  High: {high_score}"
    _rounded_rect(surface, WHITE, (10, 10, 280, 38), radius=10, alpha=200)
    img  = font.render(score_txt, True, DARK)
    surface.blit(img, img.get_rect(midleft=(20, 29)))

    # -- Lives panel (top-right)
    if lives > 0:
        hearts = "♥ " * lives
    else:
        hearts = "☠"
    lives_txt = f"Lives: {hearts.strip()}"
    _rounded_rect(surface, WHITE, (surface.get_width() - 180, 10, 170, 38),
                  radius=10, alpha=200)
    img2 = font.render(lives_txt, True, RED if lives <= 1 else DARK)
    surface.blit(img2, img2.get_rect(midright=(surface.get_width() - 20, 29)))


# ──────────────────────────────────────────────────────────────────────────────
# Overlay screens
# ──────────────────────────────────────────────────────────────────────────────

def draw_screen_overlay(surface: pygame.Surface,
                        font_big: pygame.font.Font,
                        font_small: pygame.font.Font,
                        state: str,
                        final_score: int = 0) -> None:
    """Render a full-screen dark overlay for START, PAUSED, or GAMEOVER."""
    W = surface.get_width()
    H = surface.get_height()

    # Full dark overlay
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    cx = W // 2

    if state == STATE_START:
        # Title
        _center_text(surface, font_big,   "Swachh Indore",       YELLOW, cx, 130)
        _center_text(surface, font_small, "Waste Sorting Hero",  WHITE,  cx, 180)

        # Instructions box
        box_x, box_y, box_w, box_h = cx - 200, 210, 400, 160
        _rounded_rect(surface, DARK, (box_x, box_y, box_w, box_h), radius=14, alpha=220)
        lines = [
            "Catch falling waste items in your basket.",
            "Select the correct bin when prompted:",
            "  G = Green (Wet Waste)",
            "  B = Blue  (Dry Waste)",
            "  R = Red   (Hazardous)",
            "Arrow keys or mouse to move basket.",
        ]
        lf = pygame.font.SysFont("Arial", 16)
        for i, line in enumerate(lines):
            img = lf.render(line, True, LIGHT)
            surface.blit(img, (box_x + 14, box_y + 12 + i * 23))

        # Action button
        _rounded_rect(surface, YELLOW, (cx - 140, 390, 280, 46), radius=14)
        _center_text(surface, font_small, "Press SPACE to Play", DARK, cx, 413)

    elif state == STATE_PAUSED:
        _center_text(surface, font_big,   "PAUSED",               YELLOW, cx, H // 2 - 50)
        _rounded_rect(surface, YELLOW, (cx - 160, H // 2 + 10, 320, 46), radius=14)
        _center_text(surface, font_small, "Press P to Resume",    DARK,   cx, H // 2 + 33)

    elif state == STATE_GAMEOVER:
        _center_text(surface, font_big,   "GAME OVER",            RED,    cx, H // 2 - 80)
        _center_text(surface, font_small, f"Score: {final_score}", WHITE,  cx, H // 2 - 20)
        _rounded_rect(surface, YELLOW, (cx - 170, H // 2 + 30, 340, 46), radius=14)
        _center_text(surface, font_small, "Press SPACE to Play Again", DARK, cx, H // 2 + 53)


# ──────────────────────────────────────────────────────────────────────────────
# Sorting popup
# ──────────────────────────────────────────────────────────────────────────────

def draw_popup(surface: pygame.Surface,
               item_data: dict,
               font_title: pygame.font.Font,
               font_body: pygame.font.Font,
               W: int, H: int,
               emoji_font: pygame.font.Font | None = None,
               ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    """Draw the bin-selection modal. Returns (green_rect, blue_rect, red_rect)."""

    # Dim the background
    dim = pygame.Surface((W, H), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    surface.blit(dim, (0, 0))

    # Modal dimensions
    mw, mh = 560, 290
    mx = (W - mw) // 2
    my = (H - mh) // 2

    # Modal background
    _rounded_rect(surface, WHITE, (mx, my, mw, mh), radius=18)
    pygame.draw.rect(surface, DARK, (mx, my, mw, mh), width=2, border_radius=18)

    # ── Left column: emoji + name + category ────────────────────────────────
    left_cx = mx + mw // 4

    emoji   = item_data.get("emoji", "?")
    e_drawn = False
    if emoji_font is not None:
        try:
            eimg = emoji_font.render(emoji, True, BLACK)
            erct = eimg.get_rect(center=(left_cx, my + 70))
            surface.blit(eimg, erct)
            e_drawn = True
        except Exception:
            pass
    if not e_drawn:
        pygame.draw.circle(surface, DARK, (left_cx, my + 70), 30)
        lbl = item_data.get("name", "")[:4]
        lf  = pygame.font.SysFont("Arial", 15, bold=True)
        img = lf.render(lbl, True, WHITE)
        surface.blit(img, img.get_rect(center=(left_cx, my + 70)))

    _center_text(surface, font_title, item_data.get("name", ""), DARK, left_cx, my + 128)
    cat_font = pygame.font.SysFont("Arial", 16)
    _center_text(surface, cat_font,  item_data.get("type", ""),  (100, 100, 100), left_cx, my + 155)

    # Divider
    pygame.draw.line(surface, (200, 200, 200),
                     (mx + mw // 2, my + 20),
                     (mx + mw // 2, my + mh - 20), 1)

    # ── Right column: bin buttons ─────────────────────────────────────────
    right_x  = mx + mw // 2 + 10
    right_w  = mw // 2 - 20
    btn_h    = 46
    gap      = 12

    _center_text(surface, font_title, "Select Correct Bin", DARK,
                 right_x + right_w // 2, my + 38)

    btn_configs = [
        ("G  –  Green Bin  (Wet)",  GREEN, "GREEN"),
        ("B  –  Blue Bin   (Dry)",  BLUE,  "BLUE"),
        ("R  –  Red Bin    (Haz)",  RED,   "RED"),
    ]

    rects: list[pygame.Rect] = []
    start_y = my + 70
    for label, color, _ in btn_configs:
        rect = pygame.Rect(right_x, start_y, right_w, btn_h)
        _rounded_rect(surface, color, rect, radius=10)
        bf   = pygame.font.SysFont("Arial", 16, bold=True)
        img  = bf.render(label, True, WHITE)
        surface.blit(img, img.get_rect(midleft=(rect.x + 12, rect.centery)))
        rects.append(rect)
        start_y += btn_h + gap

    return tuple(rects)   # type: ignore[return-value]


# ──────────────────────────────────────────────────────────────────────────────
# Toast notification
# ──────────────────────────────────────────────────────────────────────────────

def draw_toast(surface: pygame.Surface, font: pygame.font.Font,
               message: str, color: tuple, alpha: int) -> None:
    """Draw a fading pill-badge centered at y=150."""
    W    = surface.get_width()
    img  = font.render(message, True, WHITE)
    pw   = img.get_width() + 36
    ph   = img.get_height() + 14
    px   = (W - pw) // 2
    py   = 150 - ph // 2

    pill = pygame.Surface((pw, ph), pygame.SRCALPHA)
    r, g, b = color[:3]
    pygame.draw.rect(pill, (r, g, b, alpha), (0, 0, pw, ph), border_radius=ph // 2)
    pill.blit(img, img.get_rect(center=(pw // 2, ph // 2)))
    surface.blit(pill, (px, py))
