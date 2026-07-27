"""EQ de 5 bandas optimizado para tiempo real (SOS + dirty flag)."""
import numpy as np
from scipy.signal import sosfilt

_BANDAS = [
    ("Graves", 80, "LowShelf"),
    ("Me-Graves", 300, "Peaking"),
    ("Medios", 1000, "Peaking"),
    ("Me-Agudos", 4000, "Peaking"),
    ("Agudos", 12000, "HighShelf"),
]


class EQ5:
    def __init__(self, sample_rate=48000):
        self.sr = sample_rate
        self.gains = [0.0] * 5
        self._sos = np.empty((0, 6), dtype=np.float32)
        self._dirty = True

    def _build(self):
        if not self._dirty:
            return
        sections = []
        for i, (_, fc, ft) in enumerate(_BANDAS):
            g = self.gains[i]
            if abs(g) < 0.5:
                continue
            A = 10.0 ** (g / 40.0)
            w0 = 2.0 * np.pi * fc / self.sr
            cos = np.cos(w0)
            sin = np.sin(w0)
            alpha = sin * 0.5 * fc / (fc * 0.5)
            if ft == "LowShelf":
                sqrtA = np.sqrt(A)
                a1 = A + 1.0
                a2 = A - 1.0
                b0 = A * (a1 - a2 * cos + 2.0 * sqrtA * alpha)
                b1 = 2.0 * A * (a2 - a1 * cos)
                b2 = A * (a1 - a2 * cos - 2.0 * sqrtA * alpha)
                a0 = a1 + a2 * cos + 2.0 * sqrtA * alpha
                a1c = -2.0 * (a2 + a1 * cos)
                a2c = a1 + a2 * cos - 2.0 * sqrtA * alpha
            elif ft == "HighShelf":
                sqrtA = np.sqrt(A)
                a1 = A + 1.0
                a2 = A - 1.0
                b0 = A * (a1 + a2 * cos + 2.0 * sqrtA * alpha)
                b1 = -2.0 * A * (a2 + a1 * cos)
                b2 = A * (a1 + a2 * cos - 2.0 * sqrtA * alpha)
                a0 = a1 - a2 * cos + 2.0 * sqrtA * alpha
                a1c = 2.0 * (a2 - a1 * cos)
                a2c = a1 - a2 * cos - 2.0 * sqrtA * alpha
            else:
                if A == 1.0:
                    continue
                b0 = 1.0 + alpha * A
                b1 = -2.0 * cos
                b2 = 1.0 - alpha * A
                a0 = 1.0 + alpha / A
                a1c = -2.0 * cos
                a2c = 1.0 - alpha / A
            sections.append([b0 / a0, b1 / a0, b2 / a0, 1.0, a1c / a0, a2c / a0])
        self._sos = np.array(sections, dtype=np.float32) if sections else np.empty((0, 6), dtype=np.float32)
        self._dirty = False

    def process(self, data):
        if not any(abs(g) >= 0.5 for g in self.gains):
            return data
        self._build()
        if self._sos.shape[0] == 0:
            return data
        return sosfilt(self._sos, data)
