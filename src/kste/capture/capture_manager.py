import numpy as np
from src.utils.log import info, warn
from src.utils.dxgi_capture import capturar_pantalla
from src.kste.config.kste_config import KSTEConfig, save_kste_config


class CaptureManager:
    def __init__(self, config):
        self.config = config

    def capture(self):
        if not self.has_region():
            return capturar_pantalla()
        return capturar_pantalla(region=self.config.capture_region)

    def set_region(self, x, y, w, h):
        self.config.capture_region = (x, y, w, h)
        save_kste_config(self.config)
        info(f"KSTE capture region set: ({x},{y},{w},{h})")

    def get_region(self):
        return self.config.capture_region

    def has_region(self):
        r = self.config.capture_region
        return r is not None and len(r) == 4

    def clear_region(self):
        self.config.capture_region = None
        save_kste_config(self.config)

    def calibrate(self):
        try:
            import tkinter as tk
            result = {"region": None}
            root = tk.Tk()
            root.title("KSTE - Selecciona area del chat")
            root.attributes("-fullscreen", True)
            root.attributes("-alpha", 0.3)
            root.attributes("-topmost", True)
            root.configure(bg="black")
            canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            start = {"x": 0, "y": 0}
            rect_id = [None]

            def on_press(e):
                start["x"], start["y"] = e.x, e.y
                if rect_id[0]:
                    canvas.delete(rect_id[0])

            def on_drag(e):
                if rect_id[0]:
                    canvas.delete(rect_id[0])
                rect_id[0] = canvas.create_rectangle(
                    start["x"], start["y"], e.x, e.y,
                    outline="lime", width=2
                )

            def on_release(e):
                x1, y1 = min(start["x"], e.x), min(start["y"], e.y)
                x2, y2 = max(start["x"], e.x), max(start["y"], e.y)
                w, h = x2 - x1, y2 - y1
                if w > 20 and h > 20:
                    result["region"] = (x1, y1, w, h)
                root.destroy()

            canvas.bind("<ButtonPress-1>", on_press)
            canvas.bind("<B1-Motion>", on_drag)
            canvas.bind("<ButtonRelease-1>", on_release)
            root.bind("<Escape>", lambda e: root.destroy())
            root.mainloop()
            if result["region"]:
                self.set_region(*result["region"])
                r = result["region"]
                return f"Region: x={r[0]}, y={r[1]}, w={r[2]}, h={r[3]}"
            return "Cancelado"
        except Exception as e:
            warn(f"KSTE calibrate error: {e}")
            return f"Error: {e}"
