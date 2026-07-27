import sqlite3, os, time, threading
from src import PROJECT_ROOT
from src.utils.log import info, error
from src.kste.parser.message_parser import ChatMessage, ChatChannel

_DB_DIR = os.path.join(PROJECT_ROOT, "data")
_DB_PATH = os.path.join(_DB_DIR, "kste_history.db")


class ConversationMemory:
    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        try:
            os.makedirs(_DB_DIR, exist_ok=True)
            conn = sqlite3.connect(self._DB_PATH, check_same_thread=False)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jugador TEXT NOT NULL,
                    texto TEXT NOT NULL,
                    traduccion TEXT DEFAULT '',
                    canal TEXT DEFAULT 'general',
                    idioma TEXT DEFAULT 'unknown',
                    timestamp REAL NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_jugador ON messages(jugador)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp)"
            )
            conn.commit()
            conn.close()
        except Exception as e:
            error(f"KSTE memory init: {e}")

    def save(self, message, translation=""):
        with self._lock:
            try:
                conn = sqlite3.connect(_DB_PATH)
                conn.execute(
                    "INSERT INTO messages (jugador, texto, traduccion, canal, idioma, timestamp) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        message.jugador,
                        message.texto,
                        translation,
                        message.canal.value if hasattr(message.canal, 'value') else str(message.canal),
                        message.idioma,
                        message.timestamp or time.time(),
                    )
                )
                conn.commit()
                conn.close()
            except Exception as e:
                error(f"KSTE memory save: {e}")

    def get_recent(self, player, n=10):
        with self._lock:
            try:
                conn = sqlite3.connect(_DB_PATH)
                cursor = conn.execute(
                    "SELECT jugador, texto, traduccion, canal, idioma, timestamp "
                    "FROM messages WHERE jugador = ? ORDER BY timestamp DESC LIMIT ?",
                    (player, n)
                )
                rows = cursor.fetchall()
                conn.close()
                messages = []
                for row in reversed(rows):
                    try:
                        canal = ChatChannel(row[3])
                    except (ValueError, KeyError):
                        canal = ChatChannel.GENERAL
                    messages.append(ChatMessage(
                        jugador=row[0],
                        texto=row[1],
                        canal=canal,
                        idioma=row[4],
                        timestamp=row[5],
                        traduccion=row[2],
                    ))
                return messages
            except Exception as e:
                error(f"KSTE memory get_recent: {e}")
                return []

    def search(self, query, limit=50):
        with self._lock:
            try:
                conn = sqlite3.connect(_DB_PATH)
                cursor = conn.execute(
                    "SELECT jugador, texto, traduccion, canal, idioma, timestamp "
                    "FROM messages WHERE texto LIKE ? OR traduccion LIKE ? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (f"%{query}%", f"%{query}%", limit)
                )
                rows = cursor.fetchall()
                conn.close()
                messages = []
                for row in rows:
                    try:
                        canal = ChatChannel(row[3])
                    except (ValueError, KeyError):
                        canal = ChatChannel.GENERAL
                    messages.append(ChatMessage(
                        jugador=row[0],
                        texto=row[1],
                        canal=canal,
                        idioma=row[4],
                        timestamp=row[5],
                        traduccion=row[2],
                    ))
                return messages
            except Exception as e:
                error(f"KSTE memory search: {e}")
                return []

    def cleanup(self, max_days=None):
        if max_days is None:
            max_days = self.config.history_max_days
        cutoff = time.time() - (max_days * 86400)
        with self._lock:
            try:
                conn = sqlite3.connect(_DB_PATH)
                cursor = conn.execute(
                    "DELETE FROM messages WHERE timestamp < ?", (cutoff,)
                )
                deleted = cursor.rowcount
                conn.commit()
                conn.close()
                if deleted > 0:
                    info(f"KSTE memory cleanup: {deleted} old messages removed")
            except Exception as e:
                error(f"KSTE memory cleanup: {e}")

    def count(self, player=None):
        with self._lock:
            try:
                conn = sqlite3.connect(_DB_PATH)
                if player:
                    cursor = conn.execute(
                        "SELECT COUNT(*) FROM messages WHERE jugador = ?", (player,)
                    )
                else:
                    cursor = conn.execute("SELECT COUNT(*) FROM messages")
                result = cursor.fetchone()[0]
                conn.close()
                return result
            except Exception:
                return 0
