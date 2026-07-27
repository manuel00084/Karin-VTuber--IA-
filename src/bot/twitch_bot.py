import asyncio
import threading
import random
import time
import os

from twitchio.ext import commands
from src.audio import speak, stop_audio, play_file
from src.ia import ask_ai
from src.utils.game_launcher import handle_command, list_games
from src.utils.custom_commands import execute as exec_custom_cmd
from src.utils.moderation import check_message, get_timeout_seconds, get_default_action
from src.utils.command_perms import check_role, has_permission
from src.utils.stream_tools import (
    quote_add, quote_get, quote_count,
    raffle_open, raffle_close, raffle_enter, raffle_pick, raffle_count, raffle_is_active,
    gqueue_join, gqueue_leave, gqueue_pick, gqueue_list,
    schedule_format,
    note_set, note_get,
    keyword_add, keyword_remove, keyword_check, keyword_list,
    linkblock_check, linkblock_get_whitelist, linkblock_get_action,
    songreq_enqueue, songreq_dequeue, songreq_list, songreq_clear, songreq_download, songreq_play,
    so_is_enabled,
)
from src.utils.chat_translator import auto_translate, user_langs, is_spanish, translate
from src.core.config import load_config as _load_cfg
from src.ia.cache import cached_ask_ai

from src.ia.memory import (
    load_memory, save_memory, add_message,
    get_context, update_mood
)
from src.ia.vector_memory import add_to_memory, get_memory_context
from src.ia.chat_learning import get_chat_learning, get_style_adjustment
from src.ia.idle_mode import get_idle_mode
from src.utils.game_watcher import update_ultima_vez_ia_chat, update_ultima_vez_bot_chat

twitch_messages_buffer = []
chat_viewer_queue = []
_chat_ia_counter = 0
_chat_ia_lock = threading.Lock()
_mem_lock = threading.Lock()
_bot_instance = None
_bot_loop = None

# Comandos registrados por plugins
_plugin_commands = {}

def _registrar_comando_plugin(comando, callback):
    _plugin_commands[comando.lower()] = callback

# Rich chat messages for the chat viewer
CHAT_VIEWER_MAX = 200
TWITCH_BUFFER_MAX = 500


def get_chat_viewer_messages():
    msgs = chat_viewer_queue.copy()
    return msgs


def clear_chat_viewer():
    chat_viewer_queue[:] = []


def get_twitch_messages(limite=None):
    msgs = twitch_messages_buffer.copy()
    if limite:
        return msgs[-limite:]
    return msgs


def is_chat_ia_activo():
    with _chat_ia_lock:
        return _chat_ia_counter > 0


def is_bot_hablando():
    from src.audio import is_busy
    return is_busy()


def start_chat(app, token, nick, channel, api_key, speaker_dev, ia_dev, gui_app,
               ia_command="!IA", ia_voice="es-MX-DaliaNeural", audio_slots=None):
    """
    Inicia el bot de Twitch en un hilo separado.
    ia_command: comando para invocar a la IA (ej: !IA)
    ia_voice: voz TTS para respuestas de la IA
    """

    def run():
        global _bot_loop
        try:
            app.log(f"🔌 Conectando a Twitch como '{nick}' en #{channel}...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            _bot_loop = loop

            mem_data = load_memory()

            class Bot(commands.Bot):
                def __init__(self):
                    tok = token.strip()
                    if not tok.startswith("oauth:"):
                        tok = f"oauth:{tok}"
                    chan = channel.strip().lstrip("#")
                    app.log(f"🔑 Token: {tok[:10]}... | Canal: #{chan}")
                    super().__init__(
                        token=tok,
                        prefix="!",
                        initial_channels=[chan]
                    )
                    self._audio_slots = audio_slots or []

                async def event_ready(self):
                    global _bot_instance
                    _bot_instance = self
                    app.log(f"✅ Bot conectado como {self.nick} en #{channel}")
                    try:
                        idle = get_idle_mode(log_fn=app.log)
                        from src.core.config import load_config
                        cfg_idle = load_config()
                        idle_interval = int(cfg_idle.get("IDLE_INTERVAL", 60))
                        idle.configure(fixed=True, time_greeting=True, ai=False, interrupt=True)
                        idle.set_interval(idle_interval)
                        idle.start(mode="twitch")
                    except Exception as e:
                        app.log(f"⚠ Error iniciando idle mode: {e}")

                async def event_message(self, message):
                    if message.echo:
                        return

                    user    = message.author.name.lower()
                    content = message.content.strip()

                    # Push rich message to chat viewer
                    try:
                        chat_viewer_queue.append({
                            "user": user,
                            "display_name": getattr(message.author, "display_name", user),
                            "color": getattr(message.author, "color", None),
                            "badges": getattr(message.author, "badges", {}),
                            "is_mod": getattr(message.author, "is_mod", False),
                            "is_sub": getattr(message.author, "is_subscriber", False),
                            "is_vip": getattr(message.author, "is_vip", False),
                            "is_broadcaster": getattr(message.author, "is_broadcaster", False),
                            "message": content,
                        })
                        if len(chat_viewer_queue) > CHAT_VIEWER_MAX:
                            chat_viewer_queue.pop(0)
                    except Exception:
                        pass

                    twitch_messages_buffer.append(f"{user}: {content}")
                    if len(twitch_messages_buffer) > TWITCH_BUFFER_MAX:
                        twitch_messages_buffer.pop(0)

                    # Moderación — check palabras prohibidas
                    try:
                        mod_result = check_message(content)
                        if mod_result:
                            action = mod_result["action"]
                            word = mod_result["word"]
                            app.log(f"🚫 [{user}] palabra prohibida: '{word}' → acción: {action}")
                            if action in ("delete", "timeout"):
                                # Delete message
                                try:
                                    await message.channel.send(f"/delete {message.id}")
                                except Exception:
                                    pass
                            if action == "timeout":
                                secs = get_timeout_seconds()
                                try:
                                    await message.channel.send(f"/timeout {user} {secs}")
                                    app.log(f"⏱  Timeout {secs}s a {user} por: '{word}'")
                                except Exception:
                                    pass
                            return  # no procesar más este mensaje
                    except Exception:
                        pass

                    # Link blocking
                    try:
                        blocked = linkblock_check(content, linkblock_get_whitelist())
                        if blocked:
                            action = linkblock_get_action()
                            app.log(f"🔗 [{user}] link bloqueado: {blocked} → {action}")
                            if action in ("delete", "timeout"):
                                try:
                                    await message.channel.send(f"/delete {message.id}")
                                except Exception:
                                    pass
                            if action == "timeout":
                                try:
                                    await message.channel.send(f"/timeout {user} 30")
                                except Exception:
                                    pass
                            if action != "log":
                                return
                    except Exception:
                        pass

                    # Keyword alerts
                    try:
                        kw_resp = keyword_check(content)
                        if kw_resp:
                            app.log(f"🔑 [{user}] keyword activada")
                            speak(f"@{user} {kw_resp}", "es-MX-DaliaNeural", speaker_dev)
                    except Exception:
                        pass

                    # Traducir mensaje si no es español
                    try:
                        cfg = _load_cfg()
                        if cfg.get("CHAT_TRANSLATE", "0") == "1" and not content.startswith("!"):
                            result = auto_translate(content)
                            if result:
                                translated, lang = result
                                app.log(f"🌐  [{lang}] {user}: {content}")
                                app.log(f"     → {translated}")
                                if lang and lang != "unknown":
                                    user_langs.set(user, lang)
                    except Exception:
                        pass

                    # Notificar al idle mode que hay actividad
                    try:
                        get_idle_mode().on_message()
                    except Exception:
                        pass

                    # Analizar reacción del chat para aprendizaje
                    try:
                        from src.ia.chat_learning import get_chat_learning
                        cl = get_chat_learning()
                        for rid, rinfo in list(cl._recent_responses.items()):
                            if time.time() - rinfo["time"] < 30:
                                reaction = cl.analyze_reaction(content, rinfo["text"])
                                if reaction["emotion"] != 0:
                                    cl.record_reaction_to_response(rid, user, content, reaction)
                                    cl.learn_pattern(rinfo["text"], reaction)
                                    if reaction["emotion"] == 1:
                                        app.log(f"📈 {user} reaccionó bien: {content[:60]}")
                                    else:
                                        app.log(f"📉 {user} reacción negativa: {content[:60]}")
                    except Exception:
                        pass

                    # ── Permission check helper ──
                    def _can(cmd_name):
                        role = check_role(message)
                        ok = has_permission(cmd_name, role)
                        if not ok:
                            app.log(f"🔒 {user} no tiene permiso para !{cmd_name} (rol: {role})")
                            speak(f"@{user}, no tienes permiso para usar ese comando.", "es-MX-DaliaNeural", speaker_dev)
                        return ok

                    for path, cmd in self._audio_slots:
                        if cmd and content.lower() == cmd.lower():
                            if not _can(cmd.lstrip("!")):
                                break
                            if path and os.path.isfile(path):
                                app.log(f"🔊 {user} activó sonido: {os.path.basename(path)}")
                                threading.Thread(target=play_file, args=(path, speaker_dev), daemon=True).start()
                            else:
                                app.log(f"⚠ Archivo de audio no encontrado: {path}")
                            return

                    if content.lower().startswith("!sp ") and _can("sp"):
                        texto = content[4:].strip()
                        if texto:
        
                            speak(f"{user} dice: {texto}", "es-ES-AlvaroNeural", speaker_dev)
        

                    elif content.lower().startswith("!sph ") and _can("sph"):
                        texto = content[5:].strip()
                        if texto:
        
                            speak(f"{user} dice: {texto}", "es-ES-AlvaroNeural", speaker_dev)
        

                    elif content.lower().startswith("!spm ") and _can("spm"):
                        texto = content[5:].strip()
                        if texto:
        
                            speak(f"{user} dice: {texto}", "es-MX-DaliaNeural", speaker_dev)
        

                    elif content.lower().startswith("!aprender") and _can("aprender"):
                        from src.ia.chat_learning import get_learning_summary
                        summary = get_learning_summary()
                        app.log(f"📊 {summary}")
    
                        speak(f"{user}, {summary}", "es-MX-DaliaNeural", speaker_dev)
    

                    elif content.lower().startswith("!showtime") and _can("showtime"):
                        # Parse: !showtime [dance_name]
                        SHOWTIME_DANCES = {
                            'hip': '1_Arms Hip Hop Dance',
                            'house': '45_House Dancing',
                            'jazz': '47_Jazz Dancing',
                            'silly': '70_Silly Dancing',
                            'clap': '19_Clapping',
                            'wave': '161_Waving',
                            'angry': '94_Angry Gesture',
                            'laugh': '150_Sitting Laughing',
                            'think': '88_Thinking',
                            'sad': '22_Crying',
                            'dance': '41_Hip Hop Dancing',
                            'rumba': '67_Rumba Dancing',
                            'swing': '83_Swing Dancing',
                            'belly': '4_Belly Dance',
                        }
                        parts = content.lower().split()[1:]
                        if parts and parts[0] in SHOWTIME_DANCES:
                            dance = SHOWTIME_DANCES[parts[0]]
                        else:
                            # Random dance
                            dance = random.choice(list(SHOWTIME_DANCES.values()))
                        app.log(f"🎤 {user} activó SHOWTIME! dance={dance}")
                        # Showtime requires a renderer (deleted)
                        threading.Thread(
                            target=_showtime_speak,
                            args=(user, speaker_dev),
                            daemon=True
                        ).start()
                    elif content.lower() == "!end" or content.lower() == "!stop":
                        app.log(f"⏹ {user} terminó SHOWTIME")
                        stop_audio()

                    elif content.lower().startswith(f"{ia_command.lower()} "):
                        if _can(ia_command.lower().lstrip("!")):
                            cmd_len = len(ia_command) + 1
                            texto = content[cmd_len:].strip()
                            if not texto:
                                return
                            threading.Thread(
                                target=_procesar_ia,
                                args=(user, texto, mem_data, api_key, gui_app,
                                      ia_dev, app, ia_voice),
                                daemon=True
                            ).start()

                    elif any(content.lower().startswith(cmd) for cmd in ("!abre ", "!abrir ", "!cierra ", "!cerrar ")):
                        if _can(content.split()[0].lstrip("!").lower()):
                            first = content.split()[0].lower().lstrip("!")
                            action_map = {"abre": "abrir", "abrir": "abrir", "cierra": "cerrar", "cerrar": "cerrar"}
                            action = action_map.get(first, "abrir")
                            name = content[len(first)+2:].strip()
                            if name:
                                result = handle_command(f"{action} {name}")
                                app.log(f"🎮 {user}: {result}")
            
                                speak(f"{user}, {result}", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower() in ("!juegos", "!lista", "!games"):
                        if _can("juegos"):
                            result = list_games()
                            app.log(f"🎮 {user}: {result}")
        
                            speak(f"{user}. {result.replace('🎮','').replace('🟢','verde').replace('⚫','apagado').replace('  ','')}", "es-MX-DaliaNeural", speaker_dev)
        

                    # ═══════════════════════════════════════════════
                    #  STREAM TOOLS
                    # ═══════════════════════════════════════════════

                    # ── Quotes ──
                    elif content.lower().startswith("!quote add "):
                        if _can("quote"):
                            text = content[11:].strip()
                            if text:
                                qid = quote_add(text, user)
                                app.log(f"💬 {user} agregó quote #{qid}")
            
                                speak(f"@{user}, quote #{qid} guardado", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower().startswith("!quote "):
                        if _can("quote"):
                            arg = content[7:].strip()
                            try:
                                qid = int(arg)
                                q = quote_get(qid)
                            except ValueError:
                                q = quote_get()
                            if q:
                                msg = f"Quote #{q['id']}: {q['text']} — {q['author']}"
            
                                speak(msg[:200], "es-MX-DaliaNeural", speaker_dev)
            
                            else:
            
                                speak(f"No hay quotes", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower() in ("!quote", "!quotes"):
                        if _can("quote"):
                            q = quote_get()
                            if q:
                                msg = f"Quote #{q['id']}: {q['text']} — {q['author']}"
            
                                speak(msg[:200], "es-MX-DaliaNeural", speaker_dev)
            
                            else:
            
                                speak(f"No hay quotes aún", "es-MX-DaliaNeural", speaker_dev)
            

                    # ── Raffle ──
                    elif content.lower() == "!sorteo" or content.lower() == "!raffle":
                        if _can("raffle"):
                            if raffle_is_active():
                                cnt = raffle_count()
            
                                speak(f"Hay sorteo activo! {cnt} participantes. Escribe !join para participar", "es-MX-DaliaNeural", speaker_dev)
            
                            else:
            
                                speak(f"No hay sorteo activo", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower() == "!raffle open" or content.lower() == "!sorteo abrir":
                        if _can("raffle_open"):
                            raffle_open()
                            app.log(f"🎲 {user} abrió sorteo")
        
                            speak(f"Sorteo abierto! Escribe !join para participar", "es-MX-DaliaNeural", speaker_dev)
        

                    elif content.lower() == "!raffle pick" or content.lower() == "!sorteo elegir":
                        if _can("raffle_pick"):
                            winner, msg = raffle_pick()
                            app.log(f"🎲 {msg}")
        
                            speak(msg, "es-MX-DaliaNeural", speaker_dev)
        

                    elif content.lower() == "!raffle close" or content.lower() == "!sorteo cerrar":
                        if _can("raffle_close"):
                            raffle_close()
                            app.log(f"🎲 {user} cerró sorteo")
        
                            speak(f"Sorteo cerrado", "es-MX-DaliaNeural", speaker_dev)
        

                    # ── Join (raffle + game queue) ──
                    elif content.lower() == "!join":
                        if _can("join"):
                            if raffle_is_active():
                                ok, msg = raffle_enter(user)
                                app.log(f"🎲 {msg}")
                                if ok:
                
                                    speak(f"@{user}, participas en el sorteo!", "es-MX-DaliaNeural", speaker_dev)
                
                            else:
                                ok, msg = gqueue_join(user)
                                if ok:
                                    app.log(f"🎮 {msg}")
                
                                    speak(f"@{user}, estás en la cola de juegos", "es-MX-DaliaNeural", speaker_dev)
                

                    elif content.lower() == "!leave" or content.lower() == "!salir":
                        gqueue_leave(user)
                        app.log(f"🚪 {user} salió de la cola")

                    # ── Game queue ──
                    elif content.lower() == "!pick" or content.lower() == "!siguiente":
                        if _can("pick"):
                            pick, msg = gqueue_pick()
                            if pick:
                                app.log(f"🎮 {msg}")
            
                                speak(msg, "es-MX-DaliaNeural", speaker_dev)
            
                            else:
            
                                speak(f"Cola vacía", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower() in ("!queue", "!cola"):
                        q = gqueue_list()
                        if q:
                            q_str = ", ".join(q[:10])
                            extra = f" y {len(q)-10} más" if len(q) > 10 else ""
        
                            speak(f"Cola: {q_str}{extra}", "es-MX-DaliaNeural", speaker_dev)
        
                        else:
        
                            speak(f"Cola vacía", "es-MX-DaliaNeural", speaker_dev)
        

                    # ── Schedule ──
                    elif content.lower() in ("!horario", "!schedule"):
                        sched = schedule_format()
    
                        speak(sched[:200].replace("📅", ""), "es-MX-DaliaNeural", speaker_dev)
    

                    # ── Song Request ──
                    elif content.lower() == "!songskip" or content.lower() == "!sr skip":
                        if _can("sr_skip"):
                            song = songreq_dequeue()
                            if song:
                                _download_and_play(song["url"], speaker_dev, app)
                                app.log(f"⏭  Saltando a siguiente canción")
                            else:
                                speak(f"No hay más canciones", "es-MX-DaliaNeural", speaker_dev)

                    elif content.lower().startswith("!sr ") or content.lower().startswith("!song "):
                        if _can("sr"):
                            url = content[4:].strip() if content.lower().startswith("!sr ") else content[6:].strip()
                            if url:
                                pos = songreq_enqueue(url, user)
                                app.log(f"🎵 {user} solicitó: {url} (posición {pos})")
            
                                speak(f"@{user}, canción agregada en posición {pos}", "es-MX-DaliaNeural", speaker_dev)
            
                                threading.Thread(target=_download_and_play, args=(url, speaker_dev, app), daemon=True).start()

                    # ── Keyword alerts ──
                    elif content.lower().startswith("!keyword add "):
                        if _can("keyword"):
                            rest = content[13:].strip()
                            if " " in rest:
                                kw, resp = rest.split(None, 1)
                                keyword_add(kw, resp)
                                app.log(f"🔑 {user} agregó keyword: {kw}")
            
                                speak(f"Keyword '{kw}' agregada", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower().startswith("!keyword del ") or content.lower().startswith("!keyword remove "):
                        if _can("keyword"):
                            kw = content.split(None, 2)[-1].strip()
                            keyword_remove(kw)
                            app.log(f"🔑 {user} eliminó keyword: {kw}")

                    # ── Notas ──
                    elif content.lower().startswith("!nota "):
                        if _can("nota"):
                            text = content[6:].strip()
                            if text:
                                note_set(user, text)
                                app.log(f"📝 {user}: nota guardada")
            
                                speak(f"@{user}, nota guardada", "es-MX-DaliaNeural", speaker_dev)
            

                    elif content.lower().startswith("!"):
                        cmd_full = content[1:].strip()
                        cmd_name = cmd_full.split()[0].lower() if cmd_full else ""
                        args = cmd_full[len(cmd_name)+1:].strip() if " " in cmd_full else ""
                        # Plugin commands
                        if cmd_name in _plugin_commands:
                            try:
                                res = _plugin_commands[cmd_name](user, args)
                                if res:
                
                                    speak(res, "es-MX-DaliaNeural", speaker_dev)
                
                            except Exception as e:
                                app.log(f"⚠ Plugin command !{cmd_name}: {e}")
                            return
                        parts = content.split(None, 1)
                        cmd_args = [parts[1]] if len(parts) > 1 else []
                        if _can(cmd_name):
                            result = exec_custom_cmd(cmd_name, cmd_args, channel=channel, user=user)
                            if result is not None:
                                app.log(f"💬 {user}: !{cmd_name} → {result}")
            
                                speak(result, "es-MX-DaliaNeural", speaker_dev)
            

                async def event_error(self, error: Exception, data=None):
                    app.log(f"⚠ Error en bot Twitch: {error}")
                    backoff = 10
                    max_backoff = 300
                    while backoff <= max_backoff:
                        await asyncio.sleep(backoff)
                        try:
                            if self.is_connected:
                                app.log("ℹ Bot aún conectado, ignorando reconexión")
                                return
                        except Exception:
                            pass
                        try:
                            app.log("🔄 Reconectando bot Twitch...")
                            await self.start()
                            app.log("✅ Bot reconectado automáticamente")
                            return
                        except Exception as e:
                            app.log(f"❌ Falló reconexión: {e}")
                            backoff = min(backoff * 2, max_backoff)

            bot = Bot()
            loop.run_until_complete(bot.start())

        except Exception as e:
            import traceback
            app.log(f"❌ Error al iniciar Twitch: {e}")
            app.log(traceback.format_exc())

    threading.Thread(target=run, daemon=True).start()


def send_chat_message(text):
    """Send a text message to the Twitch chat using the active bot instance."""
    global _bot_instance, _bot_loop
    if not _bot_instance or not _bot_loop:
        return False
    try:
        channels = _bot_instance.connected_channels
        if channels:
            asyncio.run_coroutine_threadsafe(
                channels[0].send(text),
                _bot_loop
            )
            return True
    except Exception:
        pass
    return False


def _showtime_speak(user, speaker_dev):
    """Say a showtime greeting via TTS."""
    try:
        speak(f"¡Showtime! {user} me puso a bailar. ¡Vamos!",
              "es-MX-DaliaNeural", speaker_dev)
    except Exception:
        pass


def _download_and_play(url, speaker_dev, app):
    """Download and play a song request in background."""
    try:
        path = songreq_download(url)
        if path:
            app.log(f"🎵  Reproduciendo: {os.path.basename(path)}")
            songreq_play(path, speaker_dev)
        else:
            app.log("❌  No se pudo descargar la canción (instala yt-dlp: pip install yt-dlp)")
    except Exception as e:
        app.log(f"❌  Error en song request: {e}")


def _procesar_ia(user, texto, mem_data, api_key, gui_app, ia_dev, app, ia_voice="es-MX-DaliaNeural"):
    global _chat_ia_counter
    with _chat_ia_lock:
        _chat_ia_counter += 1
    resp_id = str(time.time())
    try:
        app.log(f"💬 {user}: {texto}")

        if user not in mem_data:
            mem_data[user] = {"history": [], "data": [], "mood": 0, "emotion": 0}

        try:
            update_mood(mem_data, user, texto)
        except Exception:
            pass

        try:
            old_context = get_context(mem_data, user)
        except Exception:
            old_context = ""

        # Buscar memorias relevantes en Vector Memory
        vector_context = ""
        try:
            vector_context = get_memory_context(texto, user=user)
        except Exception:
            pass

        # Obtener ajustes de aprendizaje del chat
        style_adj = {}
        try:
            style_adj = get_style_adjustment()
        except Exception:
            pass

        # Agregar instrucciones de aprendizaje al prompt
        learning_instruction = ""
        if style_adj:
            learning_instruction = style_adj.get("extra_instruction", "")
            avoid = style_adj.get("avoid_patterns", [])
            if avoid:
                learning_instruction += f" Evita frases como: {' o '.join(avoid[:2])}."

        prompt_parts = [gui_app.current_prompt]
        if vector_context:
            prompt_parts.append(f"\n[Recuerdos relevantes]\n{vector_context}")
        if old_context:
            prompt_parts.append(f"\n[Contexto]\n{old_context}")
        if learning_instruction:
            prompt_parts.append(f"\n[Aprendizaje]\n{learning_instruction}")

        prompt_final = "\n\n".join(prompt_parts).strip()
        api_key_cerebras = api_key
        try:
            from src.core.config import load_config
            cfg = load_config()
            api_key_cerebras = cfg.get("CEREBRAS_API_KEY", api_key)
        except Exception:
            pass
        respuesta = cached_ask_ai(user, texto, api_key_cerebras, prompt_final, "cerebras")

        if not respuesta or respuesta.strip() == "":
            respuesta = "Hmm, no sé qué decirte ahora mismo..."

        # Traducir respuesta al idioma del usuario si corresponde
        try:
            cfg = _load_cfg()
            if cfg.get("CHAT_TRANSLATE", "0") == "1":
                user_lang = user_langs.get(user)
                if user_lang and user_lang != "es":
                    from src.utils.chat_translator import translate as _tr
                    translated, _ = _tr(respuesta, target=user_lang)
                    if translated:
                        app.log(f"🌐  Respuesta traducida a [{user_lang}]: {translated}")
                        respuesta = translated
        except Exception:
            pass

        # Detect emotion from response
        detected_emotion = None
        try:
            from src.avatar.karin_mocap import detect_emotion
            detected_emotion, _ = detect_emotion(respuesta)
        except Exception:
            pass

        # Guardar en Vector Memory
        try:
            add_to_memory(texto, user=user, role="user")
            add_to_memory(respuesta, user=user, role="assistant")
        except Exception:
            pass

        # Trackear respuesta para aprendizaje
        try:
            cl = get_chat_learning()
            cl.track_response(resp_id, respuesta)
        except Exception:
            pass

        from src.ia.memory import EMOTION_VOICES, EMOTION_PREFIXES
        
        mood = mem_data[user].get("mood", 0)
        emotion = mem_data[user].get("emotion", 0)
        
        voz = EMOTION_VOICES.get(emotion, ia_voice)
        inicio = random.choice(EMOTION_PREFIXES.get(emotion, ["Oye", "Mira", "Escucha"]))
        
        flair = ""
        if emotion == 1:
            flair = "💖 "
        elif emotion == 2:
            flair = "✨ "
        elif emotion == 3:
            flair = "😤 "
        elif emotion == 4:
            flair = "💭 "
        elif emotion == 5:
            flair = "🤒 "
        
        mensaje_final = f"{inicio} {user}{flair}{respuesta}"

        app.log(f"🤖 IA → {user}: {respuesta}")

        try:
            with _mem_lock:
                add_message(mem_data, user, texto)
                add_message(mem_data, user, respuesta)
                save_memory(mem_data)
        except Exception:
            pass

        stop_audio()
        speak(mensaje_final, voz, ia_dev)
        update_ultima_vez_ia_chat()

    except Exception as e:
        import traceback
        app.log(f"❌ Error procesando IA para {user}: {e}")
        app.log(traceback.format_exc())
    finally:
        with _chat_ia_lock:
            _chat_ia_counter = max(0, _chat_ia_counter - 1)