#version 330 core

uniform vec3 u_outline_color;
out vec4 frag_color;

void main() {
    frag_color = vec4(u_outline_color, 1.0);
}
