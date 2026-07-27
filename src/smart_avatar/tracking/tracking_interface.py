"""Interfaces abstractas y tipos de datos para tracking facial."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.smart_avatar.core.types import Vec2


@dataclass(slots=True)
class TrackingData:
    """Datos crudos de tracking facial y corporal.

    Todos los ángulos están en grados. Valores de expresión en rango [0, 1]
    salvo que se indique lo contrario.
    """

    # Rotación de cabeza
    head_yaw: float = 0.0      # rotación lateral (izquierda/derecha)
    head_pitch: float = 0.0    # rotación vertical (arriba/abajo)
    head_roll: float = 0.0     # inclinación lateral

    # Mirada de ojos
    left_eye_gaze: Vec2 = field(default_factory=Vec2)
    right_eye_gaze: Vec2 = field(default_factory=Vec2)

    # Boca
    mouth_open: float = 0.0    # 0.0 = cerrado, 1.0 = abierto

    # Cejas
    brow_left_up: float = 0.0   # 0.0 = neutro, 1.0 = levantado
    brow_right_up: float = 0.0  # 0.0 = neutro, 1.0 = levantado

    # Sonrisa
    smile: float = 0.0         # 0.0 = sin sonrisa, 1.0 = sonrisa máxima

    # Parpadeo (0 = abierto, 1 = cerrado)
    left_blink: float = 0.0
    right_blink: float = 0.0

    # Timestamp del frame
    timestamp: float = field(default_factory=time.monotonic)


class ITrackingProvider(ABC):
    """Interfaz para fuentes de datos de tracking en tiempo real.

    Cada proveedor (webcam + MediaPipe, Phone VMC, etc.) implementa
    esta interfaz para entregar ``TrackingData`` estandarizado al avatar.
    """

    @abstractmethod
    def start(self) -> bool:
        """Inicializa la conexión / cámara. Devuelve True si arrancó OK."""
        ...

    @abstractmethod
    def stop(self) -> None:
        """Libera recursos del proveedor."""
        ...

    @abstractmethod
    def get_data(self) -> TrackingData:
        """Lee el último frame de tracking disponible."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """True si el proveedor está activo y entregando datos."""
        ...
