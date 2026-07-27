#version 330 core

layout(location = 0) in vec3 a_position;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec3 a_normal;

uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_outline_width;

void main() {
    vec3 expanded = a_position + a_normal * u_outline_width;
    gl_Position = u_projection * u_view * u_model * vec4(expanded, 1.0);
}
