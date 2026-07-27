import threading
import queue
import asyncio
import edge_tts
import tempfile
import os
import time

import numpy as np
import sounddevice as sd
import soundfile as sf
from src.utils.log import error, warn
from src.utils.optimize import fast_audio_resample, fast_normalize, fast_clip
from .equalizer import EQ5

audio_queue = queue.Queue()

# Cache de samplerates para evitar sd.query_devices() repetido
_samplerate_cache = {}

# ── Pitch shift (solo monitor) ──
_pitch_semitones = 0
_monitor_device = None
_eq = EQ5()

def set_pitch(semitones):
    global _pitch_semitones
    _pitch_semitones = max(-12, min(12, semitones))

def set_monitor_device(device_id):
    global _monitor_device
    _monitor_device = device_id

def set_eq_gain(band, db):
    _eq.gains[band] = max(-12, min(12, db))
    _eq._dirty = True

def _pitch_shift(data, semitones):
    if semitones == 0:
        return data
    n = int(len(data) * (2 ** (-semitones / 12)))
    n = max(1, min(n, len(data) * 4))
    return np.interp(np.linspace(0, len(data), n), np.arange(len(data)), data).astype(np.float32)

# ── Coordinador de audio ──
_is_speaking = False
_active_streams = 0
_speaking_lock = threading.Lock()
_last_play_time = 0
SPEAK_COOLDOWN = 1.5  # segundos mínimo entre reproducciones de distinto origen


def is_busy():
    """Retorna True si hay audio reproduciéndose actualmente."""
    with _speaking_lock:
        return _active_streams > 0


def was_recently_playing(seconds=2.0):
    """Retorna True si se reprodujo audio en los últimos X segundos."""
    with _speaking_lock:
        return (time.time() - _last_play_time) < seconds


def _set_speaking(val):
    global _is_speaking, _last_play_time, _active_streams
    with _speaking_lock:
        if val:
            _active_streams += 1
            _is_speaking = True
            _last_play_time = time.time()
        else:
            _active_streams = max(0, _active_streams - 1)
            _is_speaking = _active_streams > 0


def get_device_samplerate(device):
    if device in _samplerate_cache:
        return _samplerate_cache[device]
    try:
        info = sd.query_devices(device, 'output')
        rate = int(info['default_samplerate'])
        _samplerate_cache[device] = rate
        return rate
    except Exception:
        return 48000


async def _generar_tts(text, voice, path):
    emocion = detectar_emocion(text)
    rate, pitch = "+0%", "+0Hz"
    if emocion == "feliz":
        rate, pitch = "+15%", "+6Hz"
    elif emocion == "enojado":
        rate, pitch = "-5%", "-4Hz"
    elif emocion == "sorpresa":
        rate, pitch = "+10%", "+8Hz"
    elif emocion == "triste":
        rate, pitch = "-10%", "-2Hz"
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await communicate.save(path)


# ===== DETECCION DE EMOCION =====
def detectar_emocion(texto):
    t = texto.lower()
    if any(p in t for p in ["jaja", "genial", "feliz", "emocion", "divertido"]):
        return "feliz"
    elif any(p in t for p in ["enojo", "molesto", "odio", "rabia"]):
        return "enojado"
    elif any(p in t for p in ["wow", "sorpresa", "increible", "no puede ser"]):
        return "sorpresa"
    elif any(p in t for p in ["triste", "lo siento", "perdon"]):
        return "triste"
    return "normal"


def resample_audio(data, src_rate, dst_rate):
    if src_rate == dst_rate:
        return data
    return fast_audio_resample(data, src_rate, dst_rate)


def _play_on_device(data, src_fs, device, volume=1.0):
    """Reproduce audio en un dispositivo (con remuestreo si hace falta)."""
    _set_speaking(True)
    try:
        d = data.copy()
        d = fast_normalize(d, 0.85)
        d = d * volume
        dev_rate = get_device_samplerate(device)
        d = fast_audio_resample(d, src_fs, dev_rate) if src_fs != dev_rate else d
        if d.ndim > 1 and d.shape[1] > 1:
            d = np.mean(d, axis=1)
        if _pitch_semitones and device == _monitor_device:
            d = _pitch_shift(d, _pitch_semitones)
        if device == _monitor_device:
            d = _eq.process(d)
        d = fast_clip(d, 0.99)
        try:
            sd.play(d, dev_rate, device=device, blocking=True)
        except Exception as e1:
            warn(f"Retrying device {device} at 48000Hz: {e1}")
            d2 = data.copy()
            d2 = fast_normalize(d2, 0.6) * volume
            d2 = fast_audio_resample(d2, src_fs, 48000)
            if d2.ndim > 1 and d2.shape[1] > 1:
                d2 = np.mean(d2, axis=1)
            if _pitch_semitones and device == _monitor_device:
                d2 = _pitch_shift(d2, _pitch_semitones)
            if device == _monitor_device:
                d2 = _eq.process(d2)
            d2 = fast_clip(d2, 0.99)
            sd.play(d2, 48000, device=device, blocking=True)
    except Exception as e:
        error(f"playing in device {device}: {e}")
    finally:
        _set_speaking(False)


# ===== WORKER =====
def audio_worker():
    while True:
        try:
            text, voice, devices, volume = audio_queue.get()

            # normaliza: puede llegar un int o una lista
            if isinstance(devices, (list, tuple)):
                dev_list = list(devices)
            else:
                dev_list = [devices]

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                path = f.name

            try:
                asyncio.run(_generar_tts(text, voice, path))
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(_generar_tts(text, voice, path))
                finally:
                    loop.close()

            try:
                data, fs = sf.read(path, dtype='float32')
                
                import threading
                threads = []
                for dev in dev_list:
                    if dev is None or dev == -1:
                        continue
                    t = threading.Thread(target=_play_on_device, args=(data, fs, dev, volume), daemon=True)
                    t.start()
                    threads.append(t)
                for t in threads:
                    t.join()
            except Exception as e:
                error(f"playing audio: {e}")

            try:
                os.remove(path)
            except Exception:
                pass

        except Exception as e:
            error(f"Worker error: {e}")


def stop_audio():
    try:
        sd.stop()
    except Exception:
        pass
    _set_speaking(False)


def speak(text, voice="es-ES-AlvaroNeural", device=None, volume=1.0):
    """device puede ser int (un dispositivo) o lista [dev1, dev2, ...]."""
    try:
        audio_queue.put((text, voice, device, volume))
    except Exception as e:
        error(f"speak: {e}")


def play_file(path, device=None):
    """Reproduce un archivo de audio (MP3/WAV/OGG) directamente"""
    if not path or not os.path.isfile(path):
        error(f"play_file: archivo no encontrado: {path}")
        return
    try:
        data, fs = sf.read(path, dtype='float32')
    except Exception as e:
        error(f"play_file sf.read: {e}")
        try:
            import subprocess
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", path],
                check=True
            )
            return
        except Exception as e2:
            error(f"play_file ffplay fallback: {e2}")
            return
    _play_on_device(data, fs, device)