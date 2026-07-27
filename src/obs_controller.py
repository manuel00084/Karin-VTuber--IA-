import threading, time

_RECONNECT_INTERVAL = 10


class OBSController:
    def __init__(self, log_fn=print):
        self._ws = None
        self._connected = False
        self._lock = threading.Lock()
        self._log = log_fn
        self._host = "localhost"
        self._port = 4455
        self._password = ""
        self.scenes = []
        self.current_scene = ""
        self.recording = False
        self.streaming = False
        self.status = "Desconectado"
        self._wanted = False
        self._reconnect_thread = None

    def config(self, host, port, password):
        self._host = host
        self._port = port
        self._password = password

    def connect(self):
        self._wanted = True
        self._run_connect()
        if not self._connected:
            self._start_reconnect()

    def _run_connect(self):
        with self._lock:
            if self._connected:
                return True
            try:
                from obswebsocket import obsws, requests
                self._ws = obsws(self._host, self._port, self._password, timeout=5)
                self._ws.connect()
                self._connected = True
                self.status = "Conectado"
                self._log(f"[OBS] Conectado a {self._host}:{self._port}")
                self._refresh()
                return True
            except Exception as e:
                self.status = f"Error: {e}"
                self._connected = False
                self._ws = None
                self._log(f"[OBS] Error de conexion: {e}")
                return False

    def _start_reconnect(self):
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _reconnect_loop(self):
        while self._wanted:
            time.sleep(_RECONNECT_INTERVAL)
            with self._lock:
                connected = self._connected
            if connected:
                try:
                    with self._lock:
                        self._refresh()
                except Exception:
                    with self._lock:
                        self._connected = False
            with self._lock:
                still_wanted = self._wanted
                still_connected = self._connected
            if not still_connected and still_wanted:
                self._log("[OBS] Reintentando conexion...")
                self._run_connect()

    def disconnect(self):
        self._wanted = False
        with self._lock:
            if self._ws:
                try:
                    self._ws.disconnect()
                except Exception:
                    pass
            self._ws = None
            self._connected = False
            self.status = "Desconectado"
            self.scenes.clear()
            self._log("[OBS] Desconectado")

    def _refresh(self):
        if not self._connected or not self._ws:
            return
        try:
            from obswebsocket import requests
            r = self._ws.call(requests.GetSceneList())
            if r and r.status:
                self.scenes = r.getScenes()
                self.current_scene = r.getCurrentProgramSceneName() or ""

            r2 = self._ws.call(requests.GetRecordStatus())
            if r2 and r2.status:
                self.recording = r2.getOutputActive()

            r3 = self._ws.call(requests.GetStreamStatus())
            if r3 and r3.status:
                self.streaming = r3.getOutputActive()

            self.status = "Conectado"
        except Exception as e:
            self.status = f"Error: {e}"

    def switch_scene(self, name):
        with self._lock:
            if not self._connected or not self._ws:
                return
            try:
                from obswebsocket import requests
                r = self._ws.call(requests.SetCurrentProgramScene(sceneName=name))
                if r and r.status:
                    self.current_scene = name
                    self._log(f"[OBS] Escena cambiada: {name}")
            except Exception as e:
                self._log(f"[OBS] Error cambiando escena: {e}")

    def toggle_recording(self):
        with self._lock:
            if not self._connected or not self._ws:
                return
            try:
                from obswebsocket import requests
                if self.recording:
                    self._ws.call(requests.StopRecord())
                else:
                    self._ws.call(requests.StartRecord())
                time.sleep(0.3)
                self._refresh()
            except Exception as e:
                self._log(f"[OBS] Error recording: {e}")

    def toggle_streaming(self):
        with self._lock:
            if not self._connected or not self._ws:
                return
            try:
                from obswebsocket import requests
                if self.streaming:
                    self._ws.call(requests.StopStream())
                else:
                    self._ws.call(requests.StartStream())
                time.sleep(0.3)
                self._refresh()
            except Exception as e:
                self._log(f"[OBS] Error streaming: {e}")