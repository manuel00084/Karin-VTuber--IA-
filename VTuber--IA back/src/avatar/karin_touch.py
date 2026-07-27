"""Karin Touch System — Node.js server launcher + cloudflare tunnel."""
import subprocess
import os
import sys
import threading
import time
import urllib.request
import json
import logging

log = logging.getLogger(__name__)

BASE_DIR = os.path.join(os.path.dirname(__file__), '..', '..')
KARIN_TOUCH_DIR = os.path.join(BASE_DIR, 'karin-touch')

# Node.js portable path
NODE_DIR = os.path.expanduser('~\\AppData\\Local\\node-portable\\node-v22.15.0-win-x64')
NODE_EXE = os.path.join(NODE_DIR, 'node.exe')

# Cloudflared path
CLOUDFLARED = os.path.join(KARIN_TOUCH_DIR, 'cloudflared.exe')


class KarinTouchServer:
    def __init__(self, log_fn=None):
        self._log = log_fn or (lambda msg: print(f"[KarinTouch] {msg}"))
        self._node_process = None
        self._tunnel_process = None
        self._tunnel_url = None
        self._running = False

    @property
    def is_running(self):
        return self._running

    @property
    def tunnel_url(self):
        return self._tunnel_url

    def start(self, port=3000, tunnel=True):
        if self._running:
            self._log("Ya está corriendo")
            return

        if not os.path.isfile(NODE_EXE):
            self._log("Node.js no encontrado. Instala Node.js o usa portable.")
            return

        if not os.path.isfile(os.path.join(KARIN_TOUCH_DIR, 'server.js')):
            self._log("karin-touch no encontrado en karin-touch/")
            return

        if not os.path.isfile(os.path.join(KARIN_TOUCH_DIR, 'node_modules', 'express', 'package.json')):
            self._log("Instalando dependencias...")
            try:
                subprocess.run([NODE_EXE, os.path.join(NODE_DIR, 'node_modules', 'npm', 'bin', 'npm-cli.js'), 'install'],
                             cwd=KARIN_TOUCH_DIR, timeout=60, capture_output=True)
            except Exception as e:
                self._log(f"Error npm install: {e}")
                return

        # Start Node.js server
        self._node_process = subprocess.Popen(
            [NODE_EXE, 'server.js'],
            cwd=KARIN_TOUCH_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
        )
        self._running = True
        self._log(f"Servidor Node.js iniciado (PID {self._node_process.pid})")

        # Start cloudflare tunnel
        if tunnel and os.path.isfile(CLOUDFLARED):
            self._start_tunnel(port)
        elif tunnel:
            self._log("cloudflared.exe no encontrado en karin-touch/")

    def _start_tunnel(self, port):
        def _run():
            try:
                self._tunnel_process = subprocess.Popen(
                    [CLOUDFLARED, 'tunnel', '--url', f'http://localhost:{port}'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
                )
                # Read stderr for URL
                for line in iter(self._tunnel_process.stderr.readline, b''):
                    text = line.decode('utf-8', errors='ignore')
                    if 'trycloudflare.com' in text:
                        import re
                        match = re.search(r'(https://[^\s]+trycloudflare\.com)', text)
                        if match:
                            self._tunnel_url = match.group(1)
                            self._log(f"🌐 Tunnel URL: {self._tunnel_url}")
                            self._log(f"   TouchPad: {self._tunnel_url}/touch")
                            self._log(f"   Overlay:  {self._tunnel_url}/overlay")
                            break
            except Exception as e:
                self._log(f"Error tunnel: {e}")

        threading.Thread(target=_run, daemon=True).start()

    def stop(self):
        if self._node_process:
            try:
                self._node_process.terminate()
            except Exception:
                pass
            self._node_process = None

        if self._tunnel_process:
            try:
                self._tunnel_process.terminate()
            except Exception:
                pass
            self._tunnel_process = None

        self._running = False
        self._tunnel_url = None
        self._log("Servidor detenido")
