"""Tracking — interfaces y gestión de datos de captura en tiempo real."""

from src.smart_avatar.tracking.tracking_interface import (
    ITrackingProvider,
    TrackingData,
)
from src.smart_avatar.tracking.tracking_manager import TrackingManager

__all__ = [
    "ITrackingProvider",
    "TrackingData",
    "TrackingManager",
]
