"""Tests for Spring physics engine."""
import math
import pytest
import numpy as np
from src.smart_avatar.physics.spring import (
    Spring, SpringChain, BreathingSimulator, SpringEngine,
    _vec,
)


class TestSpring:
    def test_creation(self):
        s = Spring()
        np.testing.assert_array_equal(s.position, _vec())
        np.testing.assert_array_equal(s.velocity, _vec())
        np.testing.assert_array_equal(s.target, _vec())
        assert s.stiffness == 15.0
        assert s.damping == 2.0
        assert s.mass == 0.5

    def test_update_toward_target(self):
        s = Spring()
        s.set_position(0.0, 0.0)
        s.set_target(10.0, 0.0)
        for _ in range(60):
            s.update(1.0 / 60.0)
        assert s.position[0] > 5.0  # Should move toward target

    def test_update_converges(self):
        s = Spring(stiffness=20.0, damping=5.0, mass=0.5)
        s.set_position(0.0, 0.0)
        s.set_target(5.0, 0.0)
        for _ in range(300):
            s.update(1.0 / 60.0)
        assert abs(s.position[0] - 5.0) < 0.1

    def test_set_position(self):
        s = Spring()
        s.set_position(3.0, 4.0)
        np.testing.assert_array_almost_equal(s.position, [3.0, 4.0])

    def test_set_target(self):
        s = Spring()
        s.set_target(7.0, 8.0)
        np.testing.assert_array_almost_equal(s.target, [7.0, 8.0])

    def test_reset(self):
        s = Spring()
        s.velocity = _vec(10.0, 20.0)
        s.reset()
        np.testing.assert_array_equal(s.velocity, _vec())

    def test_oscillation(self):
        s = Spring(stiffness=50.0, damping=0.5, mass=0.5)
        s.set_position(0.0, 0.0)
        s.set_target(10.0, 0.0)
        positions = []
        for _ in range(120):
            s.update(1.0 / 60.0)
            positions.append(s.position[0])
        # With low damping, should overshoot
        assert max(positions) > 10.0


class TestSpringChain:
    def test_create(self):
        chain = SpringChain.create(5, segment_length=10.0)
        assert len(chain) == 5
        assert chain.segment_length == 10.0

    def test_empty_chain(self):
        chain = SpringChain()
        result = chain.update(1.0 / 60.0)
        assert result == []

    def test_positions(self):
        chain = SpringChain.create(3, start_x=0.0, start_y=0.0)
        positions = chain.positions
        assert len(positions) == 3
        # Segments should be spaced apart
        assert positions[1][1] > positions[0][1]

    def test_chain_propagation(self):
        chain = SpringChain.create(4, stiffness=20.0, damping=3.0)
        # Move root
        chain.springs[0].set_target(50.0, 0.0)
        for _ in range(120):
            chain.update(1.0 / 60.0)
        # All segments should have moved
        for s in chain.springs:
            assert abs(s.position[0]) > 0.1

    def test_gravity(self):
        chain = SpringChain.create(3, gravity=9.8, stiffness=5.0, damping=2.0)
        for _ in range(120):
            chain.update(1.0 / 60.0)
        positions = chain.positions
        # Bottom segments should be lower due to positive gravity (Y-down screen space)
        assert positions[2][1] > positions[0][1]


class TestBreathingSimulator:
    def test_defaults(self):
        b = BreathingSimulator()
        assert b.rate == 16.0
        assert b.amplitude == 0.02
        assert b.phase == 0.0
        assert b.vertical is True

    def test_update_changes_phase(self):
        b = BreathingSimulator()
        initial_phase = b.phase
        b.update(1.0 / 60.0)
        assert b.phase > initial_phase

    def test_vertical_breathing(self):
        b = BreathingSimulator(vertical=True)
        offsets = []
        for _ in range(120):
            offset = b.update(1.0 / 60.0)
            offsets.append(offset)
        # Y offsets should vary
        y_values = [o[1] for o in offsets]
        assert max(y_values) - min(y_values) > 0.001
        # X should always be 0
        for o in offsets:
            assert o[0] == pytest.approx(0.0)

    def test_horizontal_breathing(self):
        b = BreathingSimulator(vertical=False)
        offset = b.update(1.0 / 60.0)
        # Y should always be 0
        assert offset[1] == pytest.approx(0.0)

    def test_current_offset(self):
        b = BreathingSimulator()
        b.update(1.0 / 60.0)
        offset = b.current_offset
        assert isinstance(offset, np.ndarray)

    def test_phase_wraps(self):
        b = BreathingSimulator(rate=60.0)
        for _ in range(600):
            b.update(1.0 / 60.0)
        assert 0 <= b.phase < 2 * math.pi


class TestSpringEngine:
    def test_creation(self):
        e = SpringEngine(fps=60)
        assert e.target_fps == 60
        assert e.dt == pytest.approx(1.0 / 60.0)
        assert len(e) == 0

    def test_add_chain(self):
        e = SpringEngine()
        chain = SpringChain.create(3)
        id_ = e.add_chain(chain)
        assert id_ == 0
        assert len(e) == 1

    def test_add_spring(self):
        e = SpringEngine()
        s = Spring()
        id_ = e.add_spring(s)
        assert id_ == 0

    def test_add_breathing(self):
        e = SpringEngine()
        id_ = e.add_breathing(rate=16, amplitude=0.02)
        assert id_ == 0

    def test_unique_ids(self):
        e = SpringEngine()
        id1 = e.add_spring(Spring())
        id2 = e.add_spring(Spring())
        id3 = e.add_chain(SpringChain.create(2))
        assert id1 != id2 != id3

    def test_tick(self):
        e = SpringEngine(fps=60)
        chain_id = e.add_chain(SpringChain.create(3))
        e.tick()
        assert e.elapsed > 0
        positions = e.get_chain(chain_id)
        assert positions is not None
        assert len(positions) == 3

    def test_tick_custom_dt(self):
        e = SpringEngine()
        e.tick(dt=0.1)
        assert e.elapsed == pytest.approx(0.1)

    def test_get_chain_nonexistent(self):
        e = SpringEngine()
        assert e.get_chain(999) is None

    def test_get_spring_position(self):
        e = SpringEngine()
        s = Spring()
        s.set_position(5.0, 3.0)
        id_ = e.add_spring(s)
        pos = e.get_spring_position(id_)
        np.testing.assert_array_almost_equal(pos, [5.0, 3.0])

    def test_get_spring_position_nonexistent(self):
        e = SpringEngine()
        assert e.get_spring_position(999) is None

    def test_get_breathing_offset(self):
        e = SpringEngine()
        id_ = e.add_breathing()
        e.tick()
        offset = e.get_breathing_offset(id_)
        assert offset is not None

    def test_get_breathing_offset_nonexistent(self):
        e = SpringEngine()
        assert e.get_breathing_offset(999) is None

    def test_remove_chain(self):
        e = SpringEngine()
        id_ = e.add_chain(SpringChain.create(2))
        e.remove_chain(id_)
        assert e.get_chain(id_) is None

    def test_remove_spring(self):
        e = SpringEngine()
        id_ = e.add_spring(Spring())
        e.remove_spring(id_)
        assert e.get_spring_position(id_) is None

    def test_remove_breathing(self):
        e = SpringEngine()
        id_ = e.add_breathing()
        e.remove_breathing(id_)
        assert e.get_breathing_offset(id_) is None

    def test_clear(self):
        e = SpringEngine()
        e.add_chain(SpringChain.create(2))
        e.add_spring(Spring())
        e.add_breathing()
        assert len(e) == 3
        e.clear()
        assert len(e) == 0

    def test_multiple_ticks_converge(self):
        e = SpringEngine(fps=60)
        s = Spring(stiffness=20.0, damping=5.0)
        s.set_position(0.0, 0.0)
        s.set_target(10.0, 0.0)
        e.add_spring(s)
        for _ in range(300):
            e.tick()
        pos = e.get_spring_position(0)
        assert abs(pos[0] - 10.0) < 0.1
