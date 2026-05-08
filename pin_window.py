import tkinter as tk
from PIL import Image, ImageTk


_MIN_SCALE = 0.2
_MAX_SCALE = 4.0
_ZOOM_STEP = 0.1
_ZOOM_STEP_FAST = 0.3
_BTN_SIZE = 20


def show_pin_window(image: Image.Image):
    """钉住截图。可拖拽、滚轮缩放、Esc/✕关闭，无外框无工具栏。"""
    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg="#000000")

    orig = image.copy()
    scale = tk.DoubleVar(value=1.0)
    drag = {"x": 0, "y": 0}

    # ---- image label ----
    label = tk.Label(win, bg="#000000", cursor="fleur")
    label.pack()

    # ---- close button (small, top-right, absolute positioned) ----
    close_btn = tk.Canvas(win, width=_BTN_SIZE, height=_BTN_SIZE,
                          highlightthickness=0, bd=0, cursor="hand2")

    def do_close(*args):
        win.destroy()
        root.destroy()

    # A subtle close mark — will be drawn when apply_zoom runs
    close_btn.bind("<Button-1>", do_close)

    # ---- drag ----
    def on_drag_start(event):
        drag["x"] = event.x_root
        drag["y"] = event.y_root

    def on_drag_move(event):
        dx = event.x_root - drag["x"]
        dy = event.y_root - drag["y"]
        drag["x"] = event.x_root
        drag["y"] = event.y_root
        win.geometry(f"+{win.winfo_x() + dx}+{win.winfo_y() + dy}")

    label.bind("<Button-1>", on_drag_start)
    label.bind("<B1-Motion>", on_drag_move)

    # ---- scroll-wheel zoom ----
    def on_wheel(event):
        step = _ZOOM_STEP_FAST if (event.state & 0x4) else _ZOOM_STEP

        if event.delta > 0:
            new_val = min(scale.get() + step, _MAX_SCALE)
        else:
            new_val = max(scale.get() - step, _MIN_SCALE)
        scale.set(round(new_val, 2))
        _apply_zoom()

    for w in (win, label, close_btn):
        w.bind("<MouseWheel>", on_wheel)

    # ---- right-click menu ----
    menu = tk.Menu(win, tearoff=0)
    menu.add_command(label="放大  +", command=lambda: _adjust_zoom(_ZOOM_STEP))
    menu.add_command(label="缩小  −", command=lambda: _adjust_zoom(-_ZOOM_STEP))
    menu.add_command(label="还原 1:1", command=lambda: _reset_zoom())
    menu.add_separator()
    menu.add_command(label="关闭", command=do_close)

    def on_right_click(event):
        menu.post(event.x_root, event.y_root)

    label.bind("<Button-3>", on_right_click)

    # ---- keyboard ----
    win.bind("<Escape>", do_close)
    win.bind("<plus>", lambda e: _adjust_zoom(_ZOOM_STEP))
    win.bind("<minus>", lambda e: _adjust_zoom(-_ZOOM_STEP))
    win.bind("<equal>", lambda e: _adjust_zoom(_ZOOM_STEP))
    win.bind("<Key-0>", lambda e: _reset_zoom())
    win.bind("<Control-plus>", lambda e: _adjust_zoom(_ZOOM_STEP_FAST))
    win.bind("<Control-minus>", lambda e: _adjust_zoom(-_ZOOM_STEP_FAST))
    win.bind("<Control-equal>", lambda e: _adjust_zoom(_ZOOM_STEP_FAST))

    def _adjust_zoom(delta):
        scale.set(round(max(_MIN_SCALE, min(_MAX_SCALE, scale.get() + delta)), 2))
        _apply_zoom()

    def _reset_zoom():
        scale.set(1.0)
        _apply_zoom()

    # ---- apply ----
    def _apply_zoom():
        s = scale.get()
        new_w = max(20, int(orig.width * s))
        new_h = max(20, int(orig.height * s))
        resized = orig.resize((new_w, new_h), Image.LANCZOS)
        tk_img = ImageTk.PhotoImage(resized)
        label.configure(image=tk_img)
        label.image = tk_img

        # Reposition close button: top-right corner of image
        cx = new_w - _BTN_SIZE - 2
        cy = 2
        close_btn.place(x=max(0, cx), y=cy)

        # Redraw close-icon scaled to button size
        sz = _BTN_SIZE
        close_btn.delete("all")
        close_btn.create_oval(sz * 0.1, sz * 0.15, sz * 0.9, sz * 0.85,
                              fill="#cc0000", outline="", tags="close")
        close_btn.create_line(sz * 0.35, sz * 0.4, sz * 0.65, sz * 0.6,
                              fill="white", width=2, tags="close")
        close_btn.create_line(sz * 0.65, sz * 0.4, sz * 0.35, sz * 0.6,
                              fill="white", width=2, tags="close")

        # Resize window to exactly hug the image
        win.geometry(f"{new_w}x{new_h}")

    _apply_zoom()

    # Center on screen
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    ww = orig.width
    wh = orig.height
    win.geometry(f"+{(sw - ww) // 2}+{(sh - wh) // 2}")

    win.focus_force()
    root.wait_window(win)
    try:
        root.destroy()
    except tk.TclError:
        pass
