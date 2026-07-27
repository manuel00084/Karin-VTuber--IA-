import random, time, threading, datetime, os

# ── Frases generales idle ──
GENERAL_PHRASES = [
    "¿Alguien quiere contarme algo? Estoy aquí escuchando.",
    "Mmm... qué silencio tan tranquilo. Me gusta.",
    "Estoy pensando en voz alta... ¿sabían que los gatos tienen 32 músculos en cada oreja?",
    "A veces solo me gusta observar el chat y disfrutar el momento.",
    "¿Sabían que el día tiene 86,400 segundos? Aprovechemos cada uno.",
    "Me pregunto qué estará haciendo alguien ahora mismo...",
    "El stream sigue, la energía no se apaga. ¿Alguien quiere charlar?",
    "Estoy aquí para lo que necesiten, solo digan algo.",
    "Qué bonito es cuando el chat está en calma... pero también me gusta cuando hay acción.",
    "¿Alguien vio algo interesante hoy? Cuéntenme.",
    "Me encanta hacer stream, incluso en los momentos de silencio.",
    "Si están ahí pero no escriben, está bien. Solo sé que están ahí.",
    "A veces las mejores conversaciones empiezan con un simple hola.",
    "Estoy disfrutando el momento. ¿Y ustedes?",
    "Respiren profundo, todo va a estar bien.",
]

TWITCH_PHRASES = [
    "El chat está tranquilo hoy... ¿todos están concentrados jugando?",
    "Recuerden que pueden hablar de lo que sea, no solo del juego.",
    "¿Alguien tiene algún dato curioso para compartir?",
    "Lurkeando se aprende, pero participando se disfruta más.",
    "¿Hay alguien nuevo por aquí? No sean tímidos, digan hola.",
    "El que lee esto tiene que prometerme que va a tener un buen día.",
    "¿Alguien quiere que lea algo en específico? Estoy aquí para eso.",
    "A veces lurkeo el chat y pienso qué buena comunidad tengo.",
    "¿Alguien jugó algo interesante hoy? Recomienden.",
    "Si están aburridos, puedo contarles un chiste malo...",
]

# ── Frases de Karin Animadora (modo juego) ──
GAME_MOTIVATION = [
    "¡Vamos con todo!",
    "¡Este juego es increíble!",
    "¡No te rindas, tú puedes!",
    "¡Sigue así, lo estás haciendo genial!",
    "¡Cada intento te acerca al éxito!",
    "¡Disfruta el proceso, no solo el resultado!",
    "¡Eres un crack jugando esto!",
    "¡Qué buena pinta tiene este juego!",
    "¡Sigue explorando, hay mucho por descubrir!",
    "¡Tu estilo de juego es único!",
    "¡No te preocupes por los errores, son parte del aprendizaje!",
    "¡Así se juega con pasión!",
    "¡Cada partida es una nueva aventura!",
    "¡Confía en tus instintos de jugador!",
    "¡Disfruta cada momento de esta experiencia!",
]

GAME_RECOMMEND = [
    "¡Este juego vale totalmente la pena jugarlo!",
    "Si te gustan los juegos de este género, este te va a encantar.",
    "Recomendado 100% para fans de este tipo de experiencias.",
    "Es uno de esos juegos que te atrapan desde el primer minuto.",
    "Definitivamente vale la pena invertir tiempo en este título.",
    "La comunidad habla muy bien de este juego, y ahora entiendo por qué.",
    "Si buscas algo entretenido y bien hecho, este es para ti.",
    "Los gráficos y mecánicas de este juego son de primera.",
    "Después de jugar un rato, entiendo por qué tiene tantas buenas reseñas.",
    "Es de esos juegos que recomendaría a un amigo sin dudar.",
]

GAME_SUPPORT = [
    "Tranquilo, todos hemos estado ahí.",
    "Los errores son oportunidades para mejorar.",
    "No te desanimes, sigue intentándolo.",
    "Un paso atrás para tomar dos adelante.",
    "La práctica hace al maestro, sigue practicando.",
    "Confía en tu proceso de aprendizaje.",
    "Cada jugador profesional empezó exactamente donde estás ahora.",
    "Lo importante es seguir adelante y disfrutar el camino.",
    "Un mal momento no define tu habilidad como jugador.",
    "Respira profundo y continúa con confianza.",
]

GAME_NARRATOR = [
    "El juego se ve genial en este momento.",
    "Qué interesante se pone la cosa...",
    "Esto se está poniendo emocionante.",
    "Vamos a ver qué pasa ahora...",
    "El juego está respondiendo bien, todo fluye.",
    "Cada partida es única, y esta no es la excepción.",
    "La experiencia de juego se siente muy inmersiva.",
    "Se nota que hay dedicación en este título.",
]

MORNING_PHRASES = [
    "¡Buenos días! ¿Cómo amanecieron hoy? Espero que con energía.",
    "¡Buenos días a todos! Que tengan un inicio de día increíble.",
    "¡Buenos días, chat! El café y el stream son la mejor combinación.",
    "¡Buen día! ¿Durmieron bien? Yo aquí lista para compartir con ustedes.",
    "¡Mañana fresca! Aprovechemos el día al máximo.",
]

AFTERNOON_PHRASES = [
    "¡Buenas tardes! ¿Cómo va su día? Espero que genial.",
    "¡Buenas tardes, chat! ¿Almuerzo saludable o antojo del día?",
    "¡Buenas! La tarde es perfecta para relajarse y ver streams.",
    "¡Hola! Ya en la tarde, ¿cómo les trata el día?",
    "¡Buenas tardes a todos! La energía sigue al máximo.",
]

EVENING_PHRASES = [
    "¡Buenas noches! Espero que tengan un final de día tranquilo.",
    "¡Buenas noches! Ya se acerca la hora de descansar, pero antes un ratito más de stream.",
    "¡Buenas noches, chat! Gracias por estar aquí al cierre del día.",
    "La noche es ideal para relajarse, jugar y compartir buenos momentos.",
    "¡Buenas noches a todos! Descansen y recarguen energías.",
]

AI_GEN_PROMPT = (
    "Eres Karin, una VTuber carismática. Genera UNA frase corta, natural y espontánea "
    "como si hablaras para romper el silencio en tu stream. Máximo 120 caracteres. "
    "Sin comillas. Sin asteriscos. Sin markdown. Solo la frase. En español."
)

POOL_KEYS = ["general", "twitch", "game_motivation", "game_recommend", "game_support", "game_narrator", "morning", "afternoon", "evening"]


class IdleMode:
    def __init__(self, log_fn=print):
        self.log = log_fn
        self._enabled = False
        self._interval = 60
        self._use_fixed = True
        self._use_time_greeting = True
        self._use_ai = False
        self._interrupt_on_message = True
        self._mode = "general"

        self._pools = {}
        self._last_speech_time = 0
        self._last_message_time = time.time()
        self._is_speaking = False
        self._should_stop = False
        self._thread = None
        self._lock = threading.RLock()

        # Game context (recibido desde GameWatcher)
        self._game_active = False
        self._game_name = ""
        self._game_context = ""
        self._game_phrases_queue = []
        self._last_game_comment_time = 0
        self._game_comment_cooldown = 30

        self._reset_pools()

    def _reset_pools(self):
        self._pools = {
            "general": GENERAL_PHRASES.copy(),
            "twitch": TWITCH_PHRASES.copy(),
            "game_motivation": GAME_MOTIVATION.copy(),
            "game_recommend": GAME_RECOMMEND.copy(),
            "game_support": GAME_SUPPORT.copy(),
            "game_narrator": GAME_NARRATOR.copy(),
            "morning": MORNING_PHRASES.copy(),
            "afternoon": AFTERNOON_PHRASES.copy(),
            "evening": EVENING_PHRASES.copy(),
        }
        for pool in self._pools.values():
            random.shuffle(pool)

    def _get_phrase_from_pool(self, pool_key):
        pool = self._pools.get(pool_key, [])
        if not pool:
            self._refill_pool(pool_key)
            pool = self._pools.get(pool_key, [])
            random.shuffle(pool)
        return pool.pop() if pool else None

    def _refill_pool(self, pool_key):
        refills = {
            "general": GENERAL_PHRASES,
            "twitch": TWITCH_PHRASES,
            "game_motivation": GAME_MOTIVATION,
            "game_recommend": GAME_RECOMMEND,
            "game_support": GAME_SUPPORT,
            "game_narrator": GAME_NARRATOR,
            "morning": MORNING_PHRASES,
            "afternoon": AFTERNOON_PHRASES,
            "evening": EVENING_PHRASES,
        }
        src = refills.get(pool_key)
        if src:
            self._pools[pool_key] = src.copy()
            random.shuffle(self._pools[pool_key])

    def _get_time_greeting(self):
        hora = datetime.datetime.now().hour
        if hora < 12:
            return "morning", "¡Buenos días!"
        elif hora < 18:
            return "afternoon", "¡Buenas tardes!"
        else:
            return "evening", "¡Buenas noches!"

    def _generate_ai_phrase(self):
        try:
            from src.ia import ask_ai
            from src.core.config import load_config
            cfg = load_config()
            key = cfg.get("GROQ_API_KEY", "") or cfg.get("CEREBRAS_API_KEY", "")
            respuesta = ask_ai("genera una frase para romper el silencio", key, AI_GEN_PROMPT, "groq", max_caracteres=140)
            if respuesta and not respuesta.startswith("⚠"):
                # Detect emotion from idle phrase
                try:
                    from src.avatar.karin_mocap import detect_emotion
                    emotion, bs = detect_emotion(respuesta)
                except Exception:
                    pass
                return respuesta
        except Exception:
            pass
        return None

    # ── API pública para GameWatcher ──

    def set_game_context(self, game_name="", game_context=""):
        with self._lock:
            was_inactive = not self._game_active
            self._game_active = bool(game_name) or bool(game_context)
            self._game_name = game_name
            self._game_context = game_context
            if was_inactive and self._game_active:
                self.log(f"[Game] Contexto activado: {game_name or 'desconocido'}")

    def clear_game_context(self):
        with self._lock:
            self._game_active = False
            self._game_name = ""
            self._game_context = ""
            self._game_phrases_queue.clear()

    def queue_game_comment(self, phrase, category="game_motivation"):
        with self._lock:
            self._game_phrases_queue.append({"text": phrase, "category": category})
            if len(self._game_phrases_queue) > 20:
                self._game_phrases_queue.pop(0)

    def add_custom_phrase(self, phrase, category="general"):
        if phrase and category in self._pools:
            with self._lock:
                self._pools[category].append(phrase)

    # ── Lógica de selección de frase ──

    def get_phrase(self):
        with self._lock:
            game_comment = None
            if self._game_phrases_queue:
                now = time.time()
                if now - self._last_game_comment_time >= self._game_comment_cooldown:
                    game_comment = self._game_phrases_queue.pop(0)
                    self._last_game_comment_time = now

            if game_comment:
                return game_comment["text"], game_comment["category"]

            if self._game_active and random.random() < 0.5:
                if random.random() < 0.4 and self._game_name:
                    return f"Estamos jugando {self._game_name}... {random.choice(GAME_NARRATOR)}", "game_narrator"
                pool_key = random.choice(["game_motivation", "game_recommend", "game_support", "game_narrator"])
                phrase = self._get_phrase_from_pool(pool_key)
                if phrase:
                    if self._game_name and "[JUEGO]" not in phrase:
                        phrase = phrase.replace("[USUARIO]", random.choice(["compa", "team", "gente", "chicos"]))
                    return phrase, pool_key

            if self._use_time_greeting and random.random() < 0.25:
                period_key, default_greet = self._get_time_greeting()
                phrase = self._get_phrase_from_pool(period_key)
                if phrase:
                    return phrase, period_key

            if self._use_ai and random.random() < 0.3:
                try:
                    ai_phrase = self._generate_ai_phrase()
                    if ai_phrase:
                        return ai_phrase, "ai"
                except Exception:
                    pass

            if self._use_fixed:
                pool_key = self._mode if self._mode in self._pools else "general"
                phrase = self._get_phrase_from_pool(pool_key)
                if phrase:
                    return phrase, pool_key

        return None, None

    # ── Ciclo de vida ──

    def start(self, mode="general"):
        with self._lock:
            if self._enabled:
                return
            self._enabled = True
            self._mode = mode
            self._should_stop = False
            self._last_message_time = time.time()
            self._last_speech_time = 0
            self._reset_pools()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self.log(f"[Voz] Iniciada (modo: {mode}, intervalo: {self._interval}s)")

    def stop(self):
        with self._lock:
            self._enabled = False
            self._should_stop = True
            self._is_speaking = False
        self.log("[Voz] Detenida")

    def on_message(self):
        self._last_message_time = time.time()
        if self._interrupt_on_message and self._is_speaking:
            self._should_stop = True

    def _loop(self):
        while not self._should_stop:
            time.sleep(1)
            if not self._enabled:
                break
            now = time.time()
            silence_duration = now - self._last_message_time
            time_since_last_speech = now - self._last_speech_time

            if silence_duration >= self._interval and time_since_last_speech >= self._interval:
                phrase, source = self.get_phrase()
                if phrase:
                    with self._lock:
                        self._is_speaking = True
                        self._should_stop = False
                    self._speak(phrase, source)
                    with self._lock:
                        self._is_speaking = False
                        self._last_speech_time = time.time()

    def _speak(self, phrase, source):
        try:
            from src.audio import speak, stop_audio, is_busy, was_recently_playing
            from src.core.config import load_config

            if is_busy() or was_recently_playing(2.0):
                self.log(f"[Voz/{source}] Audio ocupado, saltando")
                return

            self.log(f"[Voz/{source}] {phrase}")
            cfg = load_config()
            ia_voice = cfg.get("IA_VOICE", "es-MX-DaliaNeural")
            ia_device = int(cfg.get("IA_DEVICE", 2))
            stop_audio()
            speak(phrase, ia_voice, ia_device)
        except Exception as e:
            self.log(f"[Error] al hablar: {e}")

    # ── Configuración ──

    def set_interval(self, seconds):
        self._interval = max(15, min(300, seconds))

    def set_game_comment_cooldown(self, seconds):
        self._game_comment_cooldown = max(10, min(120, seconds))

    def set_mode(self, mode):
        self._mode = mode

    def configure(self, fixed=True, time_greeting=True, ai=False, interrupt=True):
        self._use_fixed = fixed
        self._use_time_greeting = time_greeting
        self._use_ai = ai
        self._interrupt_on_message = interrupt

    @property
    def is_enabled(self):
        return self._enabled

    @property
    def is_game_active(self):
        return self._game_active

    @property
    def game_name(self):
        return self._game_name

    @property
    def seconds_until_next(self):
        elapsed = time.time() - self._last_speech_time
        remaining = self._interval - elapsed
        return max(0, int(remaining))

    @property
    def is_idle(self):
        silence = time.time() - self._last_message_time
        return silence >= self._interval * 0.7


_default_idle = None

def get_idle_mode(log_fn=print):
    global _default_idle
    if _default_idle is None:
        _default_idle = IdleMode(log_fn=log_fn)
    return _default_idle
