"""Controlador principal del avatar — orquesta todos los subsistemas runtime.

Conecta esqueleto, malla, blendshapes, física, spring engine y body graph
en un solo ciclo de actualización por frame.
"""

from __future__ import annotations

import logging
import math
import time
from typing import Any

import numpy as np

from src.smart_avatar.core.body_graph import BodyRelationshipGraph, create_default_graph
from src.smart_avatar.core.types import (
    AvatarData,
    BlendShapes,
    Bone,
    Mesh,
    Physics,
    PhysicsBone,
    Skeleton,
    SpringConfig,
    Vec3,
)
from src.smart_avatar.tracking.tracking_interface import TrackingData
from src.smart_avatar.runtime.renderer import (
    AvatarRenderer,
    _euler_to_mat4,
    _mat4_identity,
    _mat4_translate,
)

log = logging.getLogger(__name__)

# ======================================================================
# Spring state (simple damped harmonic oscillator)
# ======================================================================

class _SpringState:
    """Estado interno de un resorte para física de pelo/accesorios."""

    __slots__ = ("position", "velocity", "rest_position")

    def __init__(self, rest: Vec3) -> None:
        self.rest_position = np.array([rest.x, rest.y, rest.z], dtype=np.float32)
        self.position = self.rest_position.copy()
        self.velocity = np.zeros(3, dtype=np.float32)


# ======================================================================
# AvatarController
# ======================================================================

class AvatarController:
    """Orquestador principal que conecta tracking → esqueleto → malla → render.

    Cada frame se llama a :meth:`update` con los datos de tracking y el delta
    de tiempo. El controller propaga las rotaciones de tracking al esqueleto,
    actualiza la física de springs, aplica blendshapes y mantiene el buffer
    de vértices deformados listo para el renderer.
    """

    def __init__(
        self,
        avatar_data: AvatarData | None = None,
        renderer: AvatarRenderer | None = None,
    ) -> None:
        self._avatar = avatar_data or AvatarData()
        self._renderer = renderer

        # Subsistemas
        self._body_graph: BodyRelationshipGraph = create_default_graph()
        self._spring_states: dict[str, _SpringState] = {}
        self._bone_matrices: dict[str, np.ndarray] = {}
        self._blendshape_weights: dict[str, float] = {}

        # Buffer de vértices deformados
        self._deformed_positions: np.ndarray | None = None
        self._deformed_normals: np.ndarray | None = None
        self._deformed_uvs: np.ndarray | None = None

        # Breathing
        self._breath_time: float = 0.0
        self._breath_amplitude: float = 0.01

        # Time tracking
        self._last_time: float = time.monotonic()

        # Inicializar
        self._init_spring_states()
        self._build_vertex_buffer()

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def _init_spring_states(self) -> None:
        """Crea estados de spring para los huesos de física."""
        for pb in self._avatar.physics.springs:
            self._spring_states[pb.bone_name] = _SpringState(pb.anchor)

    def _build_vertex_buffer(self) -> None:
        """Extrae positions, normals y UVs de la malla como arrays numpy."""
        verts = []
        normals = []
        uvs = []

        for region in self._avatar.mesh.regions.values():
            for v in region.vertices:
                verts.append([v.position.x, v.position.y, v.position.z])
                normals.append([0.0, 0.0, 1.0])  # default normal
                uvs.append([v.uv.x, v.uv.y])

        if not verts:
            verts = [[0, 0, 0]]
            normals = [[0, 0, 1]]
            uvs = [[0, 0]]

        self._deformed_positions = np.array(verts, dtype=np.float32)
        self._deformed_normals = np.array(normals, dtype=np.float32)
        self._deformed_uvs = np.array(uvs, dtype=np.float32)

    # ------------------------------------------------------------------
    # Update — ciclo principal por frame
    # ------------------------------------------------------------------

    def update(self, tracking_data: TrackingData, dt: float) -> None:
        """Actualiza el avatar completo con datos de tracking.

        Pasos:
        1. Aplicar tracking data a huesos root (Head → rotación, etc.)
        2. Propagar movimiento a través del BodyRelationshipGraph
        3. Actualizar springs (pelo, accesorios, ropa)
        4. Actualizar breathing
        5. Aplicar pesos de blendshapes desde tracking
        6. Computar posiciones finales de vértices
        """
        if dt <= 0.0:
            return

        # 1. Tracking → root bones
        self._apply_tracking_to_bones(tracking_data)

        # 2. Propagar a través del body graph
        self._propagate_motion(tracking_data)

        # 3. Springs
        self._update_springs(dt)

        # 4. Breathing
        self._update_breathing(dt)

        # 5. Blendshapes
        self._apply_blendshapes(tracking_data)

        # 6. Deformación final
        self._compute_final_vertices()

        self._last_time = time.monotonic()

    # ------------------------------------------------------------------
    # Tracking → Bones
    # ------------------------------------------------------------------

    def _apply_tracking_to_bones(self, data: TrackingData) -> None:
        """Aplica datos de tracking crudos a los huesos root del esqueleto."""
        # Mapear tracking → huesos del esqueleto
        bone_map: dict[str, Vec3] = {}

        for bone in self._avatar.skeleton.bones:
            if bone.name.lower() in ("head", "head_bone"):
                bone_map[bone.name] = Vec3(
                    x=data.head_pitch,
                    y=data.head_yaw,
                    z=data.head_roll,
                )
            elif bone.name.lower() in ("left_eye", "left_eye_bone"):
                bone_map[bone.name] = Vec3(
                    x=0.0,
                    y=data.left_eye_gaze.x * 30.0,  # ampliar a grados
                    z=data.left_eye_gaze.y * 30.0,
                )
            elif bone.name.lower() in ("right_eye", "right_eye_bone"):
                bone_map[bone.name] = Vec3(
                    x=0.0,
                    y=data.right_eye_gaze.x * 30.0,
                    z=data.right_eye_gaze.y * 30.0,
                )

        # Calcular matrices de huesos desde el tracking
        for bone in self._avatar.skeleton.bones:
            if bone.name in bone_map:
                rot = bone_map[bone.name]
                self._bone_matrices[bone.name] = _euler_to_mat4(rot.y, rot.x, rot.z)
            elif bone.name not in self._bone_matrices:
                # Si no hay tracking, mantener pose base
                base_rot = bone.rotation
                self._bone_matrices[bone.name] = _euler_to_mat4(base_rot.y, base_rot.x, base_rot.z)

    # ------------------------------------------------------------------
    # Body Graph propagation
    # ------------------------------------------------------------------

    def _propagate_motion(self, data: TrackingData) -> None:
        """Usa el BodyRelationshipGraph para propagar movimiento cascada."""
        head_delta = Vec3(x=data.head_pitch, y=data.head_yaw, z=data.head_roll)

        propagated = self._body_graph.transmit_motion(
            source="head",
            delta=head_delta,
            factors={
                "hair": 0.8,
                "accessory": 0.6,
                "neck": 0.5,
                "left_eyebrow": 0.3,
                "right_eyebrow": 0.3,
                "left_eye": 1.0,
                "right_eye": 1.0,
                "mouth": 0.15,
                "nose": 0.1,
            },
        )

        for part_name, delta in propagated.items():
            current = self._bone_matrices.get(part_name, _mat4_identity())
            rotation = _euler_to_mat4(delta.y, delta.x, delta.z)
            self._bone_matrices[part_name] = current @ rotation

    # ------------------------------------------------------------------
    # Spring physics
    # ------------------------------------------------------------------

    def _update_springs(self, dt: float) -> None:
        """Simula física de springs para pelo, accesorios y ropa."""
        for pb in self._avatar.physics.springs:
            state = self._spring_states.get(pb.bone_name)
            if state is None:
                continue

            cfg = pb.spring
            # Fuerza del resorte: F = -k * displacement - damping * velocity
            displacement = state.position - state.rest_position
            spring_force = -cfg.stiffness * displacement
            damping_force = -cfg.damping * state.velocity
            total_force = spring_force + damping_force

            # Integración semi-implicit Euler
            acceleration = total_force / cfg.mass
            state.velocity = state.velocity + acceleration * dt
            state.position = state.position + state.velocity * dt

            # Aplicar al hueso
            self._bone_matrices[pb.bone_name] = _mat4_translate(
                float(state.position[0]),
                float(state.position[1]),
                float(state.position[2]),
            )

    # ------------------------------------------------------------------
    # Breathing
    # ------------------------------------------------------------------

    def _update_breathing(self, dt: float) -> None:
        """Simula respiración con onda sinusoidal."""
        self._breath_time += dt

        cfg = self._avatar.physics.breathing_config
        freq = cfg.mass  # frequency in Hz (stored by physics_generator)
        breath = math.sin(self._breath_time * freq * math.pi * 2.0) * self._breath_amplitude

        # Aplicar a huesos del torso/chest
        for bone in self._avatar.skeleton.bones:
            if bone.name.lower() in ("chest", "torso", "hips"):
                current = self._bone_matrices.get(bone.name, _mat4_identity())
                breath_offset = _mat4_translate(0.0, breath, 0.0)
                self._bone_matrices[bone.name] = current @ breath_offset

    # ------------------------------------------------------------------
    # Blendshapes
    # ------------------------------------------------------------------

    def _apply_blendshapes(self, data: TrackingData) -> None:
        """Mapea datos de tracking a pesos de blendshapes."""
        # Mapeo tracking → blendshape name → weight
        mapping: dict[str, float] = {
            "MouthA": data.mouth_open,
            "MouthI": data.mouth_open * 0.5 if data.mouth_shape == "open" else 0.0,
            "MouthSmile": data.smile,
            "BrowLeftUp": data.brow_left_up,
            "BrowRightUp": data.brow_right_up,
            "EyeLeftBlink": data.left_blink,
            "EyeRightBlink": data.right_blink,
            "EyeLeftGazeX": data.left_eye_gaze.x,
            "EyeLeftGazeY": data.left_eye_gaze.y,
            "EyeRightGazeX": data.right_eye_gaze.x,
            "EyeRightGazeY": data.right_eye_gaze.y,
        }

        for name, weight in mapping.items():
            if name in self._avatar.blendshapes.targets:
                self._blendshape_weights[name] = max(0.0, min(1.0, weight))

    # ------------------------------------------------------------------
    # Vertex deformation
    # ------------------------------------------------------------------

    def _compute_final_vertices(self) -> None:
        """Aplica deformaciones de bones + blendshapes a los vértices."""
        if self._deformed_positions is None:
            return

        # Resetear a posiciones base
        base_positions = self._get_base_positions()
        self._deformed_positions[:] = base_positions

        # Aplicar blendshape deltas
        self._apply_blendshape_deltas()

        # Aplicar bone transforms (skin-weighted approximate)
        self._apply_bone_deformation()

    def _get_base_positions(self) -> np.ndarray:
        """Extrae las posiciones base de la malla."""
        verts = []
        for region in self._avatar.mesh.regions.values():
            for v in region.vertices:
                verts.append([v.position.x, v.position.y, v.position.z])
        if not verts:
            return np.zeros((1, 3), dtype=np.float32)
        return np.array(verts, dtype=np.float32)

    def _apply_blendshape_deltas(self) -> None:
        """Suma los deltas de blendshapes activos a las posiciones."""
        for name, weight in self._blendshape_weights.items():
            if weight <= 0.0:
                continue
            target = self._avatar.blendshapes.targets.get(name)
            if target is None:
                continue
            for idx, delta in target.vertex_deltas:
                if idx < len(self._deformed_positions):
                    self._deformed_positions[idx, 0] += delta.x * weight
                    self._deformed_positions[idx, 1] += delta.y * weight
                    self._deformed_positions[idx, 2] += delta.z * weight

    def _apply_bone_deformation(self) -> None:
        """Aplica transformaciones de huesos a los vértices.

        Simplificación: cada región de la malla se asocia al hueso
        con el mismo nombre. Los vértices de una región se transforman
        con la matriz de ese hueso.
        """
        region_names = list(self._avatar.mesh.regions.keys())
        offset = 0
        for region_name in region_names:
            region = self._avatar.mesh.regions[region_name]
            bone_mat = self._bone_matrices.get(region_name, _mat4_identity())

            for _ in region.vertices:
                if offset < len(self._deformed_positions):
                    pos = np.array([
                        self._deformed_positions[offset, 0],
                        self._deformed_positions[offset, 1],
                        self._deformed_positions[offset, 2],
                        1.0,
                    ], dtype=np.float32)
                    transformed = bone_mat @ pos
                    self._deformed_positions[offset, 0] = transformed[0]
                    self._deformed_positions[offset, 1] = transformed[1]
                    self._deformed_positions[offset, 2] = transformed[2]
                offset += 1

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_deformed_mesh(self) -> np.ndarray | None:
        """Devuelve las posiciones deformadas actuales (N, 3)."""
        return self._deformed_positions

    def get_mesh_data_for_render(self) -> tuple[np.ndarray, np.ndarray] | None:
        """Devuelve (vertices_8ch, indices) listos para el renderer.

        vertices_8ch: (N, 8) → [x, y, z, u, v, nx, ny, nz]
        """
        if self._deformed_positions is None:
            return None

        n = len(self._deformed_positions)
        vertices = np.zeros((n, 8), dtype=np.float32)
        vertices[:, :3] = self._deformed_positions
        if self._deformed_uvs is not None:
            uv_len = min(len(self._deformed_uvs), n)
            vertices[:uv_len, 3:5] = self._deformed_uvs[:uv_len]
        if self._deformed_normals is not None:
            norm_len = min(len(self._deformed_normals), n)
            vertices[:norm_len, 5:8] = self._deformed_normals[:norm_len]

        # Construir índices de triángulos
        indices = []
        offset = 0
        for region in self._avatar.mesh.regions.values():
            for tri in region.triangles:
                indices.extend([tri.v0 + offset, tri.v1 + offset, tri.v2 + offset])
            offset += len(region.vertices)

        return vertices, np.array(indices, dtype=np.uint32) if indices else np.array([], dtype=np.uint32)

    @property
    def avatar_data(self) -> AvatarData:
        return self._avatar

    @avatar_data.setter
    def avatar_data(self, value: AvatarData) -> None:
        self._avatar = value
        self._init_spring_states()
        self._build_vertex_buffer()
        self._bone_matrices.clear()
        self._blendshape_weights.clear()

    @property
    def body_graph(self) -> BodyRelationshipGraph:
        return self._body_graph

    @property
    def blendshape_weights(self) -> dict[str, float]:
        return dict(self._blendshape_weights)

    def set_blendshape_weight(self, name: str, weight: float) -> None:
        """Establece manualmente el peso de un blendshape."""
        self._blendshape_weights[name] = max(0.0, min(1.0, weight))

    def reset(self) -> None:
        """Resetea todos los estados del controller."""
        self._bone_matrices.clear()
        self._blendshape_weights.clear()
        self._breath_time = 0.0
        for state in self._spring_states.values():
            state.position = state.rest_position.copy()
            state.velocity = np.zeros(3, dtype=np.float32)
        self._build_vertex_buffer()
