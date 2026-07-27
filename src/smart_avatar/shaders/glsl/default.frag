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
