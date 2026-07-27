import requests, time


class TwitchEventPoller:
    def __init__(self, token, client_id, channel_id, log_fn=print):
        self._token = token
        self._client_id = client_id
        self._channel_id = channel_id
        self._log = log_fn
        self._last_follow_check = time.time()
        self._known_followers = set()

    def set_credentials(self, token, client_id, channel_id):
        self._token = token
        self._client_id = client_id
        self._channel_id = channel_id

    def check_follows(self, broadcaster_id):
        if not self._token or not self._client_id or not broadcaster_id:
            return []
        try:
            r = requests.get(
                "https://api.twitch.tv/helix/channels/followers",
                params={"broadcaster_id": broadcaster_id, "first": 10},
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Client-Id": self._client_id,
                },
                timeout=10,
            )
            if r.status_code != 200:
                self._log(f"⚠  Follows API error: {r.status_code}")
                return []
            data = r.json().get("data", [])
            new_events = []
            for f in data:
                uid = f.get("user_id", "")
                name = f.get("user_name", f.get("user_login", "?"))
                if uid and uid not in self._known_followers:
                    self._known_followers.add(uid)
                    followed_at = f.get("followed_at", "")
                    if followed_at:
                        ft = time.strptime(followed_at.split(".")[0], "%Y-%m-%dT%H:%M:%S")
                        if time.mktime(ft) > self._last_follow_check - 60:
                            new_events.append({"type": "follow", "username": name})
            self._last_follow_check = time.time()
            return new_events
        except requests.exceptions.ConnectionError:
            return []
        except Exception as e:
            self._log(f"⚠  Follows poll error: {e}")
            return []

    def check_subs(self, broadcaster_id):
        if not self._token or not self._client_id or not broadcaster_id:
            return []
        try:
            r = requests.get(
                "https://api.twitch.tv/helix/subscriptions",
                params={"broadcaster_id": broadcaster_id, "first": 10},
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Client-Id": self._client_id,
                },
                timeout=10,
            )
            if r.status_code == 403:
                return []
            if r.status_code != 200:
                return []
            return r.json().get("data", [])
        except Exception:
            return []
