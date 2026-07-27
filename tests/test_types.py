"""Tests for core data types."""
import pytest
from src.smart_avatar.core.types import (
    Vec2, Vec3, Vertex, Triangle, MeshRegion, Mesh,
    Bone, Skeleton, SpringConfig, PhysicsBone, Physics,
    BlendShapeTarget, BlendShapes,
    BodyPartType, BodyRegion, AnalysisResult,
    AvatarData, BodyPartNode,
)
from src.smart_avatar.tracking.tracking_interface import TrackingData


class TestVec2:
    def test_defaults(self):
        v = Vec2()
        assert v.x == 0.0
        assert v.y == 0.0

    def test_values(self):
        v = Vec2(1.5, 2.5)
        assert v.x == 1.5
        assert v.y == 2.5

    def test_frozen(self):
        v = Vec2(1.0, 2.0)
        with pytest.raises(AttributeError):
            v.x = 3.0

    def test_equality(self):
        assert Vec2(1.0, 2.0) == Vec2(1.0, 2.0)
        assert Vec2(1.0, 2.0) != Vec2(3.0, 4.0)


class TestVec3:
    def test_defaults(self):
        v = Vec3()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_values(self):
        v = Vec3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_frozen(self):
        v = Vec3(1.0, 2.0, 3.0)
        with pytest.raises(AttributeError):
            v.z = 5.0


class TestVertex:
    def test_defaults(self):
        v = Vertex()
        assert v.position == Vec3()
        assert v.uv == Vec2()
        assert v.weight == 1.0

    def test_custom(self):
        v = Vertex(position=Vec3(1.0, 2.0, 3.0), uv=Vec2(0.5, 0.5), weight=0.8)
        assert v.position.x == 1.0
        assert v.uv.x == 0.5
        assert v.weight == 0.8


class TestTriangle:
    def test_creation(self):
        t = Triangle(0, 1, 2)
        assert t.v0 == 0
        assert t.v1 == 1
        assert t.v2 == 2

    def test_frozen(self):
        t = Triangle(0, 1, 2)
        with pytest.raises(AttributeError):
            t.v0 = 5


class TestMesh:
    def test_empty(self):
        m = Mesh()
        assert m.regions == {}
        assert m.texture_size == (512, 512)

    def test_with_regions(self):
        region = MeshRegion(
            name="head",
            vertices=[Vertex(position=Vec3(10, 10, 0))],
            triangles=[Triangle(0, 1, 2)],
            density=2,
        )
        m = Mesh(regions={"head": region}, texture_size=(1024, 1024))
        assert "head" in m.regions
        assert len(m.regions["head"].vertices) == 1
        assert m.texture_size == (1024, 1024)


class TestBone:
    def test_defaults(self):
        b = Bone(name="Root")
        assert b.name == "Root"
        assert b.parent is None
        assert b.children == []

    def test_with_parent(self):
        b = Bone(name="Head", parent="Neck", position=Vec3(0, 1, 0))
        assert b.parent == "Neck"
        assert b.position.y == 1


class TestSkeleton:
    def test_empty(self):
        s = Skeleton()
        assert s.root == "Hips"
        assert s.bones == []


class TestSpringConfig:
    def test_defaults(self):
        c = SpringConfig()
        assert c.stiffness == 0.5
        assert c.damping == 0.1
        assert c.mass == 1.0
        assert c.gravity == 0.0


class TestPhysics:
    def test_empty(self):
        p = Physics()
        assert p.springs == []
        assert p.breathing_config.stiffness == 0.5


class TestBodyPartType:
    def test_all_values(self):
        parts = list(BodyPartType)
        assert len(parts) == 23
        assert BodyPartType.HEAD.value == "head"
        assert BodyPartType.HAIR.value == "hair"
        assert BodyPartType.ACCESSORY.value == "accessory"


class TestBodyRegion:
    def test_defaults(self):
        r = BodyRegion(type=BodyPartType.HEAD)
        assert r.type == BodyPartType.HEAD
        assert r.bbox == (0, 0, 0, 0)
        assert r.confidence == 0.0

    def test_custom(self):
        r = BodyRegion(
            type=BodyPartType.LEFT_EYE,
            bbox=(100, 200, 50, 30),
            confidence=0.95,
        )
        assert r.bbox == (100, 200, 50, 30)
        assert r.confidence == 0.95


class TestAnalysisResult:
    def test_defaults(self):
        a = AnalysisResult()
        assert a.regions == []
        assert a.image_size == (0, 0)
        assert a.character_type == "unknown"

    def test_with_data(self):
        a = AnalysisResult(
            regions=[BodyRegion(type=BodyPartType.HEAD)],
            image_size=(800, 600),
            character_type="anime",
        )
        assert len(a.regions) == 1
        assert a.image_size == (800, 600)


class TestAvatarData:
    def test_defaults(self):
        d = AvatarData()
        assert d.mesh is not None
        assert d.skeleton is not None
        assert d.blendshapes is not None
        assert d.physics is not None
        assert d.metadata == {}
        assert d.texture_path == ""


class TestTrackingData:
    def test_defaults(self):
        t = TrackingData()
        assert t.head_yaw == 0.0
        assert t.head_pitch == 0.0
        assert t.head_roll == 0.0
        assert t.mouth_open == 0.0
        assert t.left_blink == 0.0
        assert t.right_blink == 0.0
        assert t.smile == 0.0
        assert t.timestamp > 0  # auto-set by time.monotonic

    def test_custom(self):
        t = TrackingData(
            head_yaw=10.0,
            head_pitch=5.0,
            mouth_open=0.8,
            left_blink=1.0,
            smile=0.5,
            brow_left_up=0.3,
            brow_right_up=0.4,
        )
        assert t.head_yaw == 10.0
        assert t.mouth_open == 0.8
        assert t.left_blink == 1.0
        assert t.smile == 0.5


class TestBlendShapeTarget:
    def test_creation(self):
        target = BlendShapeTarget(
            name="Blink_L",
            vertex_deltas=[(0, Vec3(0, -0.1, 0)), (1, Vec3(0, 0.1, 0))],
        )
        assert target.name == "Blink_L"
        assert len(target.vertex_deltas) == 2


class TestBlendShapes:
    def test_empty(self):
        bs = BlendShapes()
        assert bs.targets == {}


class TestBodyPartNode:
    def test_creation(self):
        node = BodyPartNode(name="head", dependencies=["neck"])
        assert node.name == "head"
        assert node.dependencies == ["neck"]
