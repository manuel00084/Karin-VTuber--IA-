"""Tests for mesh generator."""
import pytest
from src.smart_avatar.mesh.mesh_generator import (
    AutoMeshGenerator, Density, _target_triangles,
)
from src.smart_avatar.core.types import (
    AnalysisResult, BodyPartType, BodyRegion, Vec2,
)


def _make_analysis(region_type, bbox, img_size=(800, 600)):
    return AnalysisResult(
        regions=[BodyRegion(type=region_type, bbox=bbox)],
        image_size=img_size,
    )


class TestTargetTriangles:
    def test_high_density(self):
        count = _target_triangles(Density.HIGH, 10000)
        assert 300 <= count <= 600

    def test_medium_density(self):
        count = _target_triangles(Density.MEDIUM, 10000)
        assert 100 <= count <= 300

    def test_low_density(self):
        count = _target_triangles(Density.LOW, 10000)
        assert 40 <= count <= 150

    def test_variable_density(self):
        count = _target_triangles(Density.VARIABLE, 10000)
        assert 30 <= count <= 400

    def test_small_area(self):
        count = _target_triangles(Density.LOW, 100)
        assert count >= 40  # minimum


class TestAutoMeshGenerator:
    def test_empty_analysis(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(image_size=(0, 0))
        mesh = gen.generate(analysis)
        assert mesh.regions == {}

    def test_no_regions(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(regions=[], image_size=(800, 600))
        mesh = gen.generate(analysis)
        assert mesh.regions == {}

    def test_single_region(self):
        gen = AutoMeshGenerator()
        analysis = _make_analysis(BodyPartType.HEAD, (100, 50, 200, 200))
        mesh = gen.generate(analysis)
        assert "head" in mesh.regions
        assert len(mesh.regions["head"].vertices) > 0
        assert len(mesh.regions["head"].triangles) > 0

    def test_uv_in_range(self):
        gen = AutoMeshGenerator()
        analysis = _make_analysis(BodyPartType.MOUTH, (300, 250, 100, 60))
        mesh = gen.generate(analysis)
        for v in mesh.regions["mouth"].vertices:
            assert 0.0 <= v.uv.x <= 1.0
            assert 0.0 <= v.uv.y <= 1.0

    def test_triangle_indices_valid(self):
        gen = AutoMeshGenerator()
        analysis = _make_analysis(BodyPartType.CHEST, (100, 100, 300, 200))
        mesh = gen.generate(analysis)
        region = mesh.regions["chest"]
        n_verts = len(region.vertices)
        for tri in region.triangles:
            assert 0 <= tri.v0 < n_verts
            assert 0 <= tri.v1 < n_verts
            assert 0 <= tri.v2 < n_verts

    def test_accessory_skipped(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(
            regions=[BodyRegion(type=BodyPartType.ACCESSORY, bbox=(0, 0, 100, 100))],
            image_size=(800, 600),
        )
        mesh = gen.generate(analysis)
        assert "accessory" not in mesh.regions

    def test_zero_bbox_skipped(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(
            regions=[BodyRegion(type=BodyPartType.HEAD, bbox=(0, 0, 0, 0))],
            image_size=(800, 600),
        )
        mesh = gen.generate(analysis)
        assert "head" not in mesh.regions

    def test_multiple_regions(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(
            regions=[
                BodyRegion(type=BodyPartType.HEAD, bbox=(100, 50, 200, 200)),
                BodyRegion(type=BodyPartType.TORSO, bbox=(50, 250, 300, 300)),
            ],
            image_size=(800, 600),
        )
        mesh = gen.generate(analysis)
        assert "head" in mesh.regions
        assert "torso" in mesh.regions
        assert len(mesh.regions) == 2

    def test_texture_size(self):
        gen = AutoMeshGenerator()
        analysis = AnalysisResult(image_size=(1920, 1080))
        mesh = gen.generate(analysis)
        assert mesh.texture_size == (1920, 1080)

    def test_snap_to_landmarks(self):
        verts, tris, offset = AutoMeshGenerator()._triangulate_region(
            bbox=(100, 100, 200, 200),
            target_triangles=10,
            vertex_offset=0,
            img_w=800,
            img_h=600,
            landmarks=[Vec2(200.0, 200.0)],
        )
        assert len(verts) > 0
        # At least one vertex should be near the landmark
        near_landmark = any(
            abs(v.position.x - 200) < 50 and abs(v.position.y - 200) < 50
            for v in verts
        )
        assert near_landmark

    def test_density_map_entries(self):
        # All non-ACCESSORY BodyPartType values should be in the density map
        for bt in BodyPartType:
            if bt != BodyPartType.ACCESSORY:
                from src.smart_avatar.mesh.mesh_generator import _DENSITY_MAP
                assert bt in _DENSITY_MAP
