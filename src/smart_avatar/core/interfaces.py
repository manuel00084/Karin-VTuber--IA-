"""Interfaces abstractas del Smart Avatar System."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.smart_avatar.core.types import (
    AnalysisResult,
    AvatarData,
    BlendShapes,
    Mesh,
    Physics,
    Skeleton,
)

if TYPE_CHECKING:
    from src.smart_avatar.tracking.tracking_interface import TrackingData


class IAnalyzer(ABC):
    """Analiza una imagen de referencia del avatar."""

    @abstractmethod
    def analyze(self, image_path: str) -> AnalysisResult: ...


class IMeshGenerator(ABC):
    """Genera la malla 3D a partir del análisis."""

    @abstractmethod
    def generate(self, analysis: AnalysisResult) -> Mesh: ...


class ISkeletonGenerator(ABC):
    """Genera el esqueleto articulado."""

    @abstractmethod
    def generate(self, mesh: Mesh, analysis: AnalysisResult) -> Skeleton: ...


class IBlendShapeGenerator(ABC):
    """Genera los blend shapes para expresiones faciales."""

    @abstractmethod
    def generate(self, mesh: Mesh, skeleton: Skeleton) -> BlendShapes: ...


class IPhysicsGenerator(ABC):
    """Genera configuraciones de física (hair-spring, breathing, etc.)."""

    @abstractmethod
    def generate(self, skeleton: Skeleton) -> Physics: ...


class IRenderer(ABC):
    """Motor de renderizado del avatar."""

    @abstractmethod
    def init(self) -> None: ...

    @abstractmethod
    def render(self, avatar: AvatarData, tracking_data: TrackingData) -> None: ...

    @abstractmethod
    def cleanup(self) -> None: ...


class IShaderEffect(ABC):
    """Efecto de shader aplicable al avatar."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def apply(self, **params) -> None: ...
