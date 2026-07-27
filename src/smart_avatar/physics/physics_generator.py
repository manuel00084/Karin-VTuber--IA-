"""PhysicsGenerator — builds Physics config from Skeleton + Mesh.

Implements ``IPhysicsGenerator`` and auto-creates spring / breathing
configurations for hair, clothes, accessories, torso, chest and head.
"""

from __future__ import annotations

from src.smart_avatar.core.interfaces import IPhysicsGenerator
from src.smart_avatar.core.types import (
    BodyPartType,
    Mesh,
    Physics,
    PhysicsBone,
    Skeleton,
    SpringConfig,
    Vec3,
)


# ---------------------------------------------------------------------------
# Default tuning constants
# ---------------------------------------------------------------------------

_HAIR_STIFFNESS = 15.0
_HAIR_DAMPING = 2.0
_HAIR_MASS = 0.5
_HAIR_SEGMENTS_MIN = 3
_HAIR_SEGMENTS_MAX = 5

_CLOTH_STIFFNESS = 20.0
_CLOTH_DAMPING = 3.0
_CLOTH_MASS = 0.8

_ACC_STIFFNESS = 12.0
_ACC_DAMPING = 1.5
_ACC_MASS = 0.3

_HEAD_STIFFNESS = 30.0
_HEAD_DAMPING = 4.0
_HEAD_MASS = 0.2

_BREATHING_RATE = 16.0  # breaths per minute
_BREATHING_AMP = 0.02

_TORSO_STIFFNESS = 25.0
_TORSO_DAMPING = 3.5
_TORSO_MASS = 1.0

_CHEST_STIFFNESS = 18.0
_CHEST_DAMPING = 2.5
_CHEST_MASS = 0.7


# ---------------------------------------------------------------------------
# Helper: bone lookup
# ---------------------------------------------------------------------------

def _bone_map(skeleton: Skeleton) -> dict[str, int]:
    """Return ``{bone_name: index}`` for fast lookups."""
    return {b.name: i for i, b in enumerate(skeleton.bones)}


def _find_bone(skeleton: Skeleton, *names: str) -> str | None:
    """Return the first bone name that exists in *skeleton*, or None."""
    bm = _bone_map(skeleton)
    for name in names:
        if name in bm:
            return name
    return None


# ---------------------------------------------------------------------------
# PhysicsGenerator
# ---------------------------------------------------------------------------

class PhysicsGenerator(IPhysicsGenerator):
    """Generates ``Physics`` configuration from skeleton + mesh analysis.

    The generator inspects bone names and mesh region names to decide
    which springs / breathing elements to create and with what
    parameters.  Missing bones or regions are silently skipped so the
    generator never fails — it just produces less physics.
    """

    def generate(self, skeleton: Skeleton, mesh: Mesh | None = None) -> Physics:
        """Build a complete ``Physics`` config.

        Args:
            skeleton: The avatar's articulated skeleton.
            mesh: Optional mesh (used to detect clothing / accessory regions).

        Returns:
            A ``Physics`` dataclass ready for the runtime ``SpringEngine``.
        """
        springs: list[PhysicsBone] = []

        springs.extend(self._create_hair_physics(skeleton))
        springs.extend(self._create_clothing_physics(skeleton, mesh))
        springs.extend(self._create_accessory_physics(skeleton, mesh))
        springs.extend(self._create_torso_physics(skeleton))
        springs.extend(self._create_chest_physics(skeleton))
        springs.extend(self._create_head_physics(skeleton))

        breathing_config = SpringConfig(
            stiffness=0.0,
            damping=0.0,
            mass=_BREATHING_RATE / 60.0,  # store frequency in Hz (16 bpm → ~0.267 Hz)
            gravity=0.0,
        )

        return Physics(springs=springs, breathing_config=breathing_config)

    # -- per-region generators ------------------------------------------------

    def _create_hair_physics(self, skeleton: Skeleton) -> list[PhysicsBone]:
        """Create spring chain config for hair bones.

        Looks for bones with common hair naming conventions and generates
        a chain of ``PhysicsBone`` entries with progressively lower stiffness
        to simulate natural hair motion.
        """
        hair_names = [
            "Hair", "Hair_01", "Hair_02", "Hair_03",
            "Hair_L", "Hair_R", "Bangs", "Ponytail",
            "HairRoot", "HairTip",
        ]
        head_bone = _find_bone(skeleton, "Head", "head", "Bip01_Head")
        if head_bone is None:
            return []

        bones: list[PhysicsBone] = []
        chain_length = _HAIR_SEGMENTS_MIN

        for name in hair_names:
            if not _find_bone(skeleton, name):
                continue
            chain_length = min(chain_length + 1, _HAIR_SEGMENTS_MAX)

        for i in range(chain_length):
            factor = 1.0 - (i * 0.15)  # softer toward tips
            bones.append(PhysicsBone(
                bone_name=f"{head_bone}_hair_{i}",
                spring=SpringConfig(
                    stiffness=_HAIR_STIFFNESS * factor,
                    damping=_HAIR_DAMPING * factor,
                    mass=_HAIR_MASS,
                    gravity=0.5,
                ),
                anchor=Vec3(0.0, 0.0, -i * 0.02),
            ))

        return bones

    def _create_clothing_physics(
        self, skeleton: Skeleton, mesh: Mesh | None,
    ) -> list[PhysicsBone]:
        """Sprims on clothing edge bones (skirt, cape, sleeves)."""
        clothing_bone_patterns = [
            "Skirt", "Skirt_01", "Skirt_02", "Skirt_03",
            "Cape", "Cape_01", "Cape_02",
            "Sleeve_L", "Sleeve_R",
            "CoatTail_L", "CoatTail_R",
        ]
        bones: list[PhysicsBone] = []
        for name in clothing_bone_patterns:
            real = _find_bone(skeleton, name)
            if real is None:
                continue
            bones.append(PhysicsBone(
                bone_name=real,
                spring=SpringConfig(
                    stiffness=_CLOTH_STIFFNESS,
                    damping=_CLOTH_DAMPING,
                    mass=_CLOTH_MASS,
                    gravity=0.3,
                ),
                anchor=Vec3(0.0, 0.0, 0.0),
            ))

        # If the mesh has a named clothing region, add edge springs.
        if mesh is not None:
            for region_name in mesh.regions:
                low = region_name.lower()
                if any(kw in low for kw in ("cloth", "dress", "skirt", "cape")):
                    bones.append(PhysicsBone(
                        bone_name=f"mesh_{region_name}",
                        spring=SpringConfig(
                            stiffness=_CLOTH_STIFFNESS * 0.8,
                            damping=_CLOTH_DAMPING,
                            mass=_CLOTH_MASS,
                        ),
                        anchor=Vec3(0.0, 0.0, 0.0),
                    ))

        return bones

    def _create_accessory_physics(
        self, skeleton: Skeleton, mesh: Mesh | None,
    ) -> list[PhysicsBone]:
        """Springs for accessories (hair ribbons, earrings, brooches)."""
        acc_patterns = [
            "Ribbon_L", "Ribbon_R", "Ribbon_01", "Ribbon_02",
            "Earring_L", "Earring_R",
            "Brooch", "Accessory", "Accessory_01", "Accessory_02",
            "Tail", "Tail_01", "Tail_02",
            "Wing_L", "Wing_R",
        ]
        bones: list[PhysicsBone] = []
        for name in acc_patterns:
            real = _find_bone(skeleton, name)
            if real is None:
                continue
            bones.append(PhysicsBone(
                bone_name=real,
                spring=SpringConfig(
                    stiffness=_ACC_STIFFNESS,
                    damping=_ACC_DAMPING,
                    mass=_ACC_MASS,
                ),
                anchor=Vec3(0.0, 0.0, 0.0),
            ))

        if mesh is not None:
            for region_name in mesh.regions:
                low = region_name.lower()
                if any(kw in low for kw in ("accessory", "ribbon", "earring")):
                    bones.append(PhysicsBone(
                        bone_name=f"mesh_{region_name}",
                        spring=SpringConfig(
                            stiffness=_ACC_STIFFNESS,
                            damping=_ACC_DAMPING,
                            mass=_ACC_MASS,
                        ),
                        anchor=Vec3(0.0, 0.0, 0.0),
                    ))

        return bones

    def _create_torso_physics(self, skeleton: Skeleton) -> list[PhysicsBone]:
        """Subtle spring on the torso / spine for breathing-related sway."""
        torso_bone = _find_bone(skeleton, "Spine", "Spine_01", "Torso", "Hips")
        if torso_bone is None:
            return []
        return [PhysicsBone(
            bone_name=torso_bone,
            spring=SpringConfig(
                stiffness=_TORSO_STIFFNESS,
                damping=_TORSO_DAMPING,
                mass=_TORSO_MASS,
                gravity=0.0,
            ),
            anchor=Vec3(0.0, 0.0, 0.0),
        )]

    def _create_chest_physics(self, skeleton: Skeleton) -> list[PhysicsBone]:
        """Breathing + slight secondary motion on the chest bone."""
        chest_bone = _find_bone(
            skeleton, "Chest", "Spine_02", "UpperSpine", "Spine1",
        )
        if chest_bone is None:
            return []
        return [PhysicsBone(
            bone_name=chest_bone,
            spring=SpringConfig(
                stiffness=_CHEST_STIFFNESS,
                damping=_CHEST_DAMPING,
                mass=_CHEST_MASS,
                gravity=0.0,
            ),
            anchor=Vec3(0.0, 0.0, 0.0),
        )]

    def _create_head_physics(self, skeleton: Skeleton) -> list[PhysicsBone]:
        """Very subtle spring on the head for natural micro-movement."""
        head_bone = _find_bone(skeleton, "Head", "head", "Bip01_Head")
        if head_bone is None:
            return []
        return [PhysicsBone(
            bone_name=head_bone,
            spring=SpringConfig(
                stiffness=_HEAD_STIFFNESS,
                damping=_HEAD_DAMPING,
                mass=_HEAD_MASS,
                gravity=0.0,
            ),
            anchor=Vec3(0.0, 0.0, 0.0),
        )]
