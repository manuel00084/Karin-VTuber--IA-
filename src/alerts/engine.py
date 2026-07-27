import threading, time
from src.alerts.overlay import AlertOverlay
from src.alerts.event_poller import TwitchEventPoller
from src.core.config import load_config


class AlertEngine:
    def __init__(self, log_fn=print):
        self.overlay = AlertOverlay()
        self._log = log_fn
        self._running = False
        self._thread = None
        self._poller = TwitchEventPoller("", "", "", log_fn=log_fn)
        self._interval = 15
        self._poll_follows = True
        self._poll_subs = False
        self._broadcaster_id = ""

    def start(self):
        if self._running:
            return
        self._running = True
        self._load_config()
        self.overlay.show()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log("✅  Alertas iniciadas")

    def stop(self):
        self._running = False
        self.overlay.destroy()
        self._log("⏹  Alertas detenidas")

    def _load_config(self):
        cfg = load_config()
        self.overlay.set_duration(int(cfg.get("ALERT_DURATION", 6)))
        self.overlay.set_opacity(float(cfg.get("ALERT_OPACITY", 0.9)))
        self.overlay.set_sound_enabled(cfg.get("ALERT_SOUND", "1") == "1")
        self._interval = int(cfg.get("ALERT_INTERVAL", 15))
        self._poll_follows = cfg.get("ALERT_POLL_FOLLOWS", "1") == "1"
        self._poll_subs = cfg.get("ALERT_POLL_SUBS", "0") == "1"

        # Cargar rutas de sonido personalizadas
        sound_paths = {}
        for ev in ("follow", "sub", "resub", "bit", "raid", "donation"):
            key = f"ALERT_SOUND_{ev.upper()}"
            val = cfg.get(key, "")
            if val:
                sound_paths[ev] = val
        self.overlay.set_sound_paths(sound_paths)

        token = cfg.get("TWITCH_TOKEN", "")
        client_id = cfg.get("TWITCH_CLIENT_ID", "")
        nick = cfg.get("NICK", "")
        if token and client_id and nick:
            self._broadcaster_id = self._resolve_id(token, client_id, nick)
            self._poller.set_credentials(token, client_id, self._broadcaster_id)

    def _resolve_id(self, token, client_id, nick):
        try:
            import requests
            r = requests.get(
                "https://api.twitch.tv/helix/users",
                params={"login": nick},
                headers={"Authorization": f"Bearer {token}", "Client-Id": client_id},
                timeout=10,
            )
            data = r.json().get("data", [])
            if data:
                return data[0]["id"]
        except Exception:
            pass
        return ""

    def _loop(self):
        while self._running:
            try:
                self._load_config()
                if self._poll_follows and self._broadcaster_id:
                    events = self._poller.check_follows(self._broadcaster_id)
                    for ev in events:
                        self.overlay.queue_alert(**ev)
            except Exception as e:
                self._log(f"⚠  Alert loop error: {e}")
            time.sleep(self._interval)

    def test_alert(self, event_type="follow", username="Viewer"):
        self.overlay.queue_alert(event_type, username, message="Gracias por el apoyo!", months=6, bits=100, viewers=5)
        self._log(f"🧪  Alerta de prueba: {event_type} - {username}")
