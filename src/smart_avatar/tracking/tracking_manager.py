"""Gestor central de proveedores de tracking con fallback a idle."""

from __future__ import annotations

import logging
import math
import random
import time

from src.smart_avatar.core.types import Vec2
from src.smart_avatar.tracking.tracking_interface import ITrackingProvider, TrackingData

log = logging.getLogger(__name__)


class TrackingManager:
    """Administra múltiples proveedores de tracking.

    Permite registrar varios proveedores, elegir cuál está activo,
    y proporciona ``get_data()`` que devuleve datos del proveedor
    activo o, si no hay ninguno, genera una animación idle procedural.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ITrackingProvider] = {}
        self._active_name: str | None = None
        self._start_time: float = time.monotonic()
        self._last_blink_time: float = 0.0
        self._blink_state: float = 0.0
        self._blink_phase: float = 0.0  # 0 = open, positive = closing

    # ------------------------------------------------------------------
    # Registro de proveedores
    # ------------------------------------------------------------------

    def register_provider(self, name: str, provider: ITrackingProvider) -> None:
        """Registra un proveedor con un nombre identificador."""
        self._providers[name] = provider
        log.info("Tracking provider registrado: %s", name)

    def set_active_provider(self, name: str | None) -> bool:
        """Activa el proveedor *name*. Devuelve False si no existe.

        Si *name* es None, se desactiva el proveedor activo y se usa idle.
        """
        if name is not None and name not in self._providers:
            log.warning("Proveedor de tracking no encontrado: %s", name)
            return False

        # Parar el proveedor anterior si había uno activo
        if self._active_name is not None and self._active_name in self._providers:
            try:
                self._providers[self._active_name].stop()
            except Exception:
                log.exception("Error al parar proveedor %s", self._active_name)

        self._active_name = name

        if name is not None and self._providers[name].start():
            log.info("Proveedor activo: %s", name)
            return True

        if name is not None:
            log.warning("Proveedor %s no pudo arrancar", name)
            self._active_name = None
            return False

        log.info("Sin proveedor activo, usando idle animation")
        return True

    @property
    def active_provider_name(self) -> str | None:
        return self._active_name

    def get_provider_names(self) -> list[str]:
        return list(self._providers.keys())

    # ------------------------------------------------------------------
    # Obtención de datos
    # ------------------------------------------------------------------

    def get_data(self) -> TrackingData:
        """Obtiene datos del proveedor activo o genera animación idle."""
        if self._active_name is not None:
            provider = self._providers.get(self._active_name)
            if provider is not None and provider.is_available():
                try:
                    return provider.get_data()
                except Exception:
                    log.exception("Error leyendo datos de %s", self._active_name)

        return self._generate_idle_data()

    # ------------------------------------------------------------------
    # Animación idle procedural
    # ------------------------------------------------------------------

    def _generate_idle_data(self) -> TrackingData:
        """Genera una animación idle sutil: micro-movimientos de cabeza,
        parpadeo periódico y sonrisa leve intermitente."""
        now = time.monotonic()
        elapsed = now - self._start_time
        dt_since_last = now - self._last_blink_time

        # --- Cabeza: movimiento lento sinusoidal ---
        head_yaw = math.sin(elapsed * 0.3) * 2.5
        head_pitch = math.sin(elapsed * 0.2 + 1.0) * 1.5
        head_roll = math.sin(elapsed * 0.15 + 2.0) * 0.8

        # --- Parpadeo ---
        blink = self._update_blink(now, dt_since_last)

        # --- Mirada: micro-drift ---
        gaze_x = math.sin(elapsed * 0.4) * 0.05
        gaze_y = math.sin(elapsed * 0.35 + 0.5) * 0.03

        # --- Sonrisa leve intermitente ---
        smile = max(0.0, math.sin(elapsed * 0.12) * 0.15)

        # --- Cejas: micro-expresión ---
        brow_l = max(0.0, math.sin(elapsed * 0.25 + 0.7) * 0.1)
        brow_r = max(0.0, math.sin(elapsed * 0.25 + 1.3) * 0.1)

        return TrackingData(
            head_yaw=head_yaw,
            head_pitch=head_pitch,
            head_roll=head_roll,
            left_eye_gaze=Vec2(x=gaze_x, y=gaze_y),
            right_eye_gaze=Vec2(x=gaze_x, y=gaze_y),
            mouth_open=0.0,
            brow_left_up=brow_l,
            brow_right_up=brow_r,
            smile=smile,
            left_blink=blink,
            right_blink=blink,
            timestamp=elapsed,
        )

    def _update_blink(self, now: float, since_last: float) -> float:
        """Simula parpadeo periódico con duración y frecuencia natural."""
        # Intervalo entre parpadeos: 2-5 segundos
        if self._blink_phase <= 0.0 and since_last > random.uniform(2.0, 5.0):
            self._last_blink_time = now
            self._blink_phase = 0.2  # duración total del parpadeo

        if self._blink_phase > 0.0:
            # Normalizar fase: 0→0.1 cierra, 0.1→0.2 abre
            progress = 0.2 - self._blink_phase
            if progress < 0.1:
                # Cerrando: 0 → 1
                self._blink_state = min(1.0, progress / 0.1)
            else:
                # Abriendo: 1 → 0
                self._blink_state = max(0.0, 1.0 - (progress - 0.1) / 0.1)
            self._blink_phase -= 0.016  # ~60fps step
            if self._blink_phase <= 0.0:
                self._blink_phase = 0.0
                self._blink_state = 0.0
        else:
            self._blink_state = 0.0

        return self._blink_state
