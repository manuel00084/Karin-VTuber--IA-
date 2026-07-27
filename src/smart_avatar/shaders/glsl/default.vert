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
