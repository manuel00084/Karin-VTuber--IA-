"""Gestor de shaders GLSL con compilación, enlace y uniform setters."""

from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

from OpenGL.GL import (
    GL_COMPILE_STATUS,
    GL_FLOAT,
    GL_FRAGMENT_SHADER,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_VERTEX_SHADER,
    glAttachShader,
    glCompileShader,
    glCreateProgram,
    glCreateShader,
    glDeleteShader,
    glGetAttribLocation,
    glGetProgramInfoLog,
    glGetProgramiv,
    glGetShaderInfoLog,
    glGetShaderiv,
    glGetUniformLocation,
    glLinkProgram,
    glShaderSource,
    glUniform1f,
    glUniform1i,
    glUniform2f,
    glUniform3f,
    glUniformMatrix4fv,
    glUseProgram,
)

log = logging.getLogger(__name__)

# ======================================================================
# GLSL — Built-in shader sources
# ======================================================================

_DEFAULT_VERT = """\
#version 330 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec3 a_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

out vec2 v_uv;
out vec3 v_normal;
out vec3 v_frag_pos;

void main() {
    vec4 world_pos = u_model * vec4(a_position, 1.0);
    v_frag_pos = vec3(world_pos);
    v_uv = a_uv;
    v_normal = mat3(transpose(inverse(u_model))) * a_normal;
    gl_Position = u_projection * u_view * world_pos;
}
"""

_DEFAULT_FRAG = """\
#version 330 core

in vec2 v_uv;
in vec3 v_normal;
in vec3 v_frag_pos;

uniform sampler2D u_texture;
uniform vec3 u_light_dir;
uniform float u_alpha;

out vec4 frag_color;

void main() {
    vec4 tex = texture(u_texture, v_uv);
    vec3 norm = normalize(v_normal);
    vec3 light = normalize(u_light_dir);
    float diff = max(dot(norm, light), 0.0);
    float ambient = 0.3;
    vec3 lit = tex.rgb * (ambient + diff * 0.7);
    frag_color = vec4(lit, tex.a * u_alpha);
}
"""

_CEL_VERT = """\
#version 330 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec3 a_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;

out vec2 v_uv;
out vec3 v_normal;

void main() {
    v_uv = a_uv;
    v_normal = mat3(transpose(inverse(u_model))) * a_normal;
    gl_Position = u_projection * u_view * u_model * vec4(a_position, 1.0);
}
"""

_CEL_FRAG = """\
#version 330 core

in vec2 v_uv;
in vec3 v_normal;

uniform sampler2D u_texture;
uniform vec3 u_light_dir;
uniform float u_cel_bands;  // number of discrete shading levels

out vec4 frag_color;

void main() {
    vec4 tex = texture(u_texture, v_uv);
    vec3 norm = normalize(v_normal);
    vec3 light = normalize(u_light_dir);
    float NdotL = max(dot(norm, light), 0.0);

    // Quantize lighting into discrete bands
    float bands = max(u_cel_bands, 1.0);
    float cel = floor(NdotL * bands) / bands;
    cel = clamp(cel, 0.05, 1.0);

    vec3 color = tex.rgb * cel;
    frag_color = vec4(color, tex.a);
}
"""

_OUTLINE_VERT = """\
#version 330 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec3 a_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_outline_width;

void main() {
    // Push vertices along their normals for outline shell
    vec3 expanded = a_position + a_normal * u_outline_width;
    gl_Position = u_projection * u_view * u_model * vec4(expanded, 1.0);
}
"""

_OUTLINE_FRAG = """\
#version 330 core

uniform vec3 u_outline_color;
out vec4 frag_color;

void main() {
    frag_color = vec4(u_outline_color, 1.0);
}
"""


_GLSL_DIR = os.path.join(os.path.dirname(__file__), "glsl")

_BUILTIN_FILES: dict[str, tuple[str, str]] = {
    "default": ("default.vert", "default.frag"),
    "cel": ("cel.vert", "cel.frag"),
    "outline": ("outline.vert", "outline.frag"),
}


def _load_glsl(name: str) -> tuple[str, str] | None:
    """Try to load shader pair from .glsl files. Returns None if missing."""
    files = _BUILTIN_FILES.get(name)
    if files is None:
        return None
    vert_path = os.path.join(_GLSL_DIR, files[0])
    frag_path = os.path.join(_GLSL_DIR, files[1])
    if not os.path.isfile(vert_path) or not os.path.isfile(frag_path):
        return None
    with open(vert_path, "r", encoding="utf-8") as f:
        vert = f.read()
    with open(frag_path, "r", encoding="utf-8") as f:
        frag = f.read()
    return vert, frag


class ShaderManager:
    """Carga, compile y gestiona programas GLSL.

    Incluye tres shaders integrados: ``default``, ``cel`` y ``outline``.
    Primero intenta cargar desde archivos .glsl; si no existen, usa los
    strings embebidos como fallback.
    Se pueden registrar shaders personalizados vía :meth:`load_shader`.
    """

    _BUILTIN: dict[str, tuple[str, str]] = {
        "default": (_DEFAULT_VERT, _DEFAULT_FRAG),
        "cel": (_CEL_VERT, _CEL_FRAG),
        "outline": (_OUTLINE_VERT, _OUTLINE_FRAG),
    }

    def __init__(self) -> None:
        self._programs: dict[str, int] = {}
        self._locations: dict[str, dict[str, int]] = {}
        self._active: str | None = None

    # ------------------------------------------------------------------
    # Compilación
    # ------------------------------------------------------------------

    @staticmethod
    def _compile_shader(source: str, shader_type: int) -> int:
        """Compila un solo shader. Devuelve su id o lanza RuntimeError."""
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)

        status = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not status:
            info = glGetShaderInfoLog(shader)
            glDeleteShader(shader)
            kind = "vertex" if shader_type == GL_VERTEX_SHADER else "fragment"
            raise RuntimeError(f"Error compilando shader {kind}:\n{info.decode()}")
        return shader

    def compile_program(self, vertex_src: str, fragment_src: str) -> int:
        """Compila y enlaza un programa de shader. Devuelve el program id."""
        vs = self._compile_shader(vertex_src, GL_VERTEX_SHADER)
        fs = self._compile_shader(fragment_src, GL_FRAGMENT_SHADER)

        program = glCreateProgram()
        glAttachShader(program, vs)
        glAttachShader(program, fs)
        glLinkProgram(program)

        status = glGetProgramiv(program, GL_LINK_STATUS)
        if not status:
            info = glGetProgramInfoLog(program)
            glDeleteShader(vs)
            glDeleteShader(fs)
            raise RuntimeError(f"Error enlazando programa de shader:\n{info.decode()}")

        glDeleteShader(vs)
        glDeleteShader(fs)
        return program

    # ------------------------------------------------------------------
    # Carga de shaders
    # ------------------------------------------------------------------

    def load_shader(self, name: str, vertex_path: str, fragment_path: str) -> None:
        """Carga shader desde archivos GLSL y lo registra como *name*."""
        with open(vertex_path, "r", encoding="utf-8") as f:
            vert_src = f.read()
        with open(fragment_path, "r", encoding="utf-8") as f:
            frag_src = f.read()

        program = self.compile_program(vert_src, frag_src)
        self._programs[name] = program
        self._locations[name] = {}
        log.info("Shader '%s' cargado (program %d)", name, program)

    def register_builtin(self, name: str) -> None:
        """Compila e registra un shader built-in por nombre.

        Intenta cargar desde archivos .glsl primero; si fallan,
        usa los strings embebidos como fallback.
        """
        if name in self._programs:
            return
        if name not in self._BUILTIN:
            log.warning("Shader built-in desconocido: %s", name)
            return

        file_pair = _load_glsl(name)
        if file_pair is not None:
            vert_src, frag_src = file_pair
            log.debug("Shader '%s' cargado desde archivos .glsl", name)
        else:
            vert_src, frag_src = self._BUILTIN[name]
            log.debug("Shader '%s' usando fallback embebido", name)

        program = self.compile_program(vert_src, frag_src)
        self._programs[name] = program
        self._locations[name] = {}
        log.info("Shader built-in '%s' registrado (program %d)", name, program)

    def init_all_builtins(self) -> None:
        """Compila y registra todos los shaders built-in."""
        for name in self._BUILTIN:
            self.register_builtin(name)

    # ------------------------------------------------------------------
    # Uso
    # ------------------------------------------------------------------

    def use_shader(self, name: str) -> None:
        """Activa el programa de shader *name*."""
        if name not in self._programs:
            raise KeyError(f"Shader no registrado: {name}")
        glUseProgram(self._programs[name])
        self._active = name

    @property
    def active_program(self) -> str | None:
        return self._active

    def get_program(self, name: str) -> int:
        """Devuelve el program id de un shader registrado."""
        if name not in self._programs:
            raise KeyError(f"Shader no registrado: {name}")
        return self._programs[name]

    # ------------------------------------------------------------------
    # Uniforms
    # ------------------------------------------------------------------

    def _get_location(self, name: str, uniform: str) -> int:
        """Obtiene y cachea la ubicación de un uniform."""
        cache = self._locations.setdefault(name, {})
        if uniform not in cache:
            loc = glGetUniformLocation(self._programs[name], uniform)
            cache[uniform] = loc
        return cache[uniform]

    def set_uniform(self, name: str, uniform: str, value: Any) -> None:
        """Establece un uniform del shader *name*.

        Tipos soportados:
            - ``float`` / ``int`` → ``glUniform1f`` / ``glUniform1i``
            - ``tuple[float, float]`` (2 elementos) → ``glUniform2f``
            - ``tuple[float, float, float]`` (3 elementos) → ``glUniform3f``
            - ``numpy.ndarray`` (4×4) → ``glUniformMatrix4fv``
        """
        if name not in self._programs:
            raise KeyError(f"Shader no registrado: {name}")

        loc = self._get_location(name, uniform)
        if loc == -1:
            log.debug("Uniform '%s' no encontrado en shader '%s'", uniform, name)
            return

        if isinstance(value, (int, np.integer)):
            glUniform1i(loc, int(value))
        elif isinstance(value, float):
            glUniform1f(loc, value)
        elif isinstance(value, (tuple, list)):
            if len(value) == 2:
                glUniform2f(loc, float(value[0]), float(value[1]))
            elif len(value) == 3:
                glUniform3f(loc, float(value[0]), float(value[1]), float(value[2]))
            else:
                log.warning("Tuple uniform de longitud no soportada: %d", len(value))
        elif isinstance(value, np.ndarray):
            if value.shape == (4, 4):
                glUniformMatrix4fv(loc, 1, GL_TRUE, value.astype(np.float32))
            else:
                log.warning("Matriz numpy de forma no soportada: %s", value.shape)
        else:
            log.warning("Tipo de uniform no soportado: %s", type(value).__name__)

    # ------------------------------------------------------------------
    # Limpieza
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Elimina todos los programas de shader de la GPU."""
        from OpenGL.GL import glDeleteProgram

        for name, prog in self._programs.items():
            glDeleteProgram(prog)
            log.debug("Shader '%s' eliminado", name)
        self._programs.clear()
        self._locations.clear()
        self._active = None
