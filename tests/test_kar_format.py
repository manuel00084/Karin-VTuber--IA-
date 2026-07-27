"""Tests for .kar avatar file format."""
import io
import json
import os
import tempfile
import pytest
from PIL import Image

from src.smart_avatar.format.kar_format import (
    KarinAvatarFormat, AvatarData, MeshData, SkeletonData,
    BlendShapeData, PhysicsData, Metadata, AvatarJSONEncoder,
)


def _make_test_avatar():
    """Create a minimal AvatarData for testing."""
    img = Image.new("RGBA", (64, 64), (255, 0, 0, 255))
    return AvatarData(
        texture=img,
        mesh=MeshData(
            vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0]],
            triangles=[[0, 1, 2]],
            uvs=[[0, 0], [1, 0], [1, 1]],
            regions=[{"name": "body", "indices": [0, 1, 2]}],
        ),
        skeleton=SkeletonData(
            bones=[{"name": "root", "position": [0, 0, 0]}],
            hierarchy={"root": []},
        ),
        blendshapes=BlendShapeData(
            targets=[{"name": "blink_left", "weight": 0}],
            vertex_deltas={"blink_left": {"0": [0, -0.1, 0]}},
        ),
        physics=PhysicsData(
            springs=[{"type": "hair", "stiffness": 0.5}],
            breathing={"enabled": True, "intensity": 0.5},
        ),
        metadata=Metadata(
            name="TestAvatar",
            version="1.0",
            author="Test",
            creation_date="2026-01-01",
            character_type="humanoid",
        ),
    )


class TestAvatarJSONEncoder:
    def test_dataclass(self):
        data = {"mesh": MeshData(vertices=[[0, 0, 0]])}
        result = json.dumps(data, cls=AvatarJSONEncoder)
        assert "vertices" in result

    def test_bytes(self):
        data = {"data": b"hello"}
        result = json.dumps(data, cls=AvatarJSONEncoder)
        assert "hello" in result

    def test_fallback(self):
        with pytest.raises(TypeError):
            json.dumps({"obj": object()}, cls=AvatarJSONEncoder)


class TestMeshData:
    def test_defaults(self):
        m = MeshData()
        assert m.vertices == []
        assert m.triangles == []
        assert m.uvs == []
        assert m.regions == []


class TestSkeletonData:
    def test_defaults(self):
        s = SkeletonData()
        assert s.bones == []
        assert s.hierarchy == {}


class TestBlendShapeData:
    def test_defaults(self):
        b = BlendShapeData()
        assert b.targets == []
        assert b.vertex_deltas == {}


class TestPhysicsData:
    def test_defaults(self):
        p = PhysicsData()
        assert p.springs == []
        assert p.breathing == {"enabled": True, "intensity": 0.5}


class TestMetadata:
    def test_defaults(self):
        m = Metadata()
        assert m.name == "Avatar"
        assert m.version == "1.0"
        assert m.author == "Karin VTuber"


class TestKarinAvatarFormat:
    def test_save_and_load(self):
        avatar = _make_test_avatar()
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            path = f.name
        try:
            KarinAvatarFormat.save(avatar, path)
            assert os.path.exists(path)
            loaded = KarinAvatarFormat.load(path)
            assert loaded.mesh.vertices == avatar.mesh.vertices
            assert loaded.mesh.triangles == avatar.mesh.triangles
            assert loaded.skeleton.bones == avatar.skeleton.bones
            assert loaded.metadata.name == "TestAvatar"
        finally:
            os.unlink(path)

    def test_save_texture(self):
        avatar = _make_test_avatar()
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            path = f.name
        try:
            KarinAvatarFormat.save(avatar, path)
            loaded = KarinAvatarFormat.load(path)
            assert loaded.texture is not None
            assert loaded.texture.size == (64, 64)
        finally:
            os.unlink(path)

    def test_save_preview(self):
        avatar = _make_test_avatar()
        preview_img = Image.new("RGBA", (128, 128), (0, 255, 0, 255))
        avatar.preview = preview_img
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            path = f.name
        try:
            KarinAvatarFormat.save(avatar, path)
            loaded = KarinAvatarFormat.load(path)
            assert loaded.preview is not None
        finally:
            os.unlink(path)

    def test_load_missing_file(self):
        with pytest.raises(FileNotFoundError):
            KarinAvatarFormat.load("nonexistent.kar")

    def test_export_preview(self):
        avatar = _make_test_avatar()
        preview_path = os.path.join(os.path.dirname(__file__), "_test_preview.png")
        try:
            KarinAvatarFormat.export_preview(avatar, preview_path, size=128)
            assert os.path.exists(preview_path)
            img = Image.open(preview_path)
            w, h = img.size
            img.close()
            assert w <= 128
            assert h <= 128
        finally:
            try:
                os.unlink(preview_path)
            except OSError:
                pass

    def test_export_preview_no_texture(self):
        avatar = AvatarData()
        with pytest.raises(ValueError):
            KarinAvatarFormat.export_preview(avatar, "test.png")

    def test_zip_contents(self):
        avatar = _make_test_avatar()
        avatar.preview = Image.new("RGBA", (64, 64), (0, 0, 255, 255))
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            path = f.name
        try:
            KarinAvatarFormat.save(avatar, path)
            import zipfile
            with zipfile.ZipFile(path, "r") as zf:
                names = set(zf.namelist())
                assert "texture.png" in names
                assert "mesh.json" in names
                assert "skeleton.json" in names
                assert "blendshapes.json" in names
                assert "physics.json" in names
                assert "metadata.json" in names
                assert "preview.png" in names
        finally:
            os.unlink(path)
