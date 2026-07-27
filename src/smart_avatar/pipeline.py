"""AvatarPipeline --- main entry point for avatar creation orchestration."""
import logging
import os
import time
from datetime import datetime

log = logging.getLogger(__name__)

from src.smart_avatar.format.kar_format import (
    AvatarData, AvatarJSONEncoder, MeshData, SkeletonData,
    BlendShapeData, PhysicsData, Metadata, KarinAvatarFormat,
)


class AnalysisResult:
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.width = 0
        self.height = 0
        self.has_alpha = False
        self.mode = "RGBA"


class AvatarPipeline:
    """Orchestrates the full avatar creation pipeline."""

    @staticmethod
    def _power_of_two(n):
        return 1 << (n - 1).bit_length()

    def create_avatar(self, image_path: str, output_path: str, progress_callback=None) -> AvatarData:
        """Run the full pipeline: analyze, mesh, skeleton, blendshapes, physics, package."""
        def progress(step, percent):
            if progress_callback:
                progress_callback(step, percent)

        try:
            progress("Analyzing image", 5)
            analysis = self._step_analyze(image_path)
        except Exception as e:
            raise RuntimeError(f"Step 1 (analyze) failed: {e}") from e

        try:
            progress("Generating mesh", 20)
            mesh = self._step_generate_mesh(analysis)
        except Exception as e:
            raise RuntimeError(f"Step 2 (mesh) failed: {e}") from e

        try:
            progress("Generating skeleton", 35)
            skeleton = self._step_generate_skeleton(analysis)
        except Exception as e:
            raise RuntimeError(f"Step 3 (skeleton) failed: {e}") from e

        try:
            progress("Generating blendshapes", 50)
            blendshapes = self._step_generate_blendshapes(analysis)
        except Exception as e:
            raise RuntimeError(f"Step 4 (blendshapes) failed: {e}") from e

        try:
            progress("Generating physics config", 65)
            physics = self._step_generate_physics(analysis)
        except Exception as e:
            raise RuntimeError(f"Step 5 (physics) failed: {e}") from e

        try:
            progress("Packaging avatar data", 80)
            avatar_data = self._step_package(analysis, mesh, skeleton, blendshapes, physics)
        except Exception as e:
            raise RuntimeError(f"Step 6 (package) failed: {e}") from e

        try:
            progress("Exporting .kar file", 90)
            KarinAvatarFormat.save(avatar_data, output_path)
        except Exception as e:
            raise RuntimeError(f"Step 7 (export) failed: {e}") from e

        try:
            progress("Generating preview", 98)
            preview_path = output_path.replace(".kar", "_preview.png")
            KarinAvatarFormat.export_preview(avatar_data, preview_path, size=256)
        except Exception as e:
            log.warning("Preview generation failed: %s", e)

        if progress_callback:
            progress_callback("Done", 100)

        return avatar_data

    def _step_analyze(self, image_path: str) -> AnalysisResult:
        from PIL import Image
        img = Image.open(image_path)
        result = AnalysisResult(image_path)
        result.width, result.height = img.size
        result.mode = img.mode
        result.has_alpha = img.mode in ("RGBA", "LA", "PA")
        return result

    def _step_generate_mesh(self, analysis: AnalysisResult) -> MeshData:
        w = AvatarPipeline._power_of_two(analysis.width)
        h = AvatarPipeline._power_of_two(analysis.height)
        vertices = [
            [-w / 2, -h / 2, 0],
            [w / 2, -h / 2, 0],
            [w / 2, h / 2, 0],
            [-w / 2, h / 2, 0],
        ]
        triangles = [[0, 1, 2], [0, 2, 3]]
        uvs = [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]
        regions = [{"name": "body", "indices": [0, 1, 2, 3]}]
        return MeshData(vertices=vertices, triangles=triangles, uvs=uvs, regions=regions)

    def _step_generate_skeleton(self, analysis: AnalysisResult) -> SkeletonData:
        bones = [
            {"name": "root", "position": [0, 0, 0]},
            {"name": "head", "position": [0, analysis.height * 0.3, 0]},
            {"name": "body", "position": [0, 0, 0]},
        ]
        hierarchy = {"root": ["head", "body"], "head": [], "body": []}
        return SkeletonData(bones=bones, hierarchy=hierarchy)

    def _step_generate_blendshapes(self, analysis: AnalysisResult) -> BlendShapeData:
        targets = [
            {"name": "blink_left", "weight": 0},
            {"name": "blink_right", "weight": 0},
            {"name": "smile", "weight": 0},
            {"name": "open_mouth", "weight": 0},
        ]
        vertex_deltas = {}
        return BlendShapeData(targets=targets, vertex_deltas=vertex_deltas)

    def _step_generate_physics(self, analysis: AnalysisResult) -> PhysicsData:
        springs = [
            {"type": "hair", "enabled": True, "stiffness": 0.5, "damping": 0.5},
            {"type": "clothes", "enabled": True, "stiffness": 0.4, "damping": 0.4},
            {"type": "accessory", "enabled": True},
        ]
        breathing = {"enabled": True, "intensity": 0.5}
        return PhysicsData(springs=springs, breathing=breathing)

    def _step_package(self, analysis: AnalysisResult, mesh: MeshData,
                      skeleton: SkeletonData, blendshapes: BlendShapeData,
                      physics: PhysicsData) -> AvatarData:
        from PIL import Image
        name = os.path.splitext(os.path.basename(analysis.image_path))[0]
        metadata = Metadata(
            name=name,
            version="1.0",
            author="Karin VTuber",
            creation_date=datetime.now().isoformat(),
            character_type="humanoid",
        )
        img = Image.open(analysis.image_path)
        data = AvatarData(
            texture=img,
            mesh=mesh,
            skeleton=skeleton,
            blendshapes=blendshapes,
            physics=physics,
            metadata=metadata,
        )
        return data

    def load_avatar(self, path: str) -> AvatarData:
        """Load an existing .kar file."""
        return KarinAvatarFormat.load(path)
