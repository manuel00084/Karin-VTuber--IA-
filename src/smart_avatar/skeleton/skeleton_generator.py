"""Skeleton generator — builds a 2D controller hierarchy from mesh analysis.

The skeleton is NOT a 3D bone rig.  Each Bone represents a 2D controller that
drives mesh deformation (position, rotation, scale) in screen-space.  Bone
positions are estimated from the bounding boxes returned by the image analyzer.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.smart_avatar.core.interfaces import ISkeletonGenerator
from src.smart_avatar.core.types import (
    AnalysisResult,
    BodyPartType,
    Bone,
    Mesh,
    Skeleton,
    Vec3,
)


# ---------------------------------------------------------------------------
# Hierarchy definition: (bone_name, parent_name | None)
# ---------------------------------------------------------------------------

_HIERARCHY: List[Tuple[str, Optional[str]]] = [
    ("Root", None),
    ("Hip", "Root"),
    ("Torso", "Hip"),
    ("Chest", "Torso"),
    ("Neck", "Chest"),
    ("Head", "Neck"),
    ("Jaw", "Head"),
    ("LeftEye", "Head"),
    ("RightEye", "Head"),
    ("LeftBrow", "Head"),
    ("RightBrow", "Head"),
    ("LeftShoulder", "Chest"),
    ("LeftArm", "LeftShoulder"),
    ("LeftHand", "LeftArm"),
    ("RightShoulder", "Chest"),
    ("RightArm", "RightShoulder"),
    ("RightHand", "RightArm"),
    ("LeftLeg", "Hip"),
    ("LeftFoot", "LeftLeg"),
    ("RightLeg", "Hip"),
    ("RightFoot", "RightLeg"),
]

# Mapping from bone names to the BodyPartType used to locate them.
_BONE_TO_BODY_PART: Dict[str, BodyPartType] = {
    "Head": BodyPartType.HEAD,
    "Neck": BodyPartType.NECK,
    "LeftEye": BodyPartType.LEFT_EYE,
    "RightEye": BodyPartType.RIGHT_EYE,
    "LeftBrow": BodyPartType.LEFT_EYEBROW,
    "RightBrow": BodyPartType.RIGHT_EYEBROW,
    "Jaw": BodyPartType.MOUTH,
    "LeftShoulder": BodyPartType.LEFT_SHOULDER,
    "RightShoulder": BodyPartType.RIGHT_SHOULDER,
    "LeftArm": BodyPartType.LEFT_ARM,
    "RightArm": BodyPartType.RIGHT_ARM,
    "LeftHand": BodyPartType.LEFT_HAND,
    "RightHand": BodyPartType.RIGHT_HAND,
    "Chest": BodyPartType.CHEST,
    "Torso": BodyPartType.TORSO,
    "Hip": BodyPartType.HIPS,
    "LeftLeg": BodyPartType.LEFT_LEG,
    "RightLeg": BodyPartType.RIGHT_LEG,
    "LeftFoot": BodyPartType.LEFT_FOOT,
    "RightFoot": BodyPartType.RIGHT_FOOT,
}


def _bbox_center(bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
    """Return the center (cx, cy) of a (x, y, w, h) bounding box."""
    x, y, w, h = bbox
    return x + w / 2.0, y + h / 2.0


def _bbox_size(bbox: Tuple[int, int, int, int]) -> Tuple[float, float]:
    """Return the (width, height) of a bounding box."""
    return float(bbox[2]), float(bbox[3])


class SkeletonGenerator(ISkeletonGenerator):
    """Generates a flat 2D-controller skeleton from *Mesh* and *AnalysisResult*.

    The generated ``Skeleton`` contains one :class:`Bone` per logical body
    part.  Each bone stores a local position relative to its parent, a
    local rotation (Z-axis Euler in degrees for 2D rotation), and references
    its parent / children.

    Algorithm
    ---------
    1. Build the parent-child hierarchy from a fixed definition.
    2. For every bone whose body part was detected in the analysis, compute a
       local position by converting the region center into the parent-bone's
       local coordinate system.
    3. Bones without a detected region receive a fallback position estimated
       from their parent's position and the average region size.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, mesh: Mesh, analysis: AnalysisResult) -> Skeleton:
        """Return a fully-populated :class:`Skeleton`.

        Parameters
        ----------
        mesh:
            The avatar mesh (used for vertex-extent fallbacks).
        analysis:
            Body-part detection result from the image analyzer.
        """
        region_map = self._build_region_map(analysis)
        bone_positions = self._estimate_bone_positions(region_map, analysis)
        skeleton = self._build_hierarchy(bone_positions)
        return skeleton

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _build_region_map(
        analysis: AnalysisResult,
    ) -> Dict[BodyPartType, "BodyRegion"]:
        """Index detected body regions by their ``BodyPartType``."""
        from src.smart_avatar.core.types import BodyRegion  # avoid circular

        mapped: Dict[BodyPartType, BodyRegion] = {}
        for region in analysis.regions:
            mapped[region.type] = region
        return mapped

    # -- position estimation ---------------------------------------------

    def _estimate_bone_positions(
        self,
        region_map: Dict[BodyPartType, "BodyRegion"],
        analysis: AnalysisResult,
    ) -> Dict[str, Vec3]:
        """Compute a position for every bone from detected body regions.

        Bones that correspond to a detected ``BodyRegion`` are placed at the
        region center.  Remaining bones are interpolated from their parent
        position using the average detected region size as an offset.
        """
        img_w, img_h = analysis.image_size
        # Normalisation factor so coordinates are roughly in [0, 1].
        norm = max(img_w, img_h) or 1.0

        # Pass 1: bones with a direct region mapping.
        positions: Dict[str, Vec3] = {}
        for bone_name, body_part in _BONE_TO_BODY_PART.items():
            region = region_map.get(body_part)
            if region is not None:
                cx, cy = _bbox_center(region.bbox)
                positions[bone_name] = Vec3(cx / norm, cy / norm, 0.0)

        # Average detected region size (normalised) for fallback offsets.
        avg_h = self._average_region_height(region_map, norm)

        # Pass 2: bones without a region get estimated from their parent.
        for bone_name, parent_name in _HIERARCHY:
            if bone_name in positions:
                continue
            if parent_name is None:
                # Root always at origin.
                positions[bone_name] = Vec3(0.0, 0.0, 0.0)
                continue
            parent_pos = positions.get(parent_name, Vec3())
            positions[bone_name] = self._fallback_position(
                bone_name, parent_pos, avg_h
            )

        return positions

    @staticmethod
    def _average_region_height(
        region_map: Dict[BodyPartType, "BodyRegion"], norm: float
    ) -> float:
        """Average normalised height of all detected regions."""
        heights = [
            _bbox_size(r.bbox)[1] for r in region_map.values()
        ]
        return (sum(heights) / len(heights) / norm) if heights else 0.1

    @staticmethod
    def _fallback_position(
        bone_name: str, parent_pos: Vec3, avg_h: float
    ) -> Vec3:
        """Heuristic position for undetected bones.

        Uses small fixed offsets relative to the parent so the hierarchy
        remains visually sensible even when the analyzer misses a part.
        """
        # Empirical offsets (normalised) keyed by bone name.
        _OFFSETS: Dict[str, Tuple[float, float]] = {
            "Root": (0.0, 0.0),
            "Hip": (0.0, 0.15),
            "Torso": (0.0, -0.10),
            "Chest": (0.0, -0.10),
            "Neck": (0.0, -0.06),
            "Head": (0.0, -0.07),
            "Jaw": (0.0, 0.02),
            "LeftEye": (-0.03, -0.02),
            "RightEye": (0.03, -0.02),
            "LeftBrow": (-0.03, -0.04),
            "RightBrow": (0.03, -0.04),
            "LeftShoulder": (-0.10, -0.02),
            "LeftArm": (-0.08, 0.06),
            "LeftHand": (-0.06, 0.08),
            "RightShoulder": (0.10, -0.02),
            "RightArm": (0.08, 0.06),
            "RightHand": (0.06, 0.08),
            "LeftLeg": (-0.05, 0.12),
            "LeftFoot": (-0.05, 0.10),
            "RightLeg": (0.05, 0.12),
            "RightFoot": (0.05, 0.10),
        }
        dx, dy = _OFFSETS.get(bone_name, (0.0, avg_h * 0.5))
        return Vec3(parent_pos.x + dx, parent_pos.y + dy, 0.0)

    # -- hierarchy construction ------------------------------------------

    def _build_hierarchy(self, positions: Dict[str, Vec3]) -> Skeleton:
        """Create a :class:`Skeleton` from the fixed hierarchy definition.

        Each :class:`Bone` stores a *local* position relative to its parent.
        """
        skeleton = Skeleton(root="Root")

        # Pre-compute world positions so we can derive local offsets.
        world_pos: Dict[str, Vec3] = {}
        for bone_name, parent_name in _HIERARCHY:
            wp = positions.get(bone_name, Vec3())
            world_pos[bone_name] = wp

        # Build children mapping for quick lookup.
        children_map: Dict[Optional[str], List[str]] = {}
        for bone_name, parent_name in _HIERARCHY:
            children_map.setdefault(parent_name, []).append(bone_name)

        # Convert world positions to local (relative to parent).
        for bone_name, parent_name in _HIERARCHY:
            wp = world_pos[bone_name]
            if parent_name is not None and parent_name in world_pos:
                pp = world_pos[parent_name]
                local_pos = Vec3(wp.x - pp.x, wp.y - pp.y, 0.0)
            else:
                local_pos = wp

            children = children_map.get(bone_name, [])

            bone = Bone(
                name=bone_name,
                parent=parent_name,
                position=local_pos,
                rotation=Vec3(0.0, 0.0, 0.0),
                children=children,
            )
            skeleton.bones.append(bone)

        return skeleton
