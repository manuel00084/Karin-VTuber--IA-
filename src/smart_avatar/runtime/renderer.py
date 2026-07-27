"""Motor de renderizado PyOpenGL para avatares 2D/3D.

Maneja la creación del contexto OpenGL, carga de texturas,
configuración de shaders, deformación de malla y renderizado
con post-procesado (outline, bloom).
"""

from __future__ import annotations

import ctypes
import logging
import math
import os
from typing import Any

import numpy as np

from OpenGL.GL import (
    GL_ARRAY_BUFFER,
    GL_BLEND,
    GL_CULL_FACE,
    GL_COLOR_BUFFER_BIT,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_ELEMENT_ARRAY_BUFFER,
    GL_FLOAT,
    GL_FALSE,
    GL_FRONT,
    GL_BACK,
    GL_FRAMEBUFFER,
    GL_FRAMEBUFFER_COMPLETE,
    GL_NEAREST,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_RENDERBUFFER,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_STATIC_DRAW,
    GL_TEXTURE_2D,
    GL_TEXTURE0,
    GL_TEXTURE_MIN_FILTER,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_WRAP_S,
    GL_TEXTURE_WRAP_T,
    GL_TRIANGLES,
    GL_UNSIGNED_INT,
    GL_REPEAT,
    GL_UNPACK_ALIGNMENT,
    glBindBuffer,
    glBindFramebuffer,
    glBindTexture,
    glBindVertexArray,
    glBlendFunc,
    glBufferData,
    glCheckFramebufferStatus,
    glClear,
    glClearColor,
    glCullFace,
    glDeleteBuffers,
    glDeleteFramebuffers,
    glDeleteRenderbuffers,
    glDeleteTextures,
    glDeleteVertexArrays,
    glDisable,
    glDisableVertexAttribArray,
    glDrawArrays,
    glDrawElements,
    glActiveTexture,
    glEnable,
    glEnableVertexAttribArray,
    glGenBuffers,
    glGenFramebuffers,
    glGenRenderbuffers,
    glGenTextures,
    glGenVertexArrays,
    glGetError,
    glFramebufferRenderbuffer,
    glFramebufferTexture2D,
    glPixelStorei,
    glRenderbufferStorage,
    glTexImage2D,
    glTexParameteri,
    glVertexAttribPointer,
    glViewport,
)
from OpenGL.GLU import gluPerspective

from src.smart_avatar.core.types import AvatarData, Vec3
from src.smart_avatar.tracking.tracking_interface import TrackingData
from src.smart_avatar.shaders.shader_manager import ShaderManager

log = logging.getLogger(__name__)

# ======================================================================
# Matrix math helpers (numpy only — no glm dependency)
# ======================================================================

def _mat4_identity() -> np.ndarray:
    """Matriz identidad 4×4."""
    return np.eye(4, dtype=np.float32)


def _mat4_translate(x: float, y: float, z: float) -> np.ndarray:
    """Matriz de traslación."""
    m = _mat4_identity()
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m


def _mat4_scale(x: float, y: float, z: float) -> np.ndarray:
    m = _mat4_identity()
    m[0, 0] = x
    m[1, 1] = y
    m[2, 2] = z
    return m


def _mat4_rotate_x(rad: float) -> np.ndarray:
    c, s = math.cos(rad), math.sin(rad)
    m = _mat4_identity()
    m[1, 1] = c;  m[1, 2] = -s
    m[2, 1] = s;  m[2, 2] = c
    return m


def _mat4_rotate_y(rad: float) -> np.ndarray:
    c, s = math.cos(rad), math.sin(rad)
    m = _mat4_identity()
    m[0, 0] = c;  m[0, 2] = s
    m[2, 0] = -s; m[2, 2] = c
    return m


def _mat4_rotate_z(rad: float) -> np.ndarray:
    c, s = math.cos(rad), math.sin(rad)
    m = _mat4_identity()
    m[0, 0] = c;  m[0, 1] = -s
    m[1, 0] = s;  m[1, 1] = c
    return m


def _mat4_perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Construye una matriz de proyección en perspectiva."""
    fov_rad = math.radians(fov_deg)
    f = 1.0 / math.tan(fov_rad / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m


def _mat4_look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray) -> np.ndarray:
    """Construye una matriz de vista (look-at)."""
    f = target - eye
    f = f / np.linalg.norm(f)
    u = up / np.linalg.norm(up)
    s = np.cross(f, u)
    s = s / np.linalg.norm(s)
    u = np.cross(s, f)

    m = _mat4_identity()
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -np.dot(s, eye)
    m[1, 3] = -np.dot(u, eye)
    m[2, 3] = np.dot(f, eye)
    return m


def _euler_to_mat4(yaw_deg: float, pitch_deg: float, roll_deg: float) -> np.ndarray:
    """Convierte ángulos Euler (grados) a matriz 4×4 de rotación."""
    y = math.radians(yaw_deg)
    p = math.radians(pitch_deg)
    r = math.radians(roll_deg)
    return _mat4_rotate_y(y) @ _mat4_rotate_x(p) @ _mat4_rotate_z(r)


# ======================================================================
# Texture loading
# ======================================================================

def _load_texture(path: str) -> int:
    """Carga una imagen PNG/JPG como textura OpenGL. Devuelve el texture id."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow es necesario para cargar texturas: pip install Pillow")

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Textura no encontrada: {path}")

    img = Image.open(path).convert("RGBA")
    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    width, height = img.size
    data = img.tobytes()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
    glTexImage2D(
        GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, 0x1401, data
    )
    log.info("Textura cargada: %s (%dx%d) → GL %d", path, width, height, tex_id)
    return tex_id


# ======================================================================
# Mesh buffers
# ======================================================================

class _MeshBuffers:
    """Contiene los IDs de VAO/VBO/EBO de una malla."""

    __slots__ = ("vao", "vbo", "ebo", "index_count")

    def __init__(self) -> None:
        self.vao: int = 0
        self.vbo: int = 0
        self.ebo: int = 0
        self.index_count: int = 0


# ======================================================================
# AvatarRenderer
# ======================================================================

class AvatarRenderer:
    """Motor de renderizado OpenGL para el avatar.

    Responsabilidades:
    - Crear y gestionar el contexto OpenGL (ventana GLUT).
    - Compilar y enlazar shaders.
    - Cargar texturas y crear buffers de malla (VBOs/VAOs).
    - Ejecutar el pipeline de renderizado por frame.
    """

    def __init__(self, width: int = 800, height: int = 600, title: str = "Karin Avatar") -> None:
        self._width = width
        self._height = height
        self._title = title

        self._shader_mgr = ShaderManager()
        self._texture_id: int = 0
        self._mesh_buffers: _MeshBuffers | None = None
        self._initialized: bool = False

        # Camera defaults
        self._cam_pos = np.array([0.0, 0.0, 3.0], dtype=np.float32)
        self._cam_target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self._cam_up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        self._fov = 45.0
        self._near = 0.1
        self._far = 100.0

        # Light
        self._light_dir = np.array([0.5, 1.0, 0.8], dtype=np.float32)

        # FBO for post-processing
        self._fbo: int = 0
        self._fbo_texture: int = 0
        self._rbo: int = 0

        # Cached fullscreen quad for blit (created once)
        self._quad_vao: int = 0
        self._quad_vbo: int = 0
        self._quad_ebo: int = 0

    # ------------------------------------------------------------------
    # Inicialización
    # ------------------------------------------------------------------

    def init(self) -> None:
        """Inicializa el contexto OpenGL, shaders y buffers base."""
        if self._initialized:
            return

        self._init_glut()
        self._shader_mgr.init_all_builtins()
        self._setup_framebuffer()
        self._setup_quad()
        self._initialized = True
        log.info("AvatarRenderer inicializado (%dx%d)", self._width, self._height)

    def _init_glut(self) -> None:
        """Inicializa GLUT y crea la ventana."""
        from OpenGL.GLUT import (
            glutCreateWindow,
            glutDisplayFunc,
            glutInit,
            glutInitDisplayMode,
            glutInitWindowSize,
            glutMainLoopEvent,
            glutReshapeFunc,
            glutSwapBuffers,
        )
        import sys

        argv = sys.argv
        glutInit(argv)
        glutInitDisplayMode(0x0002 | 0x0010)  # GLUT_DOUBLE | GLUT_RGBA
        glutInitWindowSize(self._width, self._height)
        glutCreateWindow(self._title.encode("utf-8"))
        glutReshapeFunc(self._on_resize)
        glutDisplayFunc(lambda: None)

    def _on_resize(self, width: int, height: int) -> None:
        """Callback de reshape de la ventana. Mantiene aspect ratio."""
        if height == 0:
            height = 1
        self._width = width
        self._height = height
        glViewport(0, 0, width, height)
        self._rebuild_framebuffer()
        log.debug("Ventana redimensionada: %dx%d", width, height)

    # ------------------------------------------------------------------
    # Framebuffer para post-procesado
    # ------------------------------------------------------------------

    def _setup_framebuffer(self) -> None:
        """Crea el FBO y textura auxiliar para post-procesado."""
        self._fbo = glGenFramebuffers(1)
        self._fbo_texture = glGenTextures(1)
        self._rbo = glGenRenderbuffers(1)
        self._rebuild_framebuffer()

    def _rebuild_framebuffer(self) -> None:
        """Reconstruye FBO con las dimensiones actuales."""
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glBindTexture(GL_TEXTURE_2D, self._fbo_texture)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA, self._width, self._height,
            0, GL_RGBA, 0x1401, None,
        )
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glFramebufferTexture2D(GL_FRAMEBUFFER, 0x8CE0, GL_TEXTURE_2D, self._fbo_texture, 0)

        glBindRenderbuffer(GL_RENDERBUFFER, self._rbo)
        glRenderbufferStorage(GL_RENDERBUFFER, 0x8105, self._width, self._height)
        glFramebufferRenderbuffer(GL_FRAMEBUFFER, 0x8D00, GL_RENDERBUFFER, self._rbo)

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        if status != GL_FRAMEBUFFER_COMPLETE:
            log.warning("FBO incompleto: %s", status)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _setup_quad(self) -> None:
        """Crea el VAO/VBO/EBO del quad fullscreen (una sola vez)."""
        self._quad_vao = glGenVertexArrays(1)
        glBindVertexArray(self._quad_vao)

        quad = np.array([
            -1, -1, 0,    0, 0,    0, 0, 1,
             1, -1, 0,    1, 0,    0, 0, 1,
             1,  1, 0,    1, 1,    0, 0, 1,
            -1,  1, 0,    0, 1,    0, 0, 1,
        ], dtype=np.float32)
        quad_indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)

        self._quad_vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self._quad_vbo)
        glBufferData(GL_ARRAY_BUFFER, quad.nbytes, quad, GL_STATIC_DRAW)

        self._quad_ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self._quad_ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, quad_indices.nbytes, quad_indices, GL_STATIC_DRAW)

        stride = 8 * 4
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))

        glBindVertexArray(0)

    # ------------------------------------------------------------------
    # Carga de recursos
    # ------------------------------------------------------------------

    def load_texture(self, path: str) -> None:
        """Carga una textura para el avatar."""
        if self._texture_id:
            glDeleteTextures([self._texture_id])
        self._texture_id = _load_texture(path)

    def upload_mesh(self, vertices: np.ndarray, indices: np.ndarray) -> None:
        """Sube vértices e índices a VBOs.

        Args:
            vertices: Array (N, 8) con [x, y, z, u, v, nx, ny, nz].
            indices: Array (M,) con índices de triángulos.
        """
        if self._mesh_buffers is not None:
            self._free_mesh_buffers()

        bufs = _MeshBuffers()
        bufs.index_count = len(indices)

        bufs.vao = glGenVertexArrays(1)
        glBindVertexArray(bufs.vao)

        bufs.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, bufs.vbo)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices.astype(np.float32), GL_STATIC_DRAW)

        bufs.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, bufs.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices.astype(np.uint32), GL_STATIC_DRAW)

        stride = 8 * 4  # 8 floats × 4 bytes
        # Position (location 0)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # UV (location 1)
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        # Normal (location 2)
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(20))

        glBindVertexArray(0)
        self._mesh_buffers = bufs
        log.info("Malla subida: %d vértices, %d índices", len(vertices), len(indices))

    def _free_mesh_buffers(self) -> None:
        if self._mesh_buffers is None:
            return
        glDeleteVertexArrays(1, [self._mesh_buffers.vao])
        glDeleteBuffers(2, [self._mesh_buffers.vbo, self._mesh_buffers.ebo])
        self._mesh_buffers = None

    # ------------------------------------------------------------------
    # Render loop
    # ------------------------------------------------------------------

    def render(
        self,
        avatar_data: AvatarData,
        tracking_data: TrackingData,
        dt: float,
    ) -> None:
        """Bucle principal de renderizado.

        Pipeline:
        1. Limpiar pantalla
        2. Computar matrices de cámara
        3. Bindar textura y shader
        4. Aplicar transforms de tracking a los huesos
        5. Dibujar malla deformada
        6. Post-procesado (outline)
        7. Swap buffers
        """
        if not self._initialized:
            return

        from OpenGL.GLUT import glutMainLoopEvent, glutSwapBuffers
        glutMainLoopEvent()

        # 1. Limpiar
        glBindFramebuffer(GL_FRAMEBUFFER, self._fbo)
        glViewport(0, 0, self._width, self._height)
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if self._mesh_buffers is None or self._texture_id == 0:
            glutSwapBuffers()
            return

        # 2. Matrices de cámara
        aspect = self._width / self._height if self._height > 0 else 1.0
        proj = _mat4_perspective(self._fov, aspect, self._near, self._far)
        view = _mat4_look_at(self._cam_pos, self._cam_target, self._cam_up)

        # 3. Modelo — aplicar tracking a esqueleto
        model = _euler_to_mat4(
            tracking_data.head_yaw,
            tracking_data.head_pitch,
            tracking_data.head_roll,
        )

        # 4. Draw main mesh
        self._shader_mgr.use_shader("default")
        self._shader_mgr.set_uniform("default", "u_model", model)
        self._shader_mgr.set_uniform("default", "u_view", view)
        self._shader_mgr.set_uniform("default", "u_projection", proj)
        self._shader_mgr.set_uniform("default", "u_texture", 0)
        self._shader_mgr.set_uniform("default", "u_light_dir", self._light_dir.tolist())
        self._shader_mgr.set_uniform("default", "u_alpha", 1.0)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self._texture_id)

        glBindVertexArray(self._mesh_buffers.vao)
        glDrawElements(GL_TRIANGLES, self._mesh_buffers.index_count, GL_UNSIGNED_INT, None)

        # 5. Post-procesado: outline pass
        self._render_outline(view, proj, model)

        # 6. Blit FBO → pantalla y swap
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, self._width, self._height)
        self._blit_fbo_to_screen()
        glutSwapBuffers()

    def _render_outline(
        self, view: np.ndarray, proj: np.ndarray, model: np.ndarray
    ) -> None:
        """Renderiza el outline (shell method) en el FBO actual."""
        try:
            self._shader_mgr.use_shader("outline")
            self._shader_mgr.set_uniform("outline", "u_model", model)
            self._shader_mgr.set_uniform("outline", "u_view", view)
            self._shader_mgr.set_uniform("outline", "u_projection", proj)
            self._shader_mgr.set_uniform("outline", "u_outline_width", 0.02)
            self._shader_mgr.set_uniform("outline", "u_outline_color", (0.0, 0.0, 0.0))

            glEnable(GL_CULL_FACE)
            glCullFace(GL_FRONT)
            glBindVertexArray(self._mesh_buffers.vao)
            glDrawElements(GL_TRIANGLES, self._mesh_buffers.index_count, GL_UNSIGNED_INT, None)
            glCullFace(GL_BACK)
            glDisable(GL_CULL_FACE)
        except Exception:
            log.debug("Outline pass omitido (shader no disponible)")

    def _blit_fbo_to_screen(self) -> None:
        """Copia la textura del FBO a la pantalla (post-proceso simple)."""
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, self._fbo_texture)

        self._shader_mgr.use_shader("default")

        glBindVertexArray(self._quad_vao)

        identity = _mat4_identity()
        self._shader_mgr.set_uniform("default", "u_model", identity)
        self._shader_mgr.set_uniform("default", "u_view", identity)
        self._shader_mgr.set_uniform("default", "u_projection", identity)
        self._shader_mgr.set_uniform("default", "u_alpha", 1.0)

        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Libera todos los recursos GPU."""
        if not self._initialized:
            return

        self._free_mesh_buffers()

        if self._texture_id:
            glDeleteTextures([self._texture_id])
            self._texture_id = 0

        if self._quad_vao:
            glDeleteVertexArrays(1, [self._quad_vao])
            self._quad_vao = 0
        if self._quad_vbo:
            glDeleteBuffers(1, [self._quad_vbo])
            self._quad_vbo = 0
        if self._quad_ebo:
            glDeleteBuffers(1, [self._quad_ebo])
            self._quad_ebo = 0

        if self._fbo:
            glDeleteFramebuffers([self._fbo])
            self._fbo = 0
        if self._fbo_texture:
            glDeleteTextures([self._fbo_texture])
            self._fbo_texture = 0
        if self._rbo:
            glDeleteRenderbuffers([self._rbo])
            self._rbo = 0

        self._shader_mgr.cleanup()
        self._initialized = False
        log.info("AvatarRenderer limpiado")

    # ------------------------------------------------------------------
    # Propiedades de cámara
    # ------------------------------------------------------------------

    def set_camera(
        self,
        position: tuple[float, float, float] | None = None,
        target: tuple[float, float, float] | None = None,
        fov: float | None = None,
    ) -> None:
        if position is not None:
            self._cam_pos = np.array(position, dtype=np.float32)
        if target is not None:
            self._cam_target = np.array(target, dtype=np.float32)
        if fov is not None:
            self._fov = fov

    def set_light_direction(self, x: float, y: float, z: float) -> None:
        self._light_dir = np.array([x, y, z], dtype=np.float32)

    @property
    def shader_manager(self) -> ShaderManager:
        return self._shader_mgr

    @property
    def window_size(self) -> tuple[int, int]:
        return self._width, self._height
