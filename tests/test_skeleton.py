"""Tests for skeleton generator."""
import pytest
from src.smart_avatar.skeleton.skeleton_generator import (
    SkeletonGenerator, _HIERARCHY, _BONE_TO_BODY_PART,
)
from src.smart_avatar.core.types import (
    AnalysisResult, BodyPartType, BodyRegion, Mesh, Vec3,
)


def _make_analysis_with_head():
    return AnalysisResult(
        regions=[
            BodyRegion(type=BodyPartType.HEAD, bbox=(300, 50, 200, 200)),
            BodyRegion(type=BodyPartType.NECK, bbox=(350, 250, 100, 50)),
            BodyRegion(type=BodyPartType.CHEST, bbox=(200, 300, 400, 200)),
            BodyRegion(type=BodyPartType.MOUTH, bbox=(350, 180, 100, 40)),
            BodyRegion(type=BodyPartType.LEFT_EYE, bbox=(320, 120, 40, 30)),
            BodyRegion(type=BodyPartType.RIGHT_EYE, bbox=(420, 120, 40, 30)),
        ],
        image_size=(800, 600),
    )


def _make_empty_analysis():
    return AnalysisResult(regions=[], image_size=(800, 600))


class TestHierarchy:
    def test_root_has_no_parent(self):
        assert _HIERARCHY[0] == ("Root", None)

    def test_all_parents_exist(self):
        bone_names = {name for name, _ in _HIERARCHY}
        for name, parent in _HIERARCHY:
            if parent is not None:
                assert parent in bone_names, f"Parent '{parent}' of '{name}' not found"

    def test_unique_names(self):
        names = [name for name, _ in _HIERARCHY]
        assert len(names) == len(set(names))


class TestSkeletonGenerator:
    def test_generate_empty(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_empty_analysis())
        assert skeleton.root == "Root"
        assert len(skeleton.bones) > 0  # Always generates fallback hierarchy

    def test_generate_with_detection(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_analysis_with_head())
        assert skeleton.root == "Root"
        bone_names = {b.name for b in skeleton.bones}
        assert "Root" in bone_names
        assert "Head" in bone_names
        assert "Neck" in bone_names

    def test_hierarchy_parent_child(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_analysis_with_head())
        bone_map = {b.name: b for b in skeleton.bones}
        # Head's parent should be Neck
        assert bone_map["Head"].parent == "Neck"
        # Neck's parent should be Chest
        assert bone_map["Neck"].parent == "Chest"

    def test_bone_count(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_analysis_with_head())
        assert len(skeleton.bones) == len(_HIERARCHY)

    def test_root_position(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_empty_analysis())
        root = next(b for b in skeleton.bones if b.name == "Root")
        assert root.position == Vec3(0.0, 0.0, 0.0)

    def test_children_lists(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_analysis_with_head())
        bone_map = {b.name: b for b in skeleton.bones}
        # Chest should have children
        chest = bone_map["Chest"]
        assert "Neck" in chest.children
        assert "LeftShoulder" in chest.children

    def test_detected_bones_near_region_centers(self):
        gen = SkeletonGenerator()
        skeleton = gen.generate(Mesh(), _make_analysis_with_head())
        bone_map = {b.name: b for b in skeleton.bones}
        # Head bone should be near the detected head region center
        head_bone = bone_map["Head"]
        # Head region center: (300+100, 50+100) = (400, 150) normalized by 800
        # So head bone position should be non-zero
        assert head_bone.position.x != 0.0 or head_bone.position.y != 0.0
