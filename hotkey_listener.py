import queue
import threading

from pynput.keyboard import GlobalHotKeys, Key, KeyCode


class HotkeyListener:
    def __init__(self, hotkey_str: str, callback):
        self._hotkey_str = hotkey_str
        self._callback = callback
        self._task_queue = queue.Queue()
        self._running = False
        self._worker = None

    def _parse_hotkey(self, hotkey_str: str) -> str:
        mapping = {
            "ctrl": "<ctrl>",
            "shift": "<shift>",
            "alt": "<alt>",
            "win": "<cmd>",
        }
        parts = hotkey_str.lower().replace("+", " ").replace(",", " ").split()
        parsed = []
        for p in parts:
            parsed.append(mapping.get(p, p))
        return "+".join(parsed)

    def _on_activate(self):
        try:
            self._task_queue.put_nowait(self._callback)
        except queue.Full:
            pass

    def start(self):
        self._running = True
        parsed = self._parse_hotkey(self._hotkey_str)
        self._listener = GlobalHotKeys({parsed: self._on_activate})
        self._listener.start()

        self._worker = threading.Thread(target=self._run_loop, daemon=True)
        self._worker.start()

    def _run_loop(self):
        while self._running:
            try:
                task = self._task_queue.get(timeout=0.5)
                task()
            except queue.Empty:
                pass

    def stop(self):
        self._running = False
        if hasattr(self, "_listener"):
            self._listener.stop()
