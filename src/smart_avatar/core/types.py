"""Tipos de datos del Smart Avatar System."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Vectores
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Vec2:
    x: float = 0.0
    y: float = 0.0


@dataclass(frozen=True, slots=True)
class Vec3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0


# ---------------------------------------------------------------------------
# Geometría del Mesh
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Vertex:
    position: Vec3 = field(default_factory=Vec3)
    uv: Vec2 = field(default_factory=Vec2)
    weight: float = 1.0


@dataclass(frozen=True, slots=True)
class Triangle:
    v0: int
    v1: int
    v2: int


@dataclass(slots=True)
class MeshRegion:
    name: str
    vertices: list[Vertex] = field(default_factory=list)
    triangles: list[Triangle] = field(default_factory=list)
    density: int = 0  # nivel de densidad: 0=base, 1=media, 2=alta


@dataclass(slots=True)
class Mesh:
    regions: dict[str, MeshRegion] = field(default_factory=dict)
    texture_size: tuple[int, int] = (512, 512)


# ---------------------------------------------------------------------------
# Esqueleto
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class Bone:
    name: str
    parent: str | None = None
    position: Vec3 = field(default_factory=Vec3)
    rotation: Vec3 = field(default_factory=Vec3)  # euler (grados)
    children: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Skeleton:
    root: str = "Hips"
    bones: list[Bone] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Física (spring / breathing)
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class SpringConfig:
    stiffness: float = 0.5
    damping: float = 0.1
    mass: float = 1.0
    gravity: float = 0.0


@dataclass(slots=True)
class PhysicsBone:
    bone_name: str
    spring: SpringConfig = field(default_factory=SpringConfig)
    anchor: Vec3 = field(default_factory=Vec3)


@dataclass(slots=True)
class Physics:
    springs: list[PhysicsBone] = field(default_factory=list)
    breathing_config: SpringConfig = field(default_factory=SpringConfig)


# ---------------------------------------------------------------------------
# Blend Shapes
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class BlendShapeTarget:
    name: str
    vertex_deltas: list[tuple[int, Vec3]] = field(default_factory=list)


@dataclass(slots=True)
class BlendShapes:
    targets: dict[str, BlendShapeTarget] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Análisis del avatar (Image Analyzer)
# ---------------------------------------------------------------------------

class BodyPartType(enum.Enum):
    HEAD = "head"
    NECK = "neck"
    HAIR = "hair"
    LEFT_EYE = "left_eye"
    RIGHT_EYE = "right_eye"
    LEFT_EYEBROW = "left_eyebrow"
    RIGHT_EYEBROW = "right_eyebrow"
    NOSE = "nose"
    MOUTH = "mouth"
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_HAND = "left_hand"
    RIGHT_HAND = "right_hand"
    CHEST = "chest"
    TORSO = "torso"
    HIPS = "hips"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    LEFT_FOOT = "left_foot"
    RIGHT_FOOT = "right_foot"
    ACCESSORY = "accessory"


@dataclass(slots=True)
class BodyRegion:
    type: BodyPartType
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
    confidence: float = 0.0
    landmarks: list[Vec2] = field(default_factory=list)


@dataclass(slots=True)
class AnalysisResult:
    regions: list[BodyRegion] = field(default_factory=list)
    image_size: tuple[int, int] = (0, 0)
    character_type: str = "unknown"  # anime, realistic, chibi, etc.


# ---------------------------------------------------------------------------
# Datos completos del Avatar
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class AvatarData:
    mesh: Mesh = field(default_factory=Mesh)
    skeleton: Skeleton = field(default_factory=Skeleton)
    blendshapes: BlendShapes = field(default_factory=BlendShapes)
    physics: Physics = field(default_factory=Physics)
    metadata: dict[str, Any] = field(default_factory=dict)
    texture_path: str = ""


# ---------------------------------------------------------------------------
# Grafo de relaciones del cuerpo
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class BodyPartNode:
    name: str
    dependencies: list[str] = field(default_factory=list)
