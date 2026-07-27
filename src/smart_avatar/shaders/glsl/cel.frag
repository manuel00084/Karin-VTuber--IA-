#version 330 core

in vec2 v_uv;
in vec3 v_normal;

uniform sampler2D u_texture;
uniform vec3 u_light_dir;
uniform float u_cel_bands;

out vec4 frag_color;

void main() {
    vec4 tex = texture(u_texture, v_uv);
    vec3 norm = normalize(v_normal);
    vec3 light = normalize(u_light_dir);
    float NdotL = max(dot(norm, light), 0.0);

    float bands = max(u_cel_bands, 1.0);
    float cel = floor(NdotL * bands) / bands;
    cel = clamp(cel, 0.05, 1.0);

    vec3 color = tex.rgb * cel;
    frag_color = vec4(color, tex.a);
}
