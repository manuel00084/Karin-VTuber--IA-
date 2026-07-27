"""Tests for AvatarPipeline end-to-end."""
import os
import tempfile
import pytest
from PIL import Image

from src.smart_avatar.pipeline import AvatarPipeline, AnalysisResult


def _create_test_image(path, size=(256, 256), mode="RGBA"):
    """Create a test image file."""
    img = Image.new(mode, size, (255, 128, 0, 255))
    img.save(path)
    return path


class TestAvatarPipeline:
    def test_power_of_two(self):
        assert AvatarPipeline._power_of_two(100) == 128
        assert AvatarPipeline._power_of_two(256) == 256
        assert AvatarPipeline._power_of_two(257) == 512
        assert AvatarPipeline._power_of_two(1) == 1

    def test_step_analyze(self):
        pipeline = AvatarPipeline()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = f.name
        try:
            _create_test_image(path)
            analysis = pipeline._step_analyze(path)
            assert analysis.width == 256
            assert analysis.height == 256
            assert analysis.has_alpha is True
            assert analysis.mode == "RGBA"
        finally:
            os.unlink(path)

    def test_step_generate_mesh(self):
        pipeline = AvatarPipeline()
        analysis = AnalysisResult(image_path="test.png")
        analysis.width = 256
        analysis.height = 256
        mesh = pipeline._step_generate_mesh(analysis)
        assert len(mesh.vertices) == 4
        assert len(mesh.triangles) == 2
        assert len(mesh.uvs) == 4

    def test_step_generate_skeleton(self):
        pipeline = AvatarPipeline()
        analysis = AnalysisResult(image_path="test.png")
        analysis.width = 256
        analysis.height = 256
        skeleton = pipeline._step_generate_skeleton(analysis)
        assert len(skeleton.bones) == 3
        assert skeleton.bones[0]["name"] == "root"

    def test_step_generate_blendshapes(self):
        pipeline = AvatarPipeline()
        analysis = AnalysisResult(image_path="test.png")
        blendshapes = pipeline._step_generate_blendshapes(analysis)
        assert len(blendshapes.targets) == 4
        names = [t["name"] for t in blendshapes.targets]
        assert "blink_left" in names
        assert "smile" in names

    def test_step_generate_physics(self):
        pipeline = AvatarPipeline()
        analysis = AnalysisResult(image_path="test.png")
        physics = pipeline._step_generate_physics(analysis)
        assert len(physics.springs) == 3
        assert physics.breathing["enabled"] is True

    def test_full_pipeline(self):
        pipeline = AvatarPipeline()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            out_path = f.name
        try:
            _create_test_image(img_path)
            progress_log = []
            avatar = pipeline.create_avatar(
                img_path, out_path,
                progress_callback=lambda step, pct: progress_log.append((step, pct)),
            )
            assert avatar is not None
            assert avatar.texture is not None
            assert os.path.exists(out_path)
            assert len(progress_log) > 0
            assert progress_log[-1] == ("Done", 100)
        finally:
            os.unlink(img_path)
            if os.path.exists(out_path):
                os.unlink(out_path)
            preview = out_path.replace(".kar", "_preview.png")
            if os.path.exists(preview):
                os.unlink(preview)

    def test_load_avatar(self):
        pipeline = AvatarPipeline()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img_path = f.name
        with tempfile.NamedTemporaryFile(suffix=".kar", delete=False) as f:
            out_path = f.name
        try:
            _create_test_image(img_path)
            pipeline.create_avatar(img_path, out_path)
            loaded = pipeline.load_avatar(out_path)
            assert loaded.texture is not None
            assert loaded.metadata.name != ""
        finally:
            os.unlink(img_path)
            if os.path.exists(out_path):
                os.unlink(out_path)

    def test_analyze_nonexistent(self):
        pipeline = AvatarPipeline()
        with pytest.raises(Exception):
            pipeline._step_analyze("nonexistent.png")
