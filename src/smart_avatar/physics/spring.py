"""Runtime spring physics engine for real-time avatar simulation.

Provides Spring, SpringChain, and BreathingSimulator classes that run
at 60 fps using numpy for vector math and semi-implicit Euler integration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

Vec2Array = np.ndarray  # shape (2,) — numpy array, distinct from core.types.Vec2 dataclass


def _vec(x: float = 0.0, y: float = 0.0) -> Vec2Array:
    return np.array([x, y], dtype=np.float64)


# ---------------------------------------------------------------------------
# Single Spring
# ---------------------------------------------------------------------------

@dataclass
class Spring:
    """A single spring-mass damper element in 2D.

    Physics model (semi-implicit Euler):
        a = (-stiffness * (pos - target) - damping * vel) / mass
        vel += a * dt
        pos += vel * dt

    Attributes:
        position: Current position.
        velocity: Current velocity.
        target: Rest / target position the spring pulls toward.
        stiffness: Spring constant (N/m equivalent). Higher = snappier.
        damping: Velocity damping coefficient. Higher = less oscillation.
        mass: Mass of the attached object. Higher = slower response.
    """

    position: Vec2Array = field(default_factory=_vec)
    velocity: Vec2Array = field(default_factory=_vec)
    target: Vec2Array = field(default_factory=_vec)
    stiffness: float = 15.0
    damping: float = 2.0
    mass: float = 0.5

    def update(self, dt: float) -> Vec2Array:
        """Advance simulation by *dt* seconds. Returns new position."""
        displacement = self.position - self.target
        acceleration = (-self.stiffness * displacement - self.damping * self.velocity) / self.mass
        self.velocity = self.velocity + acceleration * dt
        self.position = self.position + self.velocity * dt
        return self.position

    def set_target(self, x: float, y: float) -> None:
        self.target = _vec(x, y)

    def set_position(self, x: float, y: float) -> None:
        self.position = _vec(x, y)

    def reset(self) -> None:
        self.velocity = _vec(0.0, 0.0)


# ---------------------------------------------------------------------------
# Spring Chain (hair / ribbon / tail)
# ---------------------------------------------------------------------------

@dataclass
class SpringChain:
    """A chain of connected springs for hair, ribbons, tails, etc.

    Each spring segment pulls the next one toward a position relative to
    its predecessor.  The first spring's target is set externally (typically
    attached to a bone); subsequent springs follow.

    Attributes:
        springs: Ordered list of springs (index 0 = root / closest to body).
        segment_length: Rest distance between consecutive segments.
        gravity: Downward acceleration applied each frame.
    """

    springs: list[Spring] = field(default_factory=list)
    segment_length: float = 10.0
    gravity: float = 0.0

    # -- helpers --------------------------------------------------------------

    @classmethod
    def create(
        cls,
        num_segments: int,
        stiffness: float = 15.0,
        damping: float = 2.0,
        mass: float = 0.5,
        segment_length: float = 10.0,
        gravity: float = 0.0,
        start_x: float = 0.0,
        start_y: float = 0.0,
    ) -> SpringChain:
        """Factory: build a chain with *num_segments* springs spaced vertically."""
        springs: list[Spring] = []
        for i in range(num_segments):
            s = Spring(
                position=_vec(start_x, start_y + i * segment_length),
                target=_vec(start_x, start_y + i * segment_length),
                velocity=_vec(0.0, 0.0),
                stiffness=stiffness,
                damping=damping,
                mass=mass,
            )
            springs.append(s)
        return cls(
            springs=springs,
            segment_length=segment_length,
            gravity=gravity,
        )

    # -- simulation -----------------------------------------------------------

    def update(self, dt: float) -> list[Vec2Array]:
        """Advance the full chain by *dt* seconds.

        Returns a list of current positions for every segment.
        """
        if not self.springs:
            return []

        n = len(self.springs)
        grav = _vec(0.0, self.gravity)

        for i, spring in enumerate(self.springs):
            # Apply gravity as an external force via acceleration adjustment.
            spring.velocity = spring.velocity + grav * dt

            if i == 0:
                # Root spring: just update against its external target.
                spring.update(dt)
            else:
                prev = self.springs[i - 1]
                # Target = previous spring position + rest offset downward.
                rest_offset = _vec(0.0, self.segment_length)
                spring.target = prev.position + rest_offset
                spring.update(dt)

        return [s.position.copy() for s in self.springs]

    @property
    def positions(self) -> list[Vec2Array]:
        return [s.position.copy() for s in self.springs]

    def __len__(self) -> int:
        return len(self.springs)


# ---------------------------------------------------------------------------
# Breathing Simulator
# ---------------------------------------------------------------------------

@dataclass
class BreathingSimulator:
    """Sinusoidal breathing oscillation for torso / chest.

    Produces a smooth vertical offset that mimics inhale/exhale cycles.

    Attributes:
        rate: Breaths per minute (typical adult: 12-20).
        amplitude: Maximum vertical offset in world units.
        phase: Current phase in radians (0..2pi).
        vertical: If True, oscillation is on Y; else on X.
    """

    rate: float = 16.0
    amplitude: float = 0.02
    phase: float = 0.0
    vertical: bool = True

    _tau: float = field(default=2.0 * math.pi, init=False, repr=False)

    def update(self, dt: float) -> Vec2Array:
        """Advance by *dt* seconds. Returns the current offset vector."""
        self.phase += self._tau * (self.rate / 60.0) * dt
        # Wrap to [0, 2pi) to avoid precision drift over long sessions.
        self.phase %= self._tau
        value = math.sin(self.phase) * self.amplitude
        if self.vertical:
            return _vec(0.0, value)
        return _vec(value, 0.0)

    @property
    def current_offset(self) -> Vec2Array:
        """Snapshot of the current offset without advancing time."""
        value = math.sin(self.phase) * self.amplitude
        if self.vertical:
            return _vec(0.0, value)
        return _vec(value, 0.0)


# ---------------------------------------------------------------------------
# Spring Engine (orchestrator)
# ---------------------------------------------------------------------------

class SpringEngine:
    """Top-level runtime engine that owns all active springs.

    Usage::

        engine = SpringEngine(fps=60)
        chain_id = engine.add_chain(SpringChain.create(5, stiffness=15.0, ...))
        engine.add_breathing(rate=16, amplitude=0.02)

        while running:
            engine.tick()          # advances internal clock
            positions = engine.get_chain(chain_id)
            offset = engine.get_breathing_offset()

    The engine is deliberately lightweight: no threading, no locking — the
    caller is expected to call ``tick()`` from the main render loop.
    """

    def __init__(self, fps: float = 60.0) -> None:
        self.target_fps = fps
        self.dt = 1.0 / fps
        self._elapsed: float = 0.0

        self._chains: dict[int, SpringChain] = {}
        self._singles: dict[int, Spring] = {}
        self._breathers: dict[int, BreathingSimulator] = {}

        self._next_id: int = 0

    # -- id allocation --------------------------------------------------------

    def _alloc_id(self) -> int:
        id_ = self._next_id
        self._next_id += 1
        return id_

    # -- registration ---------------------------------------------------------

    def add_chain(self, chain: SpringChain) -> int:
        """Register a SpringChain. Returns its integer id."""
        id_ = self._alloc_id()
        self._chains[id_] = chain
        return id_

    def add_spring(self, spring: Spring) -> int:
        """Register a standalone Spring. Returns its integer id."""
        id_ = self._alloc_id()
        self._singles[id_] = spring
        return id_

    def add_breathing(
        self,
        rate: float = 16.0,
        amplitude: float = 0.02,
        vertical: bool = True,
    ) -> int:
        """Create and register a BreathingSimulator. Returns its integer id."""
        id_ = self._alloc_id()
        self._breathers[id_] = BreathingSimulator(
            rate=rate, amplitude=amplitude, vertical=vertical,
        )
        return id_

    # -- removal --------------------------------------------------------------

    def remove_chain(self, id_: int) -> None:
        self._chains.pop(id_, None)

    def remove_spring(self, id_: int) -> None:
        self._singles.pop(id_, None)

    def remove_breathing(self, id_: int) -> None:
        self._breathers.pop(id_, None)

    def clear(self) -> None:
        """Remove all registered elements."""
        self._chains.clear()
        self._singles.clear()
        self._breathers.clear()

    # -- simulation tick ------------------------------------------------------

    def tick(self, dt: float | None = None) -> None:
        """Advance all springs by one frame.

        Args:
            dt: Override timestep (seconds).  If *None*, uses the fixed
                timestep computed from ``target_fps``.
        """
        step = dt if dt is not None else self.dt
        self._elapsed += step

        for chain in self._chains.values():
            chain.update(step)
        for spring in self._singles.values():
            spring.update(step)
        for breather in self._breathers.values():
            breather.update(step)

    # -- queries --------------------------------------------------------------

    def get_chain(self, id_: int) -> list[Vec2Array] | None:
        chain = self._chains.get(id_)
        return chain.positions if chain is not None else None

    def get_spring_position(self, id_: int) -> Vec2Array | None:
        spring = self._singles.get(id_)
        return spring.position.copy() if spring is not None else None

    def get_breathing_offset(self, id_: int) -> Vec2Array | None:
        breather = self._breathers.get(id_)
        return breather.current_offset.copy() if breather is not None else None

    @property
    def elapsed(self) -> float:
        return self._elapsed

    def __len__(self) -> int:
        return len(self._chains) + len(self._singles) + len(self._breathers)
