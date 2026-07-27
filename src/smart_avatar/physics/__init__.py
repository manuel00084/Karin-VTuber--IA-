"""Physics subsystem — config generation and runtime simulation.

Public API::

    from src.smart_avatar.physics import PhysicsGenerator, SpringEngine

    # One-time: generate config from skeleton + mesh
    generator = PhysicsGenerator()
    physics_cfg = generator.generate(skeleton, mesh)

    # Runtime: simulate every frame
    engine = SpringEngine(fps=60)
    ...
    engine.tick()
"""

from src.smart_avatar.physics.physics_generator import PhysicsGenerator
from src.smart_avatar.physics.spring import (
    BreathingSimulator,
    Spring,
    SpringChain,
    SpringEngine,
)

__all__ = [
    "PhysicsGenerator",
    "Spring",
    "SpringChain",
    "SpringEngine",
    "BreathingSimulator",
]
