"""
Karin Model Optimizer — reduce VRM/PMX models for better performance.
Usage: python optimize_model.py input.vrm output.vrm [--quality low|medium|high]
"""
import os
import sys
import json
import struct
import shutil
import argparse
from pathlib import Path

try:
    import trimesh
    import numpy as np
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False


# ══════════════════════════════════════════════════════════════
# TEXTURE OPTIMIZER — resize oversized textures
# ══════════════════════════════════════════════════════════════

def get_max_texture_size(quality):
    """Max texture size based on quality tier."""
    return {
        'low': 512,
        'medium': 1024,
        'high': 2048,
    }.get(quality, 1024)


def analyze_model(filepath):
    """Analyze a model file and return stats."""
    filepath = Path(filepath)
    stats = {
        'file': str(filepath),
        'size_mb': filepath.stat().st_size / (1024 * 1024),
        'format': filepath.suffix.lower(),
    }

    if stats['format'] in ('.vrm', '.glb', '.gltf'):
        if HAS_TRIMESH:
            try:
                scene = trimesh.load(str(filepath), force='scene')
                total_verts = 0
                total_tris = 0
                mesh_count = 0
                tex_count = 0
                for name, geom in scene.geometry.items():
                    if hasattr(geom, 'vertices'):
                        total_verts += len(geom.vertices)
                        mesh_count += 1
                        if hasattr(geom, 'faces'):
                            total_tris += len(geom.faces)
                stats['vertices'] = total_verts
                stats['triangles'] = total_tris
                stats['meshes'] = mesh_count
            except Exception as e:
                stats['error'] = str(e)
    elif stats['format'] == '.pmx':
        stats.update(analyze_pmx(filepath))

    return stats


def analyze_pmx(filepath):
    """Read PMX header for basic stats."""
    stats = {}
    try:
        with open(filepath, 'rb') as f:
            magic = f.read(4)
            if magic != b'PMX ':
                stats['error'] = 'Not a PMX file'
                return stats
            version = struct.unpack('<f', f.read(4))[0]
            stats['pmx_version'] = version
            globals_count = struct.unpack('<B', f.read(1))[0]
            globals_size = struct.unpack('<B', f.read(1))[0]

            # Skip to vertex count
            text_encoding = struct.unpack('<B', f.read(1))[0]
            extra_uv = struct.unpack('<B', f.read(1))[0]
            vertex_index_size = struct.unpack('<B', f.read(1))[0]
            tex_index_size = struct.unpack('<B', f.read(1))[0]
            mat_index_size = struct.unpack('<B', f.read(1))[0]
            bone_index_size = struct.unpack('<B', f.read(1))[0]
            morph_index_size = struct.unpack('<B', f.read(1))[0]
            body_index_size = struct.unpack('<B', f.read(1))[0]

            vertex_count = struct.unpack('<I', f.read(4))[0]
            stats['vertices'] = vertex_count

            index_size_map = {1: 1, 2: 2, 4: 4}
            vert_per_face = vertex_index_size // 3  # approximate
            face_count_approx = vertex_count // 3
            stats['triangles'] = face_count_approx

            # Skip vertex data to find face count
            skip = vertex_count * (3*4 + 3*4 + 2*4 + 4 + 4 + 2)
            # This is approximate; for real stats, use trimesh
    except Exception as e:
        stats['error'] = str(e)
    return stats


def optimize_glb_vrm(filepath, output_path, quality='medium'):
    """Optimize a GLB/VRM file by reducing texture sizes."""
    if not HAS_TRIMESH:
        print("⚠ trimesh no instalado. Instala con: pip install trimesh numpy")
        return False

    max_tex = get_max_texture_size(quality)
    print(f"Optimizing {filepath} (quality={quality}, maxTex={max_tex}px)...")

    try:
        import PIL.Image as Image

        scene = trimesh.load(str(filepath), force='scene')
        optimized = 0

        for name, geom in scene.geometry.items():
            if hasattr(geom, 'visual') and hasattr(geom.visual, 'image'):
                img = geom.visual.image
                if img and (img.width > max_tex or img.height > max_tex):
                    ratio = max_tex / max(img.width, img.height)
                    new_w = int(img.width * ratio)
                    new_h = int(img.height * ratio)
                    geom.visual.image = img.resize((new_w, new_h), Image.LANCZOS)
                    optimized += 1
                    print(f"  Texture: {img.width}x{img.height} → {new_w}x{new_h}")

        # Export
        scene.export(str(output_path))
        out_size = Path(output_path).stat().st_size / (1024 * 1024)
        in_size = Path(filepath).stat().st_size / (1024 * 1024)
        saved = in_size - out_size
        print(f"✅ Done: {in_size:.1f}MB → {out_size:.1f}MB (saved {saved:.1f}MB)")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def optimize_pmx(filepath, output_path, quality='medium'):
    """Copy PMX with texture folder, resize textures."""
    max_tex = get_max_texture_size(quality)
    filepath = Path(filepath)
    output = Path(output_path)

    # Copy PMX file as-is
    shutil.copy2(filepath, output)

    # Find texture folder (same name without extension, or in subfolder)
    tex_folder = filepath.parent / filepath.stem
    if not tex_folder.is_dir():
        tex_folder = filepath.parent

    out_tex_folder = output.parent / output.stem
    if tex_folder != out_tex_folder:
        if tex_folder.is_dir():
            shutil.copytree(tex_folder, out_tex_folder, dirs_exist_ok=True)

    # Resize textures
    try:
        from PIL import Image
        resized = 0
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tga']:
            for tex_file in (out_tex_folder.parent if out_tex_folder.is_dir() else output.parent).rglob(ext):
                try:
                    img = Image.open(tex_file)
                    if img.width > max_tex or img.height > max_tex:
                        ratio = max_tex / max(img.width, img.height)
                        new_w = int(img.width * ratio)
                        new_h = int(img.height * ratio)
                        img.resize((new_w, new_h), Image.LANCZOS).save(tex_file)
                        resized += 1
                        print(f"  {tex_file.name}: {img.width}x{img.height} → {new_w}x{new_h}")
                except:
                    pass
        print(f"✅ PMX copied + {resized} textures resized")
        return True
    except ImportError:
        print("⚠ PIL no instalado. pip install Pillow")
        return True  # File still copied


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Karin Model Optimizer')
    parser.add_argument('input', help='Input model file (VRM/GLB/PMX)')
    parser.add_argument('output', nargs='?', help='Output file (default: input_optimized.ext)')
    parser.add_argument('--quality', choices=['low', 'medium', 'high'], default='medium')
    parser.add_argument('--analyze', action='store_true', help='Only analyze, don\'t optimize')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return

    # Analyze
    print(f"\n📊 Analyzing: {input_path.name}")
    stats = analyze_model(input_path)
    for k, v in stats.items():
        if k == 'file': continue
        if isinstance(v, int) and v > 1000:
            print(f"  {k}: {v:,}")
        else:
            print(f"  {k}: {v}")

    if args.analyze:
        return

    # Determine output
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.parent / f"{input_path.stem}_opt{input_path.suffix}"

    print(f"\n🔧 Optimizing → {output_path.name} (quality={args.quality})")
    ext = input_path.suffix.lower()

    if ext in ('.vrm', '.glb', '.gltf', '.fbx'):
        optimize_glb_vrm(input_path, output_path, args.quality)
    elif ext == '.pmx':
        optimize_pmx(input_path, output_path, args.quality)
    else:
        print(f"❌ Format not supported: {ext}")


if __name__ == '__main__':
    main()
