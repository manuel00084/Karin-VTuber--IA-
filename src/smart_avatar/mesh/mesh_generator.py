"""AutoMeshGenerator – genera meshes deformables a partir de AnalysisResult."""

from __future__ import annotations

import enum
import logging
import math
from typing import Sequence

import numpy as np

from src.smart_avatar.core.interfaces import IMeshGenerator
from src.smart_avatar.core.types import (
    AnalysisResult,
    BodyPartType,
    BodyRegion,
    Mesh,
    MeshRegion,
    Triangle,
    Vec2,
    Vec3,
    Vertex,
)

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Density levels
# ---------------------------------------------------------------------------

class Density(enum.IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    VARIABLE = -1


_DENSITY_MAP: dict[BodyPartType, Density] = {
    # Face details – high density
    BodyPartType.HEAD: Density.HIGH,
    BodyPartType.LEFT_EYE: Density.HIGH,
    BodyPartType.RIGHT_EYE: Density.HIGH,
    BodyPartType.LEFT_EYEBROW: Density.HIGH,
    BodyPartType.RIGHT_EYEBROW: Density.HIGH,
    BodyPartType.NOSE: Density.HIGH,
    BodyPartType.MOUTH: Density.HIGH,
    # Hair – high density (fine strands)
    BodyPartType.HAIR: Density.HIGH,
    # Neck – low
    BodyPartType.NECK: Density.LOW,
    # Torso / chest – medium
    BodyPartType.CHEST: Density.MEDIUM,
    BodyPartType.TORSO: Density.MEDIUM,
    BodyPartType.HIPS: Density.MEDIUM,
    # Shoulders – medium
    BodyPartType.LEFT_SHOULDER: Density.MEDIUM,
    BodyPartType.RIGHT_SHOULDER: Density.MEDIUM,
    # Arms / legs – low
    BodyPartType.LEFT_ARM: Density.LOW,
    BodyPartType.RIGHT_ARM: Density.LOW,
    BodyPartType.LEFT_LEG: Density.LOW,
    BodyPartType.RIGHT_LEG: Density.LOW,
    # Hands / feet – low
    BodyPartType.LEFT_HAND: Density.LOW,
    BodyPartType.RIGHT_HAND: Density.LOW,
    BodyPartType.LEFT_FOOT: Density.LOW,
    BodyPartType.RIGHT_FOOT: Density.LOW,
    # Accessories – variable
    BodyPartType.ACCESSORY: Density.VARIABLE,
}


def _target_triangles(density: Density, area: int) -> int:
    """Número objetivo de triángulos según densidad y área en píxeles²."""
    if density == Density.HIGH:
        return max(300, min(600, area // 80))
    if density == Density.MEDIUM:
        return max(100, min(300, area // 200))
    if density == Density.LOW:
        return max(40, min(150, area // 500))
    # VARIABLE: escalar con raíz del área
    return max(30, min(400, int(math.sqrt(area) * 0.8)))


# ---------------------------------------------------------------------------
# AutoMeshGenerator
# ---------------------------------------------------------------------------

class AutoMeshGenerator(IMeshGenerator):
    """Genera una malla 3D deformable a partir de un `AnalysisResult`.

    Cada `BodyRegion` se convierte en un `MeshRegion` con Delaunay
    triangulation adaptativa. Los vértices llevan UV mapeados a la textura.
    """

    def generate(self, analysis: AnalysisResult) -> Mesh:
        img_w, img_h = analysis.image_size
        if img_w == 0 or img_h == 0:
            log.warning("AnalysisResult sin dimensiones válidas – generando malla vacía")
            return Mesh()

        mesh = Mesh(texture_size=(img_w, img_h))
        vertex_offset = 0

        for region in analysis.regions:
            if region.type == BodyPartType.ACCESSORY:
                continue
            if region.bbox[2] == 0 or region.bbox[3] == 0:
                continue

            density = _DENSITY_MAP.get(region.type, Density.MEDIUM)
            area = region.bbox[2] * region.bbox[3]
            target_tris = _target_triangles(density, area)

            verts, tris, new_offset = self._triangulate_region(
                region.bbox,
                target_tris,
                vertex_offset,
                img_w,
                img_h,
                region.landmarks,
            )
            vertex_offset = new_offset

            mr = MeshRegion(
                name=region.type.value,
                vertices=verts,
                triangles=tris,
                density=int(density) if density >= 0 else 0,
            )
            mesh.regions[region.type.value] = mr

            log.debug(
                "Región %s: %d vértices, %d triángulos (densidad %s)",
                region.type.value, len(verts), len(tris), density.name,
            )

        total_v = sum(len(mr.vertices) for mr in mesh.regions.values())
        total_t = sum(len(mr.triangles) for mr in mesh.regions.values())
        log.info(
            "Malla generada: %d regiones, %d vértices, %d triángulos",
            len(mesh.regions), total_v, total_t,
        )
        return mesh

    # ------------------------------------------------------------------
    # Triangulación de una región rectangular
    # ------------------------------------------------------------------

    def _triangulate_region(
        self,
        bbox: tuple[int, int, int, int],
        target_triangles: int,
        vertex_offset: int,
        img_w: int,
        img_h: int,
        landmarks: list[Vec2] | None = None,
    ) -> tuple[list[Vertex], list[Triangle], int]:
        """Genera vértices y triángulos Delaunay para un bbox.

        Returns:
            (vertices, triangles, next_vertex_offset)
        """
        x0, y0, w, h = bbox
        if w <= 0 or h <= 0:
            return [], [], vertex_offset

        # Calcular resolución de grilla basada en el número deseado de triángulos
        # Cada celda rectangular genera 2 triángulos → n_cells ≈ target/2
        n_cells = max(1, target_triangles // 2)
        aspect = w / max(h, 1)
        cols = max(2, int(round(math.sqrt(n_cells * aspect))))
        rows = max(2, int(round(n_cells / cols)))

        step_x = w / cols
        step_y = h / rows

        # 1. Generar vértices en grilla con perturbación basada en landmarks
        grid_positions: list[tuple[float, float]] = []
        vertices: list[Vertex] = []

        for row in range(rows + 1):
            for col in range(cols + 1):
                # Posición base de grilla
                px = x0 + col * step_x
                py = y0 + row * step_y

                # Perturbación: si hay landmarks cercanos, deslizar vértice hacia el más cercano
                if landmarks:
                    px, py = self._snap_to_landmarks(px, py, landmarks, step_x * 0.4)

                # Clamp a la imagen
                px = max(0.0, min(float(img_w), px))
                py = max(0.0, min(float(img_h), py))

                # UV = posición normalizada en la textura
                uv = Vec2(px / img_w, py / img_h)
                # Z=0 para malla 2D (se puede extruir después)
                pos = Vec3(px, py, 0.0)

                vertices.append(Vertex(position=pos, uv=uv, weight=1.0))
                grid_positions.append((px, py))

        # 2. Triangular la grilla (dos triángulos por celda)
        triangles: list[Triangle] = []
        for row in range(rows):
            for col in range(cols):
                i00 = vertex_offset + row * (cols + 1) + col
                i10 = i00 + 1
                i01 = i00 + (cols + 1)
                i11 = i01 + 1

                triangles.append(Triangle(v0=i00, v1=i10, v2=i01))
                triangles.append(Triangle(v0=i10, v1=i11, v2=i01))

        # 3. Subdividir si sobran triángulos (refinamiento adaptativo)
        if len(triangles) < target_triangles:
            vertices, triangles = self._subdivide_mesh(
                vertices, triangles, grid_positions, cols, rows,
                x0, y0, w, h, img_w, img_h,
                target_triangles, vertex_offset,
                landmarks,
            )

        return vertices, triangles, vertex_offset + len(vertices)

    # ------------------------------------------------------------------
    # Snapping a landmarks
    # ------------------------------------------------------------------

    @staticmethod
    def _snap_to_landmarks(
        px: float, py: float,
        landmarks: list[Vec2],
        radius: float,
    ) -> tuple[float, float]:
        """Desliza un punto hacia el landmark más cercano si está dentro del radio."""
        best_dist = radius
        best_x, best_y = px, py
        for lm in landmarks:
            dx = lm.x - px
            dy = lm.y - py
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < best_dist:
                best_dist = dist
                best_x = lm.x
                best_y = lm.y
        if best_dist < radius:
            # Interpolar suavemente
            t = 0.5
            return px + (best_x - px) * t, py + (best_y - py) * t
        return px, py

    # ------------------------------------------------------------------
    # Subdivisión de malla
    # ------------------------------------------------------------------

    def _subdivide_mesh(
        self,
        vertices: list[Vertex],
        triangles: list[Triangle],
        grid_positions: list[tuple[float, float]],
        cols: int,
        rows: int,
        x0: int, y0: int,
        w: int, h: int,
        img_w: int, img_h: int,
        target_triangles: int,
        vertex_offset: int,
        landmarks: list[Vec2] | None = None,
    ) -> tuple[list[Vertex], list[Triangle]]:
        """Subdivide la malla insertando vértices en los puntos medios de los triángulos
        más grandes hasta alcanzar el objetivo de densidad."""
        max_iterations = 50
        iteration = 0

        while len(triangles) < target_triangles and iteration < max_iterations:
            iteration += 1
            new_triangles: list[Triangle] = []

            for tri in triangles:
                if len(triangles) + len(new_triangles) >= target_triangles:
                    new_triangles.append(tri)
                    continue

                # Punto medio del triángulo más grande
                v0 = vertices[tri.v0 - vertex_offset] if (tri.v0 - vertex_offset) < len(vertices) else None
                v1 = vertices[tri.v1 - vertex_offset] if (tri.v1 - vertex_offset) < len(vertices) else None
                v2 = vertices[tri.v2 - vertex_offset] if (tri.v2 - vertex_offset) < len(vertices) else None

                if v0 is None or v1 is None or v2 is None:
                    new_triangles.append(tri)
                    continue

                # Punto medio del lado más largo
                d01 = self._edge_length(v0, v1)
                d12 = self._edge_length(v1, v2)
                d20 = self._edge_length(v2, v0)

                max_d = max(d01, d12, d20)
                if max_d < 3.0:
                    new_triangles.append(tri)
                    continue

                if max_d == d01:
                    mid = self._midpoint_vertex(v0, v1, img_w, img_h, landmarks)
                elif max_d == d12:
                    mid = self._midpoint_vertex(v1, v2, img_w, img_h, landmarks)
                else:
                    mid = self._midpoint_vertex(v2, v0, img_w, img_h, landmarks)

                mid_idx = vertex_offset + len(vertices)
                vertices.append(mid)

                # Reemplazar un triángulo por dos
                if max_d == d01:
                    new_triangles.append(Triangle(v0=tri.v0, v1=mid_idx, v2=tri.v2))
                    new_triangles.append(Triangle(v0=mid_idx, v1=tri.v1, v2=tri.v2))
                elif max_d == d12:
                    new_triangles.append(Triangle(v0=tri.v1, v1=mid_idx, v2=tri.v0))
                    new_triangles.append(Triangle(v0=mid_idx, v1=tri.v2, v2=tri.v0))
                else:
                    new_triangles.append(Triangle(v0=tri.v2, v1=mid_idx, v2=tri.v1))
                    new_triangles.append(Triangle(v0=mid_idx, v1=tri.v0, v2=tri.v1))

            triangles = new_triangles

        return vertices, triangles

    @staticmethod
    def _edge_length(a: Vertex, b: Vertex) -> float:
        dx = a.position.x - b.position.x
        dy = a.position.y - b.position.y
        return math.sqrt(dx * dx + dy * dy)

    def _midpoint_vertex(
        self,
        a: Vertex,
        b: Vertex,
        img_w: int,
        img_h: int,
        landmarks: list[Vec2] | None = None,
    ) -> Vertex:
        mx = (a.position.x + b.position.x) / 2.0
        my = (a.position.y + b.position.y) / 2.0

        if landmarks:
            mx, my = self._snap_to_landmarks(mx, my, landmarks, 5.0)

        return Vertex(
            position=Vec3(mx, my, 0.0),
            uv=Vec2(mx / img_w, my / img_h),
            weight=1.0,
        )
