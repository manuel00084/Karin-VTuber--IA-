"""Test all new modules — HDR buffer, cascade shadows, IBL, spring bone GPU, deferred pipeline.
Run without a VRM model to verify Python modules initialize correctly."""
import logging
import sys
import os
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
_log = logging.getLogger("test_modules")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_imports():
    """Test that all new modules can be imported."""
    _log.info("=== Test: Imports ===")
    modules = [
        "render.hdr_buffer",
        "render.cascade_shadow",
        "render.ibl_loader",
        "render.springbone_gpu",
        "render.deferred",
        "render.shadow_pipeline",
        "render.postprocess",
    ]
    ok = 0
    for mod_name in modules:
        try:
            __import__(mod_name)
            _log.info("  OK: %s", mod_name)
            ok += 1
        except Exception as exc:
            _log.error("  FAIL: %s — %s", mod_name, exc)
    _log.info("Imports: %d/%d passed", ok, len(modules))
    return ok == len(modules)


def test_springbone_gpu():
    """Test spring bone GPU data packing."""
    _log.info("=== Test: SpringBoneGPUManager ===")
    from render.springbone_gpu import SpringBoneGPUManager

    mgr = SpringBoneGPUManager()

    # Add 3 spring bones
    mgr.set_spring_bone(0, stiffness=2.0, drag=0.5, gravity_dir=(0, -1), rest_pos=(0, 0, 1.0))
    mgr.set_spring_bone(1, stiffness=1.5, drag=0.4, gravity_dir=(0, -1), rest_pos=(0, 0, 0.8))
    mgr.set_spring_bone(2, stiffness=3.0, drag=0.6, gravity_dir=(0, -1), rest_pos=(0, 0, 0.6))
    mgr.set_bone_parent(1, 0)
    mgr.set_bone_parent(2, 1)

    # Add colliders
    idx0 = mgr.add_sphere_collider(bone_idx=0, radius=0.05, world_pos=(0, 0, 0.5))
    idx1 = mgr.add_capsule_collider(bone_idx=1, radius=0.03, world_pos=(0, 0, 0.3), world_tail=(0, 0, 0.1))

    assert idx0 == 0, f"Expected collider idx 0, got {idx0}"
    assert idx1 == 1, f"Expected collider idx 1, got {idx1}"
    assert mgr.spring_bone_count == 3, f"Expected 3 bones, got {mgr.spring_bone_count}"
    assert mgr.collider_count == 2, f"Expected 2 colliders, got {mgr.collider_count}"

    # Pack for GPU
    data = mgr.pack_for_gpu()
    assert "spring_bone_data" in data
    assert "collider_data" in data
    assert data["spring_bone_data"].shape == (3, 4)
    assert data["collider_data"].shape == (2, 4)
    assert data["meta"][0] == 3  # bone count
    assert data["meta"][1] == 2  # collider count

    # CPU simulation step
    mgr.step_simulation(1.0 / 60.0)
    _log.info("  Tail[0]: %s", mgr.tail_current[0, :3])
    _log.info("  OK: SpringBoneGPUManager")
    return True


def test_cascade_shadow():
    """Test cascade shadow map split computation."""
    _log.info("=== Test: CascadeShadowMap ===")
    from render.cascade_shadow import CascadeShadowMap

    class FakeApp:
        class pipe:
            pass
        class win:
            @staticmethod
            def getGsg():
                return None
        graphicsEngine = None
        render = None
        camera = None

    # Only test the split computation (no GPU)
    csm = CascadeShadowMap.__new__(CascadeShadowMap)
    csm._num_cascades = 4
    csm._split_lambda = 0.75
    csm._max_distance = 50.0
    csm._split_depths = []
    csm._cascade_sizes = []

    splits = csm.compute_split_depths(near=0.1, far=50.0)
    _log.info("  Splits: [%.2f, %.2f, %.2f, %.2f]", *splits)
    assert len(splits) == 4, f"Expected 4 splits, got {len(splits)}"
    assert splits[0] > 0.1, "First split should be > near"
    assert splits[-1] <= 50.0, "Last split should be <= far"
    for i in range(len(splits) - 1):
        assert splits[i] < splits[i+1], f"Splits not monotonically increasing at {i}"

    # Test GPU data packing
    csm._cascade_view_projs = [np.eye(4, dtype=np.float32) for _ in range(4)]
    gpu_data = csm.get_cascade_data_for_gpu()
    assert gpu_data["cascade_count"] == 4
    assert len(gpu_data["cascades"]) == 4

    _log.info("  OK: CascadeShadowMap")
    return True


def test_brdf_lut():
    """Test BRDF LUT generation."""
    _log.info("=== Test: BRDFLUTGenerator ===")
    from render.ibl_loader import BRDFLUTGenerator, DEFAULT_SH_COEFFS

    class FakeApp:
        pass

    gen = BRDFLUTGenerator(FakeApp(), lut_size=32)  # Small for speed
    lut = gen.generate()
    assert lut is not None, "BRDF LUT generation failed"

    # Check SH coefficients
    assert len(DEFAULT_SH_COEFFS) == 9, f"Expected 9 SH bands, got {len(DEFAULT_SH_COEFFS)}"
    for i, c in enumerate(DEFAULT_SH_COEFFS):
        assert len(c) == 3, f"SH band {i} should have 3 channels"

    _log.info("  OK: BRDFLUTGenerator")
    return True


def test_gbuffer():
    """Test G-Buffer texture creation."""
    _log.info("=== Test: GBuffer ===")
    from render.deferred import GBuffer

    gb = GBuffer(1920, 1080)
    assert gb.width == 1920
    assert gb.height == 1080
    textures = gb.get_textures()
    assert len(textures) == 4, f"Expected 4 textures, got {len(textures)}"

    # Test resize
    gb.resize(1280, 720)
    assert gb.width == 1280
    assert gb.height == 720

    _log.info("  OK: GBuffer")
    return True


def test_shaders_exist():
    """Test that all HLSL shaders exist."""
    _log.info("=== Test: Shader Files ===")
    shader_dir = os.path.join(os.path.dirname(__file__), "render")
    hlsl_files = [
        "pbr_skinned_vs.hlsl", "pbr_skinned_ps.hlsl",
        "deferred_gbuffer_vs.hlsl", "deferred_gbuffer_ps.hlsl",
        "deferred_lighting_ps.hlsl", "deferred_composite_ps.hlsl",
        "shadow_vs.hlsl", "shadow_ps.hlsl", "shadow_sampling.hlsl",
        "cascade_shadow.hlsl",
        "springbone_vs.hlsl", "springbone_collider_vs.hlsl",
        "postprocess_vs.hlsl", "postprocess_ps.hlsl",
        "bloom_extract_ps.hlsl", "gaussian_blur_ps.hlsl",
        "tonemap_composite_ps.hlsl",
        "depth_prepass_vs.hlsl", "depth_prepass_ps.hlsl",
        "fullscreen_vs.hlsl",
        "basic_vs.hlsl", "basic_ps.hlsl",
        "skinned_vs.hlsl", "skinned_ps.hlsl",
    ]
    ok = 0
    for f in hlsl_files:
        path = os.path.join(shader_dir, f)
        if os.path.exists(path):
            ok += 1
        else:
            _log.error("  MISSING: %s", f)
    _log.info("Shaders: %d/%d present", ok, len(hlsl_files))
    return ok == len(hlsl_files)


def main():
    _log.info("=" * 60)
    _log.info("KARIN DX11 — Module Test Suite")
    _log.info("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("SpringBoneGPU", test_springbone_gpu()))
    results.append(("CascadeShadow", test_cascade_shadow()))
    results.append(("BRDF LUT", test_brdf_lut()))
    results.append(("GBuffer", test_gbuffer()))
    results.append(("Shader Files", test_shaders_exist()))

    _log.info("=" * 60)
    _log.info("RESULTS:")
    all_pass = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        _log.info("  %s: %s", name, status)
        if not ok:
            all_pass = False

    _log.info("=" * 60)
    if all_pass:
        _log.info("ALL TESTS PASSED")
    else:
        _log.error("SOME TESTS FAILED")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
