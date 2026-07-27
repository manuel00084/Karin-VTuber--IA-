import sounddevice as sd
import queue
import sys
import json
import os
import threading
from src.utils.log import error, warn
from src import PROJECT_ROOT

VOSK_OK = False
vosk = None
_model = None

MODEL_PATH = os.path.join(PROJECT_ROOT, "vosk-model-small-es-0.42")

def _try_load_vosk():
    global VOSK_OK, vosk
    try:
        import vosk as v
        vosk = v
        VOSK_OK = True
        return True
    except Exception as e:
        warn(f"Vosk not available: {e}")
        return False

def _ensure_vosk():
    global vosk, _model
    if not VOSK_OK:
        _try_load_vosk()
    if VOSK_OK and _model is None and os.path.exists(MODEL_PATH):
        try:
            _model = vosk.Model(MODEL_PATH)
        except Exception as e:
            error(f"Vosk model error: {e}")
            VOSK_OK = False

q = queue.Queue()
_stream_lock = threading.Lock()
stream = None
recognizer = None

def _callback(indata, frames, time, status):
    if status:
        warn(f"STT status: {status}")
    q.put(bytes(indata))


def listen():
    global stream, recognizer, _model
    _ensure_vosk()
    if not VOSK_OK:
        warn("Vosk not available")
        return ""
    if not os.path.exists(MODEL_PATH):
        error(f"Model not found at {MODEL_PATH}")
        return ""

    # Limpiar cola de datos stale
    while not q.empty():
        try: q.get_nowait()
        except Exception: break

    try:
        if _model is None:
            if not os.path.exists(MODEL_PATH):
                error(f"Model path does not exist: {MODEL_PATH}")
                return ""
            _model = vosk.Model(MODEL_PATH)
        recognizer = vosk.KaldiRecognizer(_model, 16000)
        stream = sd.InputStream(samplerate=16000, channels=1, callback=_callback)
        with stream:
            sd.sleep(4000)
        data = b"".join(list(q.queue))
        if data:
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                return result.get("text", "")
            else:
                return ""
        return ""
    except Exception as e:
        error(f"STT Error: {e}")
        return ""
    finally:
        if stream:
            stream.close()
            stream = None


def listen_stream_start(device=None):
    global stream, recognizer, _model
    _ensure_vosk()
    if not VOSK_OK:
        warn("Vosk not available")
        return False
    try:
        if _model is None:
            _model = vosk.Model(MODEL_PATH)
        recognizer = vosk.KaldiRecognizer(_model, 16000)
        stream = sd.InputStream(samplerate=16000, channels=1, device=device, callback=_callback)
        stream.start()
        return True
    except Exception as e:
        error(f"listen_stream_start error: {e}")
        return False


def listen_stream_stop():
    global stream, recognizer
    try:
        if stream:
            stream.stop()
            stream.close()
            stream = None
        data = b"".join(list(q.queue))
        while not q.empty():
            try: q.get_nowait()
            except Exception: break
        if data and recognizer:
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
            else:
                result = json.loads(recognizer.PartialResult())
            return result.get("text", "")
        return ""
    except Exception as e:
        error(f"listen_stream_stop error: {e}")
        return ""
