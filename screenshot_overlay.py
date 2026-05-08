import ctypes
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageGrab, ImageTk


def _get_virtual_screen_rect():
    user32 = ctypes.windll.user32
    x = user32.GetSystemMetrics(76)       # SM_XVIRTUALSCREEN
    y = user32.GetSystemMetrics(77)       # SM_YVIRTUALSCREEN
    w = user32.GetSystemMetrics(78)       # SM_CXVIRTUALSCREEN
    h = user32.GetSystemMetrics(79)       # SM_CYVIRTUALSCREEN
    return x, y, w, h


def select_region():
    """Returns (cropped_image, action) where action is 'pin'|'ocr'|'copy'|None."""
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)

    vx, vy, vw, vh = _get_virtual_screen_rect()
    full_img = ImageGrab.grab(all_screens=True)

    selector = tk.Toplevel(root)
    selector.overrideredirect(True)
    selector.geometry(f"{vw}x{vh}+{vx}+{vy}")
    selector.attributes("-topmost", True)
    selector.configure(cursor="cross")
    selector.focus_force()

    canvas = tk.Canvas(selector, highlightthickness=0, bg="black")
    canvas.pack(fill="both", expand=True)

    bg_tk = ImageTk.PhotoImage(full_img)
    canvas.create_image(0, 0, image=bg_tk, anchor="nw", tags="bg")

    state = {
        "start_x": None, "start_y": None,
        "end_x": None, "end_y": None,
        "selected_action": None,
        "confirmed": False,
        "toolbar": None,
    }

    def draw_overlay(x1, y1, x2, y2):
        canvas.delete("overlay")
        left, right = sorted([x1, x2])
        top, bottom = sorted([y1, y2])

        fill_color = "#000000"
        stipple = "gray50"

        regions = [
            (0, 0, vw, top),
            (0, top, left, bottom),
            (right, top, vw, bottom),
            (0, bottom, vw, vh),
        ]
        for rx1, ry1, rx2, ry2 in regions:
            if rx2 > rx1 and ry2 > ry1:
                canvas.create_rectangle(
                    rx1, ry1, rx2, ry2,
                    fill=fill_color, stipple=stipple,
                    outline="", tags="overlay",
                )

        canvas.create_rectangle(
            left, top, right, bottom,
            outline="#00BFFF", width=2, tags="overlay",
        )

        w, h = right - left, bottom - top
        label_text = f"{w} x {h}"
        label_x = right + 6 if right + 100 < vw else left - 100
        label_y = bottom + 16 if bottom + 20 < vh else top - 6
        canvas.delete("size_label")
        canvas.create_text(
            label_x, label_y, text=label_text,
            fill="#00BFFF", anchor="nw",
            font=("Consolas", 10, "bold"), tags="size_label",
        )

    def show_toolbar():
        left, right = sorted([state["start_x"], state["end_x"]])
        top, bottom = sorted([state["start_y"], state["end_y"]])

        toolbar = tk.Toplevel(selector)
        toolbar.overrideredirect(True)
        toolbar.attributes("-topmost", True)
        toolbar.configure(bg="#2d2d2d", padx=3, pady=3)

        style = ttk.Style()
        style.configure("Toolbar.TButton", font=("Microsoft YaHei UI", 10), padding=(12, 4))

        def do_action(action):
            state["selected_action"] = action
            toolbar.destroy()
            selector.destroy()

        btn_pin = ttk.Button(toolbar, text="钉住", style="Toolbar.TButton",
                             command=lambda: do_action("pin"))
        btn_ocr = ttk.Button(toolbar, text="识字", style="Toolbar.TButton",
                             command=lambda: do_action("ocr"))
        btn_copy = ttk.Button(toolbar, text="复制", style="Toolbar.TButton",
                              command=lambda: do_action("copy"))

        btn_pin.pack(side="left", padx=2)
        btn_ocr.pack(side="left", padx=2)
        btn_copy.pack(side="left", padx=2)

        toolbar.update_idletasks()
        tw = toolbar.winfo_width()
        th = toolbar.winfo_height()

        # Try below the selection first, then above, then right
        gap = 8
        if bottom + th + gap < vh:
            tx = left + (right - left - tw) // 2
            ty = bottom + gap
        elif top - th - gap >= 0:
            tx = left + (right - left - tw) // 2
            ty = top - th - gap
        else:
            tx = right + gap if right + tw + gap < vw else left - tw - gap
            ty = top + (bottom - top - th) // 2

        tx = max(4, min(tx, vw - tw - 4))
        ty = max(4, min(ty, vh - th - 4))
        toolbar.geometry(f"+{tx}+{ty}")

        state["toolbar"] = toolbar

    def on_press(event):
        if state["confirmed"]:
            # After confirmation, click outside selection → cancel
            left, right = sorted([state["start_x"], state["end_x"]])
            top, bottom = sorted([state["start_y"], state["end_y"]])
            if not (left <= event.x <= right and top <= event.y <= bottom):
                if state["toolbar"]:
                    state["toolbar"].destroy()
                selector.destroy()
            return

        state["start_x"], state["start_y"] = event.x, event.y
        draw_overlay(event.x, event.y, event.x, event.y)

    def on_drag(event):
        if not state["confirmed"] and state["start_x"] is not None:
            draw_overlay(state["start_x"], state["start_y"], event.x, event.y)

    def on_release(event):
        if state["confirmed"] or state["start_x"] is None:
            return
        state["end_x"], state["end_y"] = event.x, event.y

        left, right = sorted([state["start_x"], state["end_x"]])
        top, bottom = sorted([state["start_y"], state["end_y"]])
        if right - left < 5 or bottom - top < 5:
            state["start_x"] = None
            return

        state["confirmed"] = True
        selector.configure(cursor="")
        show_toolbar()

    def on_escape(event):
        if state["toolbar"]:
            state["toolbar"].destroy()
        state["start_x"] = None
        selector.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    selector.bind("<Escape>", on_escape)

    root.wait_window(selector)
    root.destroy()

    if state["selected_action"] is None or state["start_x"] is None:
        return None, None

    x1, y1 = state["start_x"], state["start_y"]
    x2, y2 = state["end_x"], state["end_y"]
    left, right = sorted([x1, x2])
    top, bottom = sorted([y1, y2])

    return full_img.crop((left, top, right, bottom)), state["selected_action"]
