"""Core — tipos, interfaces y grafo corporal del Smart Avatar System."""

from src.smart_avatar.core.body_graph import BodyRelationshipGraph, create_default_graph
from src.smart_avatar.core.interfaces import (
    IAnalyzer,
    IBlendShapeGenerator,
    IMeshGenerator,
    IPhysicsGenerator,
    IRenderer,
    IShaderEffect,
    ISkeletonGenerator,
)
from src.smart_avatar.core.types import (
    AnalysisResult,
    AvatarData,
    BlendShapeTarget,
    BlendShapes,
    BodyPartNode,
    BodyPartType,
    BodyRegion,
    Bone,
    Mesh,
    MeshRegion,
    Physics,
    PhysicsBone,
    Skeleton,
    SpringConfig,
    Triangle,
    Vec2,
    Vec3,
    Vertex,
)
from src.smart_avatar.tracking.tracking_interface import (
    ITrackingProvider,
    TrackingData,
)

__all__ = [
    # Tipos
    "Vec2",
    "Vec3",
    "Vertex",
    "Triangle",
    "MeshRegion",
    "Mesh",
    "Bone",
    "Skeleton",
    "SpringConfig",
    "PhysicsBone",
    "Physics",
    "BlendShapeTarget",
    "BlendShapes",
    "BodyPartType",
    "BodyRegion",
    "AnalysisResult",
    "AvatarData",
    "TrackingData",
    "BodyPartNode",
    # Interfaces
    "IAnalyzer",
    "IMeshGenerator",
    "ISkeletonGenerator",
    "IBlendShapeGenerator",
    "IPhysicsGenerator",
    "IRenderer",
    "ITrackingProvider",
    "IShaderEffect",
    # Grafo
    "BodyRelationshipGraph",
    "create_default_graph",
]
