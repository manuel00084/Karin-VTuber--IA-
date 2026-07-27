import threading
import asyncio
import time
import discord
from discord.ext import commands

from src.utils.log import error, info

_bot_instance = None
_bot_thread = None
_bot_loop = None
_running = False
_message_handler = None
_ready_callback = None


class _DiscordBot(commands.Bot):
    def __init__(self, token, text_channel_id, voice_channel_id, log_fn):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self._token = token
        self._text_channel_id = text_channel_id
        self._voice_channel_id = voice_channel_id
        self._log = log_fn
        self._vc = None

    async def on_ready(self):
        self._log(f"✅ Discord conectado como {self.user}")
        # Join voice channel if configured
        if self._voice_channel_id:
            await self._join_voice()

    async def _join_voice(self):
        try:
            ch = self.get_channel(self._voice_channel_id)
            if ch and isinstance(ch, discord.VoiceChannel):
                self._vc = await ch.connect()
                self._log(f"🔊 Conectado a canal de voz: {ch.name}")
        except Exception as e:
            self._log(f"⚠ Error al conectar a voz: {e}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if message.channel.id != self._text_channel_id:
            return
        if _message_handler:
            content = message.content
            author = message.author.display_name
            try:
                response = _message_handler(author, content)
                if response:
                    await message.channel.send(response)
                    # Speak in voice if connected
                    if self._vc and self._vc.is_connected():
                        await self._speak(response)
            except Exception as e:
                self._log(f"⚠ Discord on_message error: {e}")

    async def _speak(self, text):
        """Speak text in voice channel via TTS."""
        try:
            import tempfile, os
            from src.audio.audio import play_file
            import edge_tts
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                path = f.name
            communicate = edge_tts.Communicate(text=text, voice="es-MX-DaliaNeural")
            await communicate.save(path)
            # Play via Discord voice
            if self._vc and self._vc.is_connected():
                self._vc.play(discord.FFmpegPCMAudio(path), after=lambda e: None)
                while self._vc.is_playing():
                    await asyncio.sleep(0.1)
            try:
                os.remove(path)
            except Exception:
                pass
        except Exception as e:
            self._log(f"⚠ Error en TTS Discord: {e}")

    async def send_text(self, text):
        try:
            ch = self.get_channel(self._text_channel_id)
            if ch:
                await ch.send(text)
        except Exception:
            pass

    async def send_voice_speak(self, text):
        if self._vc and self._vc.is_connected():
            await self._speak(text)

    async def disconnect_voice(self):
        if self._vc:
            await self._vc.disconnect()
            self._vc = None
            self._log("🔊 Desconectado de canal de voz")


def _run_bot(token, text_cid, voice_cid, log_fn):
    global _bot_instance, _bot_loop, _running
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _bot_loop = loop

        bot = _DiscordBot(token, text_cid, voice_cid, log_fn)
        _bot_instance = bot
        _running = True

        if _ready_callback:
            _ready_callback()

        loop.run_until_complete(bot.start(token))
    except Exception as e:
        log_fn(f"❌ Discord bot error: {e}")
    finally:
        _running = False
        _bot_instance = None


def start_bot(token, text_channel_id, voice_channel_id, log_fn=print,
              message_handler=None, ready_callback=None):
    """Start Discord bot in background thread."""
    global _bot_thread, _message_handler, _ready_callback, _running
    if _running:
        log_fn("⚠ Discord bot ya está en ejecución")
        return False

    _message_handler = message_handler
    _ready_callback = ready_callback

    _bot_thread = threading.Thread(
        target=_run_bot,
        args=(token, text_channel_id, voice_channel_id, log_fn),
        daemon=True,
    )
    _bot_thread.start()
    log_fn("🔵 Conectando Discord...")
    return True


def stop_bot():
    global _running, _bot_instance
    _running = False
    if _bot_instance and _bot_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _bot_instance.close(), _bot_loop
            )
        except Exception:
            pass
    _bot_instance = None
    return True


def is_running():
    return _running


def send_message(text):
    """Send text to Discord text channel."""
    if _bot_instance and _bot_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _bot_instance.send_text(text), _bot_loop
            )
            return True
        except Exception:
            pass
    return False


def send_voice(text):
    """Speak text in Discord voice channel."""
    if _bot_instance and _bot_loop:
        try:
            asyncio.run_coroutine_threadsafe(
                _bot_instance.send_voice_speak(text), _bot_loop
            )
            return True
        except Exception:
            pass
    return False
