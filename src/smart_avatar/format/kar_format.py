"""Karin Avatar Format --- .kar ZIP-based avatar file reader/writer."""
import io, json, os, zipfile
from dataclasses import dataclass, field, asdict
from typing import Optional
from PIL import Image

import numpy as np


class AvatarJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles dataclasses and numpy types."""

    def default(self, obj):
        if hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)


@dataclass
class MeshData:
    vertices: list = field(default_factory=list)
    triangles: list = field(default_factory=list)
    uvs: list = field(default_factory=list)
    regions: list = field(default_factory=list)


@dataclass
class SkeletonData:
    bones: list = field(default_factory=list)
    hierarchy: dict = field(default_factory=dict)


@dataclass
class BlendShapeData:
    targets: list = field(default_factory=list)
    vertex_deltas: dict = field(default_factory=dict)


@dataclass
class PhysicsData:
    springs: list = field(default_factory=list)
    breathing: dict = field(default_factory=lambda: {"enabled": True, "intensity": 0.5})


@dataclass
class Metadata:
    name: str = "Avatar"
    version: str = "1.0"
    author: str = "Karin VTuber"
    creation_date: str = ""
    character_type: str = "humanoid"


@dataclass
class AvatarData:
    texture: Optional[Image.Image] = None
    texture_bytes: Optional[bytes] = None
    mesh: MeshData = field(default_factory=MeshData)
    skeleton: SkeletonData = field(default_factory=SkeletonData)
    blendshapes: BlendShapeData = field(default_factory=BlendShapeData)
    physics: PhysicsData = field(default_factory=PhysicsData)
    metadata: Metadata = field(default_factory=Metadata)
    preview: Optional[Image.Image] = None


class KarinAvatarFormat:
    """Reads and writes .kar avatar files (ZIP containers)."""

    @staticmethod
    def save(avatar_data: AvatarData, path: str):
        """Save avatar data to a .kar file."""
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            if avatar_data.texture:
                buf = io.BytesIO()
                avatar_data.texture.save(buf, format="PNG")
                zf.writestr("texture.png", buf.getvalue())

            zf.writestr("mesh.json", json.dumps({
                "vertices": avatar_data.mesh.vertices,
                "triangles": avatar_data.mesh.triangles,
                "uvs": avatar_data.mesh.uvs,
                "regions": avatar_data.mesh.regions,
            }, cls=AvatarJSONEncoder, ensure_ascii=False, indent=2))

            zf.writestr("skeleton.json", json.dumps({
                "bones": avatar_data.skeleton.bones,
                "hierarchy": avatar_data.skeleton.hierarchy,
            }, cls=AvatarJSONEncoder, ensure_ascii=False, indent=2))

            zf.writestr("blendshapes.json", json.dumps({
                "targets": avatar_data.blendshapes.targets,
                "vertex_deltas": avatar_data.blendshapes.vertex_deltas,
            }, cls=AvatarJSONEncoder, ensure_ascii=False, indent=2))

            zf.writestr("physics.json", json.dumps({
                "springs": avatar_data.physics.springs,
                "breathing": avatar_data.physics.breathing,
            }, cls=AvatarJSONEncoder, ensure_ascii=False, indent=2))

            zf.writestr("metadata.json", json.dumps(
                asdict(avatar_data.metadata), ensure_ascii=False, indent=2
            ))

            if avatar_data.preview:
                buf = io.BytesIO()
                avatar_data.preview.save(buf, format="PNG")
                zf.writestr("preview.png", buf.getvalue())

    @staticmethod
    def load(path: str) -> AvatarData:
        """Load avatar data from a .kar file."""
        data = AvatarData()
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()

            if "texture.png" in names:
                raw = zf.read("texture.png")
                data.texture_bytes = raw
                data.texture = Image.open(io.BytesIO(raw))

            if "mesh.json" in names:
                m = json.loads(zf.read("mesh.json"))
                data.mesh = MeshData(
                    vertices=m.get("vertices", []),
                    triangles=m.get("triangles", []),
                    uvs=m.get("uvs", []),
                    regions=m.get("regions", []),
                )

            if "skeleton.json" in names:
                s = json.loads(zf.read("skeleton.json"))
                data.skeleton = SkeletonData(
                    bones=s.get("bones", []),
                    hierarchy=s.get("hierarchy", {}),
                )

            if "blendshapes.json" in names:
                b = json.loads(zf.read("blendshapes.json"))
                data.blendshapes = BlendShapeData(
                    targets=b.get("targets", []),
                    vertex_deltas=b.get("vertex_deltas", {}),
                )

            if "physics.json" in names:
                p = json.loads(zf.read("physics.json"))
                data.physics = PhysicsData(
                    springs=p.get("springs", []),
                    breathing=p.get("breathing", {"enabled": True, "intensity": 0.5}),
                )

            if "metadata.json" in names:
                m = json.loads(zf.read("metadata.json"))
                data.metadata = Metadata(**m)

            if "preview.png" in names:
                data.preview = Image.open(io.BytesIO(zf.read("preview.png")))

        return data

    @staticmethod
    def export_preview(avatar_data: AvatarData, path: str, size: int = 256):
        """Generate and save a preview thumbnail."""
        img = avatar_data.texture
        if img is None:
            raise ValueError("Avatar has no texture to create preview from")
        preview = img.copy()
        preview.thumbnail((size, size), Image.LANCZOS)
        preview.save(path, format="PNG")
        avatar_data.preview = preview
