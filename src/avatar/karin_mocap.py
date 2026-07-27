import os, json, socket, subprocess, threading, time, shutil, math, struct
from pathlib import Path
from collections import deque
import xml.etree.ElementTree as ET
import re
from src.utils.log import error, warn


# ══════════════════════════════════════════════════════════════
# EMOTION DETECTION — keyword-based, no dependencies
# ══════════════════════════════════════════════════════════════

EMOTION_KEYWORDS = {
    "happy": {
        "keywords": [
            "feliz", "alegre", "genial", "increíble", "increible", "fantástico", "fantastico",
            "excelente", "perfecto", "brillante", "súper", "super", "bien", "encanta",
            "divertido", "risa", "jaja", "jeje", "jiji", "xD", "lol", "buenísimo",
            "maravilloso", "hermoso", "lindo", "bonito", "gracias", "sí", "claro",
            "absolutamente", "obvio", "claro que sí", "me gusta", "amo", "adoro",
            "contento", "emocionado", "animado", "entusiasmado", "celebrar", "fiesta"
        ],
        "blendshapes": {
            "mouth_smile": 0.8,
            "brow_raise_left": 0.3,
            "brow_raise_right": 0.3,
            "jaw_open": 0.1
        }
    },
    "sad": {
        "keywords": [
            "triste", "pena", "lamento", "lo siento", "perdón", "perdon",
            "llorar", "llanto", "dolor", "sufro", "tristemente", "desafortunado",
            "mal", "terrible", "horrible", "desastre", "problema", "equivocado",
            "fracaso", "perdí", "perdi", "soledad", "solo", "sola", "extrañar",
            "extraño", "extraña", "adiós", "adios", "chao", "hasta luego"
        ],
        "blendshapes": {
            "mouth_sad": 0.7,
            "brow_raise_left": -0.3,
            "brow_raise_right": -0.3,
            "jaw_open": 0.05
        }
    },
    "angry": {
        "keywords": [
            "enojado", "molesto", "furioso", "rabia", "odio", "detesto",
            "estúpido", "estupido", "idiota", "inútil", "inutil", "basura",
            "no me gusta", "fastidio", "maldita", "carajo", "joder", "mierda",
            "imposible", "inaceptable", "indignante", "brutal", "violento",
            "furor", "ira", "resentimiento", "venganza"
        ],
        "blendshapes": {
            "brow_raise_left": -0.5,
            "brow_raise_right": -0.5,
            "jaw_open": 0.3,
            "mouth_smile": -0.2
        }
    },
    "surprised": {
        "keywords": [
            "wow", "vaya", "increíble", "increible", "sorpresa", "sorprendido",
            "no puede ser", "imposible", "en serio", "¿qué?", "que?",
            "¡oh!", "oh Dios", "oh my god", "omg", "asombroso", "extraordinario",
            "inesperado", "inesperadamente", "boquiabierto", "alucinante",
            "deslumbrante", "estupefacto", "atónito", "atonito"
        ],
        "blendshapes": {
            "brow_raise_left": 0.8,
            "brow_raise_right": 0.8,
            "jaw_open": 0.6,
            "mouth_smile": 0.2
        }
    },
    "thinking": {
        "keywords": [
            "pienso", "creo", "considero", "analizo", "reflexiono", "imagino",
            "supongo", "tal vez", "quizás", "quizas", "podría", "podria",
            "interesante", "curioso", "duda", "pregunta", "respuesta",
            "problema", "solución", "solucion", "estrategia", "planificar",
            "mm", "hmm", "ehm", "pues", "bueno", "a ver", "déjame", "dejame"
        ],
        "blendshapes": {
            "look_left": 0.3,
            "brow_raise_left": 0.2,
            "mouth_smile": 0.1
        }
    }
}


def detect_emotion(text):
    """
    Detecta la emoción dominante en un texto.
    Retorna (emotion_name, blendshapes_dict).
    """
    if not text:
        return "neutral", {}

    text_lower = text.lower()
    scores = {}

    for emotion, data in EMOTION_KEYWORDS.items():
        score = 0
        for kw in data["keywords"]:
            if kw in text_lower:
                score += 1
        if score > 0:
            scores[emotion] = score

    if not scores:
        return "neutral", {}

    dominant = max(scores, key=scores.get)
    blendshapes = EMOTION_KEYWORDS[dominant]["blendshapes"].copy()

    # Scale blendshapes by keyword count (0.5 to 1.0)
    max_score = scores[dominant]
    scale = min(1.0, max(0.5, max_score / 3))
    for k in blendshapes:
        blendshapes[k] = blendshapes[k] * scale

    return dominant, blendshapes


# ══════════════════════════════════════════════════════════════

COMMON_PATHS = [
    os.path.expandvars(r"%ProgramFiles%\KarinMocap\KarinMocap.exe"),
    os.path.expandvars(r"%ProgramFiles(x86)%\KarinMocap\KarinMocap.exe"),
    os.path.expandvars(r"%LOCALAPPDATA%\KarinMocap\KarinMocap.exe"),
    os.path.expandvars(r"%USERPROFILE%\AppData\Local\KarinMocap\KarinMocap.exe"),
    os.path.expandvars(r"%ProgramFiles%\Steam\steamapps\common\KarinMocap\KarinMocap.exe"),
    os.path.expandvars(r"%USERPROFILE%\Desktop\KarinMocap\KarinMocap.exe"),
]

VRM_BLENDSHAPE_MAP = {
    "blink_left": "Blink_L",
    "blink_right": "Blink_R",
    "blink": "Blink",
    "jaw_open": "JawOpen",
    "jaw_left": "JawLeft",
    "jaw_right": "JawRight",
    "mouth_smile": "MouthSmile",
    "mouth_sad": "MouthSad",
    "mouth_funnel": "MouthFunnel",
    "brow_down_left": "BrowDown_L",
    "brow_down_right": "BrowDown_R",
    "brow_raise_left": "BrowRaise_L",
    "brow_raise_right": "BrowRaise_R",
    "look_left": "LookLeft",
    "look_right": "LookRight",
    "look_up": "LookUp",
    "look_down": "LookDown",
    "cheek_puff": "CheekPuff",
    "tongue_out": "TongueOut",
    "head_nod": "NeckNod",
    "head_tilt": "NeckTiltLeft",
}

APPDATA_VMM = os.path.expandvars(r"%APPDATA%\KarinMocap")
VMM_SETTINGS_XML = os.path.join(APPDATA_VMM, "KarinMocap Settings.xml")


# ══════════════════════════════════════════════════════════════
# MOTION PARSERS — BVH, .anim (text), VMD
# ══════════════════════════════════════════════════════════════

def parse_bvh(filepath):
    """Parse BVH (Biovision Hierarchy) motion capture file.
    Returns: { joints: [...], frame_time: float, frames: [[values...], ...] }
    """
    with open(filepath, 'r') as f:
        lines = f.readlines()

    joints = []
    joint_stack = []
    frame_time = 1.0 / 30.0
    frames = []
    reading_motion = False
    num_channels = 0

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        if reading_motion:
            if line.startswith('Frame Time:'):
                frame_time = float(line.split(':')[1].strip())
            elif line.startswith('Frames:'):
                pass
            else:
                parts = line.split()
                vals = [float(v) for v in parts]
                frames.append(vals)
            i += 1
            continue

        if line == 'HIERARCHY':
            i += 1
            continue

        if line.startswith('ROOT'):
            name = line.split()[1]
            joint = {'name': name, 'offset': [0, 0, 0], 'channels': [], 'children': [], 'parent': None}
            joints.append(joint)
            joint_stack.append(joint)
            i += 1
            continue

        if line.startswith('JOINT'):
            name = line.split()[1]
            parent = joint_stack[-1] if joint_stack else None
            joint = {'name': name, 'offset': [0, 0, 0], 'channels': [], 'children': [], 'parent': parent['name'] if parent else None}
            joints.append(joint)
            if parent:
                parent['children'].append(name)
            joint_stack.append(joint)
            i += 1
            continue

        if line == 'End Site':
            i += 1
            continue

        if line == '{':
            i += 1
            continue

        if line == '}':
            if joint_stack:
                joint_stack.pop()
            i += 1
            continue

        if line.startswith('OFFSET'):
            parts = line.split()
            offset = [float(parts[1]), float(parts[2]), float(parts[3])]
            if joint_stack:
                joint_stack[-1]['offset'] = offset
            i += 1
            continue

        if line.startswith('CHANNELS'):
            parts = line.split()
            count = int(parts[1])
            channels = parts[2:]
            if joint_stack:
                joint_stack[-1]['channels'] = channels
                joint_stack[-1]['channel_offset'] = num_channels
            num_channels += count
            i += 1
            continue

        if line == 'MOTION':
            reading_motion = True
            i += 1
            continue

        i += 1

    # Convert to Three.js compatible format
    joint_list = []
    for j in joints:
        joint_list.append({
            'name': j['name'],
            'offset': j['offset'],
            'channels': j['channels'],
            'channel_offset': j.get('channel_offset', 0),
            'parent': j['parent'],
        })

    return {
        'format': 'bvh',
        'joints': joint_list,
        'num_channels': num_channels,
        'frame_time': frame_time,
        'frames': frames,
    }


def parse_anim_text(filepath):
    """Parse Unity .anim text (YAML) format.
    Returns: same format as BVH for viewer compatibility.
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    curves = []
    current_path = ''
    current_attr = ''

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('m_Path:'):
            current_path = line.split(':', 1)[1].strip().strip('"')
        elif line.startswith('m_Attr:'):
            current_attr = line.split(':', 1)[1].strip().strip('"')
        elif line.startswith('m_Time:'):
            pass
        elif line.startswith('m_Value:'):
            val_str = line.split(':', 1)[1].strip()
            try:
                val = float(val_str)
            except ValueError:
                val = 0.0
            curves.append({
                'path': current_path,
                'attr': current_attr,
                'value': val,
            })

    # Group curves by time/frame and build joint list
    joint_names = list(set(c['path'] for c in curves if c['path']))
    joints = [{'name': n, 'offset': [0, 0, 0], 'channels': [], 'channel_offset': 0, 'parent': None}
              for n in joint_names]

    return {
        'format': 'anim',
        'joints': joints,
        'num_channels': 0,
        'frame_time': 1.0 / 30.0,
        'frames': [],
        'raw_curves': curves,
    }


def parse_vmd(filepath):
    """Parse VMD (Vocaloid Motion Dance) file for MMD models.
    Returns: { format, joints, frame_time, frames }
    """
    with open(filepath, 'rb') as f:
        data = f.read()

    # VMD header: 30 bytes model name + 50 bytes comment
    if len(data) < 80:
        return None

    model_name = data[:30].decode('shift_jis', errors='ignore').rstrip('\x00')

    # Skip to bone motion count (offset 80)
    if len(data) < 84:
        return None

    bone_count = struct.unpack_from('<I', data, 80)[0]

    bone_keys = []
    offset = 84
    for _ in range(bone_count):
        if offset + 110 > len(data):
            break
        bone_name = data[offset:offset+15].decode('shift_jis', errors='ignore').rstrip('\x00')
        frame_num = struct.unpack_from('<I', data, offset + 15)[0]
        pos_x, pos_y, pos_z = struct.unpack_from('<fff', data, offset + 19)
        rot_x, rot_y, rot_z, rot_w = struct.unpack_from('<ffff', data, offset + 31)
        # 64 bytes interpolation data
        bone_keys.append({
            'bone': bone_name,
            'frame': frame_num,
            'position': [pos_x, pos_y, pos_z],
            'rotation': [rot_x, rot_y, rot_z, rot_w],
        })
        offset += 110

    # Build joint list
    bone_names = list(dict.fromkeys(k['bone'] for k in bone_keys))
    joints = [{'name': n, 'offset': [0, 0, 0], 'channels': [], 'channel_offset': 0, 'parent': None}
              for n in bone_names]

    # Group by frame
    max_frame = max((k['frame'] for k in bone_keys), default=0) if bone_keys else 0
    fps = 30.0
    total_frames = max_frame + 1
    frames = []
    for f_idx in range(total_frames):
        frame_data = {}
        for k in bone_keys:
            if k['frame'] == f_idx:
                frame_data[k['bone']] = {
                    'pos': k['position'],
                    'rot': k['rotation'],
                }
        frames.append(frame_data)

    return {
        'format': 'vmd',
        'joints': joints,
        'num_channels': 0,
        'frame_time': 1.0 / fps,
        'frames': frames,
        'fps': fps,
        'total_frames': total_frames,
        'bone_keys': bone_keys,
    }


def load_motion(filepath):
    """Auto-detect format and load motion file.
    Returns motion data dict for the viewer.
    """
    ext = Path(filepath).suffix.lower()
    try:
        if ext == '.bvh':
            return parse_bvh(filepath)
        elif ext == '.anim':
            return parse_anim_text(filepath)
        elif ext == '.vmd':
            return parse_vmd(filepath)
        else:
            # Try BVH first (text-based)
            with open(filepath, 'r') as f:
                first_line = f.readline().strip()
            if first_line == 'HIERARCHY':
                return parse_bvh(filepath)
            return None
    except Exception as e:
        return None


class KalmanFilter1D:
    """Simple 1D Kalman filter for smoothing noisy tracking data."""
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        self.q = process_noise
        self.r = measurement_noise
        self.x = 0.0
        self.p = 1.0
        self.k = 0.0

    def update(self, measurement):
        self.p += self.q
        self.k = self.p / (self.p + self.r)
        self.x += self.k * (measurement - self.x)
        self.p *= (1 - self.k)
        return self.x

    def reset(self, value=0.0):
        self.x = value
        self.p = 1.0


class TrackingSmoother:
    """Smooths head rotation and blendshapes using Kalman filters."""
    def __init__(self, process_noise=0.015, measurement_noise=0.12):
        self.head_x = KalmanFilter1D(process_noise, measurement_noise)
        self.head_y = KalmanFilter1D(process_noise, measurement_noise)
        self.head_z = KalmanFilter1D(process_noise, measurement_noise)
        self.head_w = KalmanFilter1D(process_noise, measurement_noise)
        self._blend_filters = {}
        self.pn = process_noise
        self.rn = measurement_noise

    def smooth_head(self, head_rot):
        if not head_rot:
            return head_rot
        return {
            "x": self.head_x.update(head_rot.get("x", 0)),
            "y": self.head_y.update(head_rot.get("y", 0)),
            "z": self.head_z.update(head_rot.get("z", 0)),
            "w": self.head_w.update(head_rot.get("w", 1)),
        }

    def smooth_blendshapes(self, bs):
        if not bs:
            return bs
        out = {}
        for k, v in bs.items():
            if k not in self._blend_filters:
                self._blend_filters[k] = KalmanFilter1D(self.pn, self.rn)
            out[k] = self._blend_filters[k].update(v)
        return out


class KarinMocapController:
    def __init__(self, log_fn=print):
        self._log_fn = log_fn
        self._vm_path = None
        self._process = None

        self._face_thread = None
        self._face_running = False
        self._face_camera = 0
        self._face_confidence = 0.5
        self._face_flip = True

        self._keyboard_thread = None
        self._keyboard_running = False
        self._key_to_expression = {
            "a": {"blink": 1.0},
            "s": {"mouth_smile": 0.8},
            "d": {"brow_raise_left": 0.7, "brow_raise_right": 0.7},
            "f": {"jaw_open": 0.6},
            "space": {"blink": 1.0},
        }

        self._audio_thread = None
        self._audio_running = False
        self._audio_sensitivity = 0.3
        self._audio_device = None

        self._gamepad_thread = None
        self._gamepad_running = False

        self._vrm_path = None
        self._recent_vrms = []
        self._load_recent_vrms()

        self._head_rot = {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
        self._expressions = {}
        self._lock = threading.Lock()

        self._face_model = None
        self._face_mesh = None
        self._face_detector = None

        self._audio_stream = None

        self._tracking_callback = None

        self._smoother = TrackingSmoother()

    def set_tracking_callback(self, callback):
        """Register a callback(head_rot, blendshapes) called on every tracking update."""
        self._tracking_callback = callback

    def set_viseme_callback(self, callback):
        """Register a callback(landmarks) called with face mesh landmarks for visemes."""
        self._viseme_callback = callback

    def set_bg_removal_callback(self, callback):
        """Register a callback(mask) called with selfie segmentation mask for bg removal."""
        self._bg_removal_callback = callback

    def set_smoothing(self, process_noise=0.015, measurement_noise=0.12):
        """Configure Kalman filter smoothing. Lower values = smoother but slower response."""
        self._smoother = TrackingSmoother(process_noise, measurement_noise)
        self._log(f"Smoothing configurado: pn={process_noise}, rn={measurement_noise}")

    def detect_and_apply_emotion(self, text):
        """
        Detecta emoción del texto y envía blendshapes al viewer.
        Retorna (emotion_name, blendshapes_dict).
        """
        emotion, bs = detect_emotion(text)
        if bs and self._tracking_callback:
            try:
                self._tracking_callback(head_rot=None, blendshapes=bs)
            except Exception as e:
                error(f"_on_emotion_detected tracking callback: {e}")
        return emotion, bs

    def apply_preset_emotion(self, emotion_name):
        """
        Aplica una emoción predefinida directamente.
        emotion_name: 'happy', 'sad', 'angry', 'surprised', 'thinking', 'neutral'
        """
        if emotion_name in EMOTION_KEYWORDS:
            bs = EMOTION_KEYWORDS[emotion_name]["blendshapes"].copy()
        elif emotion_name == "neutral":
            bs = {
                "mouth_smile": 0.0, "mouth_sad": 0.0,
                "brow_raise_left": 0.0, "brow_raise_right": 0.0,
                "jaw_open": 0.0, "look_left": 0.0, "look_right": 0.0
            }
        else:
            return emotion_name, {}

        if self._tracking_callback:
            try:
                self._tracking_callback(head_rot=None, blendshapes=bs)
            except Exception:
                pass
        return emotion_name, bs

    def _call_tracking_callback(self, head_rot=None, blendshapes=None):
        if self._tracking_callback:
            try:
                if head_rot:
                    head_rot = self._smoother.smooth_head(head_rot)
                if blendshapes:
                    blendshapes = self._smoother.smooth_blendshapes(blendshapes)
                self._tracking_callback(head_rot, blendshapes)
            except Exception:
                pass

    def _log(self, msg):
        self._log_fn(f"[KarinMocap] {msg}")

    # ── Process Management ──

    def find_installation(self):
        for p in COMMON_PATHS:
            if os.path.isfile(p):
                self._vm_path = p
                return p
        p = shutil.which("KarinMocap.exe")
        if p:
            self._vm_path = p
            return p
        return None

    def set_path(self, path):
        self._vm_path = path

    @property
    def is_installed(self):
        return self._vm_path and os.path.isfile(self._vm_path)

    @property
    def is_running(self):
        return self._process is not None and self._process.poll() is None

    @property
    def pid(self):
        return self._process.pid if self._process and self.is_running else None

    def start(self, vrm_path=None):
        if not self._vm_path:
            self._log("No se encontró KarinMocap.exe")
            return False
        if self.is_running:
            self._log("Ya está en ejecución")
            return True
        if vrm_path:
            self._load_vrm_settings(vrm_path)
        try:
            self._process = subprocess.Popen(
                [self._vm_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._log(f"Iniciado (PID: {self._process.pid})")
            return True
        except Exception as e:
            self._log(f"Error al iniciar: {e}")
            return False

    def stop(self):
        if self._process and self.is_running:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._log("Detenido")
        self.stop_face_tracking()
        self.stop_keyboard_tracking()
        self.stop_audio_tracking()
        self.stop_gamepad_tracking()
        self._process = None

    # ── VRM Loading ──

    def _get_mocap_settings_xml(self):
        return VMM_SETTINGS_XML

    def _load_vrm_settings(self, vrm_path):
        xml_path = self._get_mocap_settings_xml()
        if not os.path.exists(xml_path):
            self._log(f"Config XML no encontrado: {xml_path}")
            return False
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            for elem in root.iter():
                if elem.tag.endswith("VrmFilePath") or "VRM" in elem.tag.upper() and "PATH" in elem.tag.upper():
                    elem.text = vrm_path
                    tree.write(xml_path)
                    self._log(f"VRM configurado en XML: {vrm_path}")
                    return True
            self._log("Tag VrmFilePath no encontrado en XML")
            return False
        except Exception as e:
            self._log(f"Error editando XML: {e}")
            return False

    def load_vrm(self, vrm_path):
        if not os.path.isfile(vrm_path):
            self._log(f"VRM no encontrado: {vrm_path}")
            return False
        self._vrm_path = vrm_path
        self._add_recent_vrm(vrm_path)
        if self.is_running:
            self._log("Reiniciando para cargar nuevo VRM...")
            self.stop()
            time.sleep(0.5)
            self.start(vrm_path)
            if self._face_running:
                self.start_face_tracking(self._face_camera, self._face_confidence, self._face_flip)
        else:
            self._load_vrm_settings(vrm_path)
        self._log(f"VRM cargado: {os.path.basename(vrm_path)}")
        return True

    def _load_recent_vrms(self):
        try:
            recent_file = os.path.join(APPDATA_VMM, "recent_vrms.json")
            if os.path.isfile(recent_file):
                with open(recent_file, encoding="utf-8") as f:
                    self._recent_vrms = json.load(f)
        except Exception as e:
            error(f"_load_recent_vrms: {e}")
            self._recent_vrms = []

    def _add_recent_vrm(self, path):
        if path in self._recent_vrms:
            self._recent_vrms.remove(path)
        self._recent_vrms.insert(0, path)
        self._recent_vrms = self._recent_vrms[:20]
        try:
            os.makedirs(APPDATA_VMM, exist_ok=True)
            recent_file = os.path.join(APPDATA_VMM, "recent_vrms.json")
            with open(recent_file, "w", encoding="utf-8") as f:
                json.dump(self._recent_vrms, f, ensure_ascii=False)
        except Exception as e:
            error(f"_add_recent_vrm save: {e}")

    @property
    def recent_vrms(self):
        return list(self._recent_vrms)

    # ── Face Tracking (MediaPipe) ──

    @property
    def face_tracking_available(self):
        try:
            import mediapipe
            return True
        except ImportError:
            return False

    def _get_mediapipe(self):
        try:
            import mediapipe as mp
            return mp
        except ImportError:
            return None

    def _face_landmarks_to_expressions(self, face_landmarks, img_w, img_h):
        h, w = img_h, img_w
        lm = face_landmarks.landmark

        def dist(i, j):
            return math.sqrt((lm[i].x - lm[j].x)**2 + (lm[i].y - lm[j].y)**2)

        def mid(i, j):
            return (lm[i].x + lm[j].x) / 2, (lm[i].y + lm[j].y) / 2

        # Head pose from nose tip and face orientation
        nose = lm[1]
        left_eye = lm[33]
        right_eye = lm[263]
        mouth_c = lm[13]

        # Blink: eye aspect ratio
        left_ear = (dist(159, 145) + dist(158, 153)) / (2 * max(dist(33, 133), 0.001))
        right_ear = (dist(386, 374) + dist(385, 380)) / (2 * max(dist(362, 263), 0.001))

        # Mouth open
        mouth_open = dist(13, 14) / max(dist(61, 291), 0.001)

        # Eyebrow raise
        brow_l = dist(105, 66)
        brow_r = dist(334, 296)

        # Head rotation from face mesh
        face_up = lm[10]
        face_down = lm[152]
        face_left = lm[234]
        face_right = lm[454]

        pitch = (face_up.y - face_down.y) * 2
        yaw = (nose.x - face_down.x) * 2
        roll = (face_right.y - face_left.y) * 2

        # Mouth smile (mouth corners)
        mouth_l = lm[61]
        mouth_r = lm[291]
        mouth_smile_val = (mouth_l.y + mouth_r.y) / 2 - mouth_c.y
        mouth_smile = max(0.0, min(1.0, mouth_smile_val * 5))

        # Mouth sad (mouth corners down)
        mouth_sad = max(0.0, min(1.0, -mouth_smile_val * 3))

        # Eye look direction
        iris_l = lm[468] if len(lm) > 468 else lm[33]
        iris_r = lm[473] if len(lm) > 473 else lm[263]
        look_x = ((iris_l.x + iris_r.x) / 2 - (left_eye.x + right_eye.x) / 2) * 10
        look_y = ((iris_l.y + iris_r.y) / 2 - (left_eye.y + right_eye.y) / 2) * 10

        # Quaternion from euler angles
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)

        expressions = {
            "blink": max(0.0, 1.0 - left_ear / 0.3),
            "blink_left": max(0.0, 1.0 - left_ear / 0.3),
            "blink_right": max(0.0, 1.0 - right_ear / 0.3),
            "jaw_open": max(0.0, min(1.0, (mouth_open - 0.1) * 3)),
            "brow_raise_left": max(0.0, min(1.0, brow_l * 2)),
            "brow_raise_right": max(0.0, min(1.0, brow_r * 2)),
            "mouth_smile": mouth_smile,
            "mouth_sad": mouth_sad,
            "look_left": max(0.0, min(1.0, -look_x)),
            "look_right": max(0.0, min(1.0, look_x)),
            "look_up": max(0.0, min(1.0, -look_y)),
            "look_down": max(0.0, min(1.0, look_y)),
        }

        head_rot = {
            "x": sp * cy,
            "y": sy * cp,
            "z": -sy * sp + sr * cp,
            "w": cp * cy
        }

        return head_rot, expressions

    def start_face_tracking(self, camera_id=0, confidence=0.5, flip_h=True):
        mp = self._get_mediapipe()
        if mp is None:
            self._log("MediaPipe no instalado. pip install mediapipe")
            return False
        if self._face_running:
            self._log("Face tracking ya activo")
            return True

        self._face_camera = camera_id
        self._face_confidence = confidence
        self._face_flip = flip_h
        self._face_running = True

        def run():
            try:
                mp_face_mesh = mp.solutions.face_mesh
                mp_selfie = mp.solutions.selfie_segmentation
                import cv2
                cap = cv2.VideoCapture(camera_id)
                if not cap.isOpened():
                    self._log("No se pudo abrir la cámara")
                    self._face_running = False
                    return

                self._log(f"Cámara {camera_id} abierta")
                with mp_face_mesh.FaceMesh(
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=confidence,
                    min_tracking_confidence=0.5,
                ) as face_mesh, mp_selfie.SelfieSegmentation(
                    model_selection=1,
                ) as selfie_seg:
                    while self._face_running and cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        if flip_h:
                            frame = cv2.flip(frame, 1)
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        results = face_mesh.process(rgb)

                        # Background removal segmentation
                        if hasattr(self, '_bg_removal_callback') and self._bg_removal_callback:
                            seg_results = selfie_seg.process(rgb)
                            if seg_results.segmentation_mask is not None:
                                try:
                                    mask = seg_results.segmentation_mask
                                    self._bg_removal_callback(mask)
                                except Exception as e:
                                    error(f"bg_removal callback: {e}")

                        if results.multi_face_landmarks:
                            landmarks = results.multi_face_landmarks[0]
                            head_rot, exprs = self._face_landmarks_to_expressions(
                                landmarks,
                                frame.shape[1], frame.shape[0]
                            )
                            self._call_tracking_callback(head_rot=head_rot, blendshapes=exprs)
                            # Send viseme landmarks for lip sync
                            if hasattr(self, '_viseme_callback') and self._viseme_callback:
                                try:
                                    vis_lm = [{'x': l.x, 'y': l.y, 'z': l.z} for l in landmarks.landmark]
                                    self._viseme_callback(vis_lm)
                                except Exception as e:
                                    error(f"viseme callback: {e}")
                        else:
                            time.sleep(0.01)
                            continue
                        time.sleep(0.005)
            except Exception as e:
                self._log(f"Face tracking error: {e}")
            finally:
                try:
                    cap.release()
                except Exception:
                    pass
                self._face_running = False
                self._log("Face tracking detenido")

        self._face_thread = threading.Thread(target=run, daemon=True)
        self._face_thread.start()
        self._log("Face tracking iniciado")
        return True

    def stop_face_tracking(self):
        self._face_running = False
        if self._face_thread:
            self._face_thread.join(timeout=2.0)
            self._face_thread = None

    @property
    def face_tracking_active(self):
        return self._face_running

    def get_camera_list(self):
        import cv2
        cameras = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    cameras.append(i)
                cap.release()
        return cameras if cameras else [0]

    # ── Keyboard Tracking ──

    @property
    def keyboard_available(self):
        try:
            import keyboard
            return True
        except ImportError:
            return False

    def start_keyboard_tracking(self):
        if self._keyboard_running:
            return True
        try:
            import keyboard as kb
        except ImportError:
            self._log("keyboard no instalado")
            return False

        self._keyboard_running = True
        self._last_key_expr = {}

        def run():
            while self._keyboard_running:
                try:
                    for key, expr in self._key_to_expression.items():
                        if kb.is_pressed(key):
                            self._last_key_expr = expr
                            self._call_tracking_callback(blendshapes=expr)
                            break
                    else:
                        if self._last_key_expr:
                            zeros = {k: 0.0 for k in self._last_key_expr}
                            self._call_tracking_callback(blendshapes=zeros)
                            self._last_key_expr = {}
                    time.sleep(0.05)
                except Exception:
                    time.sleep(0.1)

        self._keyboard_thread = threading.Thread(target=run, daemon=True)
        self._keyboard_thread.start()
        self._log("Keyboard tracking iniciado")
        return True

    def stop_keyboard_tracking(self):
        self._keyboard_running = False
        if self._keyboard_thread:
            self._keyboard_thread.join(timeout=1.0)
            self._keyboard_thread = None

    @property
    def keyboard_tracking_active(self):
        return self._keyboard_running

    def set_key_expression(self, key, expression_dict):
        self._key_to_expression[key] = expression_dict

    def remove_key_expression(self, key):
        self._key_to_expression.pop(key, None)

    # ── Audio Tracking (Lip Sync) ──

    @property
    def audio_available(self):
        try:
            import sounddevice
            return True
        except ImportError:
            return False

    def start_audio_tracking(self, sensitivity=0.3, device=None):
        if self._audio_running:
            return True
        try:
            import sounddevice as sd
            import numpy as np
        except ImportError:
            self._log("sounddevice no instalado")
            return False

        self._audio_sensitivity = sensitivity
        self._audio_device = device
        self._audio_running = True

        def callback(indata, frames, time_info, status):
            if not self._audio_running:
                raise Exception("stop")
            try:
                rms = float(np.sqrt(np.mean(indata**2)))
                energy = min(1.0, rms * 10 / max(self._audio_sensitivity, 0.01))
                if energy > 0.05:
                    jaw = min(1.0, energy * 1.5)
                    self._call_tracking_callback(blendshapes={"jaw_open": jaw})
                else:
                    self._call_tracking_callback(blendshapes={"jaw_open": 0.0})
            except Exception:
                pass

        def run():
            try:
                self._audio_stream = sd.InputStream(
                    device=device,
                    channels=1,
                    samplerate=16000,
                    callback=callback,
                    blocksize=1024,
                )
                self._audio_stream.start()
                while self._audio_running:
                    time.sleep(0.1)
            except Exception as e:
                self._log(f"Audio tracking error: {e}")
            finally:
                if self._audio_stream:
                    try:
                        self._audio_stream.stop()
                        self._audio_stream.close()
                    except Exception:
                        pass
                    self._audio_stream = None
                self._audio_running = False

        self._audio_thread = threading.Thread(target=run, daemon=True)
        self._audio_thread.start()
        self._log("Audio lip-sync iniciado")
        return True

    def stop_audio_tracking(self):
        self._audio_running = False
        if self._audio_stream:
            try:
                self._audio_stream.stop()
                self._audio_stream.close()
            except Exception:
                pass
            self._audio_stream = None
        if self._audio_thread:
            self._audio_thread.join(timeout=1.0)
            self._audio_thread = None

    @property
    def audio_tracking_active(self):
        return self._audio_running

    def get_audio_devices(self):
        try:
            import sounddevice as sd
            return sd.query_devices()
        except Exception:
            return []

    # ── Gamepad Tracking ──

    @property
    def gamepad_available(self):
        try:
            import inputs
            return True
        except ImportError:
            return False

    def start_gamepad_tracking(self):
        if self._gamepad_running:
            return True
        try:
            from inputs import devices, get_gamepad
        except ImportError:
            self._log("inputs no instalado. pip install inputs")
            return False

        pads = devices.gamepads
        if not pads:
            self._log("No se detectaron gamepads")
            return False

        self._gamepad_running = True

        def run():
            try:
                while self._gamepad_running:
                    events = get_gamepad()
                    expr = {}
                    for e in events:
                        val = max(0.0, min(1.0, abs(e.state) / 32767.0))
                        if e.code == "ABS_RY":
                            expr["brow_raise_left"] = val
                            expr["brow_raise_right"] = val
                        elif e.code == "ABS_Y":
                            expr["jaw_open"] = val
                        elif e.code == "BTN_SOUTH":
                            expr["blink"] = 1.0 if e.state else 0.0
                    if expr:
                        self._call_tracking_callback(blendshapes=expr)
                    time.sleep(0.03)
            except Exception as e:
                self._log(f"Gamepad error: {e}")
            finally:
                self._gamepad_running = False

        self._gamepad_thread = threading.Thread(target=run, daemon=True)
        self._gamepad_thread.start()
        self._log("Gamepad tracking iniciado")
        return True

    def stop_gamepad_tracking(self):
        self._gamepad_running = False
        if self._gamepad_thread:
            self._gamepad_thread.join(timeout=1.0)
            self._gamepad_thread = None

    @property
    def gamepad_tracking_active(self):
        return self._gamepad_running

    # ── Cleanup ──

    def stop_all(self):
        self.stop()
        self.stop_face_tracking()
        self.stop_keyboard_tracking()
        self.stop_audio_tracking()
        self.stop_gamepad_tracking()

    def __del__(self):
        self.stop_all()
