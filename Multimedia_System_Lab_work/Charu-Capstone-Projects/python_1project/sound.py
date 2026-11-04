"""
sound.py — SoundManager for Swachh Indore - Waste Sorting Hero.

Generates procedural audio tones using numpy + pygame.sndarray when numpy is
available, otherwise silently disables all sound.
"""

import pygame

_SAMPLE_RATE = 44100


def _make_tone_numpy(freq: float, duration: float,
                     wave_type: str = "sine", volume: float = 0.4):
    """Return a pygame.Sound built from a numpy-generated waveform."""
    import numpy as np
    t = np.linspace(0, duration, int(_SAMPLE_RATE * duration), endpoint=False)
    if wave_type == "sine":
        wave = np.sin(2 * np.pi * freq * t)
    elif wave_type == "square":
        wave = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave_type == "sawtooth":
        wave = 2 * (t * freq - np.floor(0.5 + t * freq))
    else:
        wave = np.sin(2 * np.pi * freq * t)
    wave = (wave * volume * 32767).astype(np.int16)
    stereo = np.column_stack([wave, wave])
    return pygame.sndarray.make_sound(stereo)


class SoundManager:
    """Manages procedural sound effects for the game.

    Uses numpy for waveform generation when available; otherwise all
    ``play()`` calls are silently ignored.
    """

    def __init__(self):
        self._sounds: dict = {}
        self._enabled = False

        try:
            pygame.mixer.pre_init(_SAMPLE_RATE, -16, 2, 512)
            pygame.mixer.init()
            import numpy  # noqa: F401 – just test availability
            self._sounds["correct"] = _make_tone_numpy(1000, 0.15, "sine",    0.4)
            self._sounds["wrong"]   = _make_tone_numpy(150,  0.30, "sawtooth",0.4)
            self._sounds["catch"]   = _make_tone_numpy(600,  0.05, "square",  0.35)
            self._enabled = True
        except Exception:
            # numpy unavailable OR mixer failed — run silently
            self._enabled = False

    # ------------------------------------------------------------------
    def play(self, name: str) -> None:
        """Play a named sound effect ('correct', 'wrong', 'catch').

        Silently ignores unknown names or when sound is disabled.
        """
        if not self._enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            try:
                sound.play()
            except Exception:
                pass
