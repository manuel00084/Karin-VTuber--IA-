"""Tests for blendshape generator."""
import pytest
from src.smart_avatar.blendshapes.blendshape_generator import (
    BlendShapeGenerator,
    _EYE_SHAPES, _MOUTH_SHAPES, _BROW_SHAPES, _EMOTION_SHAPES, _ALL_SHAPES,
)
from src.smart_avatar.core.types import (
    Mesh, MeshRegion, Skeleton, Bone, Vec2, Vec3, Vertex,
)


def _make_mesh_with_regions():
    """Create a Mesh with regions that blendshape generator expects."""
    head_verts = [
        Vertex(position=Vec3(100, 100, 0)),
        Vertex(position=Vec3(200, 100, 0)),
        Vertex(position=Vec3(200, 200, 0)),
        Vertex(position=Vec3(100, 200, 0)),
    ]
    eye_verts = [
        Vertex(position=Vec3(120, 130, 0)),
        Vertex(position=Vec3(160, 130, 0)),
        Vertex(position=Vec3(160, 150, 0)),
        Vertex(position=Vec3(120, 150, 0)),
    ]
    mouth_verts = [
        Vertex(position=Vec3(140, 180, 0)),
        Vertex(position=Vec3(170, 180, 0)),
        Vertex(position=Vec3(170, 195, 0)),
        Vertex(position=Vec3(140, 195, 0)),
    ]
    brow_verts = [
        Vertex(position=Vec3(120, 110, 0)),
        Vertex(position=Vec3(160, 110, 0)),
    ]

    return Mesh(
        regions={
            "head": MeshRegion(name="head", vertices=head_verts),
            "left_eye": MeshRegion(name="left_eye", vertices=eye_verts),
            "right_eye": MeshRegion(name="right_eye", vertices=eye_verts),
            "left_eyebrow": MeshRegion(name="left_eyebrow", vertices=brow_verts),
            "right_eyebrow": MeshRegion(name="right_eyebrow", vertices=brow_verts),
            "mouth": MeshRegion(name="mouth", vertices=mouth_verts),
        },
        texture_size=(800, 600),
    )


def _make_skeleton():
    return Skeleton(
        root="Root",
        bones=[Bone(name="Root"), Bone(name="Head", parent="Root")],
    )


class TestBlendShapeConstants:
    def test_eye_shapes_count(self):
        assert len(_EYE_SHAPES) == 10

    def test_mouth_shapes_count(self):
        assert len(_MOUTH_SHAPES) == 7

    def test_brow_shapes_count(self):
        assert len(_BROW_SHAPES) == 4

    def test_emotion_shapes_count(self):
        assert len(_EMOTION_SHAPES) == 4

    def test_all_shapes_total(self):
        assert len(_ALL_SHAPES) == 25

    def test_no_duplicates(self):
        assert len(_ALL_SHAPES) == len(set(_ALL_SHAPES))


class TestBlendShapeGenerator:
    def test_generate_with_mesh(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        assert len(bs.targets) > 0

    def test_all_expected_shapes_present(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        for shape_name in _ALL_SHAPES:
            assert shape_name in bs.targets, f"Missing shape: {shape_name}"

    def test_blink_shapes(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        assert "Blink_L" in bs.targets
        assert "Blink_R" in bs.targets
        assert len(bs.targets["Blink_L"].vertex_deltas) > 0

    def test_mouth_shapes(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        for name in ["MouthA", "MouthE", "MouthI", "MouthO", "MouthU"]:
            assert name in bs.targets

    def test_jaw_shapes(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        assert "JawOpen" in bs.targets
        assert "JawClose" in bs.targets

    def test_brow_shapes(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        for name in ["BrowUp_L", "BrowUp_R", "BrowDown_L", "BrowDown_R"]:
            assert name in bs.targets

    def test_emotion_shapes(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        for name in ["Smile", "Sad", "Angry", "Surprise"]:
            assert name in bs.targets

    def test_delta_values_are_vec3(self):
        gen = BlendShapeGenerator()
        mesh = _make_mesh_with_regions()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        for target in bs.targets.values():
            for idx, delta in target.vertex_deltas:
                assert isinstance(delta, Vec3)

    def test_generate_empty_mesh(self):
        gen = BlendShapeGenerator()
        mesh = Mesh()
        skeleton = _make_skeleton()
        bs = gen.generate(mesh, skeleton)
        # Should still produce shapes (just with empty vertex lists)
        assert len(bs.targets) > 0

    def test_region_offsets(self):
        mesh = _make_mesh_with_regions()
        offsets = BlendShapeGenerator._compute_region_offsets(mesh)
        assert "head" in offsets
        assert offsets["head"] == 0
        assert offsets["left_eye"] == 4  # head has 4 vertices

    def test_global_scale(self):
        mesh = _make_mesh_with_regions()
        scale = BlendShapeGenerator._global_scale(mesh)
        assert scale > 0
