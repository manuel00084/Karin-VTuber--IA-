"""Tests for BodyRelationshipGraph."""
import pytest
from src.smart_avatar.core.body_graph import BodyRelationshipGraph, create_default_graph
from src.smart_avatar.core.types import Vec3


class TestBodyRelationshipGraph:
    def test_empty_graph(self):
        g = BodyRelationshipGraph()
        assert g.get_dependents("head") == []

    def test_add_part_no_deps(self):
        g = BodyRelationshipGraph()
        g.add_part("head")
        assert g.get_dependents("head") == []

    def test_add_part_with_deps(self):
        g = BodyRelationshipGraph()
        g.add_part("head", ["neck"])
        assert "head" in g.get_dependents("neck")

    def test_multiple_dependents(self):
        g = BodyRelationshipGraph()
        g.add_part("chest", ["torso"])
        g.add_part("neck", ["chest"])
        g.add_part("left_shoulder", ["chest"])
        dependents = g.get_dependents("chest")
        assert "neck" in dependents
        assert "left_shoulder" in dependents

    def test_get_all_dependents_bfs(self):
        g = BodyRelationshipGraph()
        g.add_part("torso", [])
        g.add_part("chest", ["torso"])
        g.add_part("neck", ["chest"])
        g.add_part("head", ["neck"])
        g.add_part("hair", ["head"])

        all_deps = g.get_all_dependents("torso")
        assert "chest" in all_deps
        assert "neck" in all_deps
        assert "head" in all_deps
        assert "hair" in all_deps

    def test_get_all_dependents_no_self_loop(self):
        g = BodyRelationshipGraph()
        g.add_part("a", ["b"])
        g.add_part("b", ["a"])
        deps = g.get_all_dependents("a")
        assert "a" not in deps

    def test_transmit_motion_basic(self):
        g = BodyRelationshipGraph()
        g.add_part("head", [])
        g.add_part("hair", ["head"])
        delta = Vec3(10.0, 0.0, 0.0)
        result = g.transmit_motion("head", delta)
        assert "hair" in result
        assert result["hair"].x > 0
        assert result["hair"].x < 10.0  # attenuated

    def test_transmit_motion_custom_factor(self):
        g = BodyRelationshipGraph()
        g.add_part("head", [])
        g.add_part("hair", ["head"])
        delta = Vec3(10.0, 0.0, 0.0)
        result = g.transmit_motion("head", delta, factors={"hair": 0.5})
        assert result["hair"].x == pytest.approx(5.0)

    def test_transmit_motion_chain(self):
        g = BodyRelationshipGraph()
        g.add_part("torso", [])
        g.add_part("chest", ["torso"])
        g.add_part("neck", ["chest"])
        g.add_part("head", ["neck"])
        delta = Vec3(5.0, 0.0, 0.0)
        result = g.transmit_motion("torso", delta)
        # Each level should be attenuated
        assert result["chest"].x > result["neck"].x
        assert result["neck"].x > result["head"].x

    def test_transmit_motion_nonexistent_source(self):
        g = BodyRelationshipGraph()
        result = g.transmit_motion("ghost", Vec3(1, 1, 1))
        assert result == {}

    def test_transmit_motion_no_deps(self):
        g = BodyRelationshipGraph()
        g.add_part("alone")
        result = g.transmit_motion("alone", Vec3(1, 1, 1))
        assert result == {}


class TestCreateDefaultGraph:
    def test_all_parts_present(self):
        g = create_default_graph()
        expected_parts = [
            "torso", "chest", "neck", "head",
            "left_shoulder", "right_shoulder",
            "left_arm", "right_arm",
            "left_hand", "right_hand",
            "hips", "left_leg", "right_leg",
            "left_foot", "right_foot",
            "left_eye", "right_eye",
            "left_eyebrow", "right_eyebrow",
            "nose", "mouth", "hair", "accessory",
        ]
        for part in expected_parts:
            deps = g.get_all_dependents(part)
            assert isinstance(deps, list)

    def test_head_chain(self):
        g = create_default_graph()
        all_deps = g.get_all_dependents("head")
        assert "hair" in all_deps
        assert "left_eye" in all_deps
        assert "right_eye" in all_deps
        assert "mouth" in all_deps

    def test_torso_cascades(self):
        g = create_default_graph()
        all_deps = g.get_all_dependents("torso")
        assert "chest" in all_deps
        assert "head" in all_deps
        assert "hair" in all_deps
