import threading
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from clipboard_manager import set_text_to_clipboard
import translator as tr


def show_ocr_window(image: Image.Image, ocr_engine):
    """OCR 识别截图文字，弹出文字窗口供用户选择复制。"""
    if ocr_engine is None:
        _show_error("OCR 引擎未就绪\n\n请安装 Tesseract-OCR:\n"
                     "https://github.com/UB-Mannheim/tesseract/wiki")
        return

    root = tk.Tk()
    root.withdraw()
    root.overrideredirect(True)

    win = tk.Toplevel(root)
    win.title("文字识别")
    win.geometry("560x440")
    win.minsize(360, 260)
    win.configure(bg="#f0f0f0")
    win.attributes("-topmost", True)

    # ---- toolbar ----
    toolbar = tk.Frame(win, bg="#e8e8e8", height=36)
    toolbar.pack(fill="x", side="top")
    toolbar.pack_propagate(False)

    btn_frame = tk.Frame(toolbar, bg="#e8e8e8")
    btn_frame.pack(side="left", padx=4)

    copy_sel_btn = ttk.Button(btn_frame, text="复制选中", state="disabled")
    copy_sel_btn.pack(side="left", padx=2)

    copy_all_btn = ttk.Button(btn_frame, text="复制全部", state="disabled")
    copy_all_btn.pack(side="left", padx=2)

    # ---- translation buttons ----
    ttk.Separator(btn_frame, orient="vertical").pack(side="left", fill="y", padx=4)

    btn_c2e = ttk.Button(btn_frame, text="中→EN", state="disabled")
    btn_c2e.pack(side="left", padx=2)

    btn_e2c = ttk.Button(btn_frame, text="EN→中", state="disabled")
    btn_e2c.pack(side="left", padx=2)

    # Translate state
    trans_state = {"direction": None, "text": ""}

    def do_translate(direction):
        """direction: 'c2e' or 'e2c' — runs in background thread."""
        if trans_state["direction"] == direction:
            return  # already translated this direction
        current_text = result.get("text", "").strip()
        if not current_text:
            return

        trans_state["direction"] = direction
        btn_c2e.configure(state="disabled")
        btn_e2c.configure(state="disabled")
        status_label.configure(text="翻译中...", fg="#666")
        # Re-show original + "翻译中" below
        _show_original_with_translation(None)

        def translate_async():
            t0 = time.time()
            try:
                if direction == "c2e":
                    translated = tr.chinese_to_english(current_text)
                else:
                    translated = tr.english_to_chinese(current_text)
                trans_state["text"] = translated
                elapsed = time.time() - t0
                win.after(0, lambda: _show_original_with_translation(translated))
                win.after(0, lambda: status_label.configure(
                    text=f"翻译完成 ({elapsed:.1f}s)", fg="#060"))
            except Exception as e:
                trans_state["direction"] = None
                win.after(0, lambda: _show_original_with_translation(None))
                win.after(0, lambda: status_label.configure(
                    text=f"翻译失败", fg="red"))
            win.after(0, lambda: btn_c2e.configure(state="normal"))
            win.after(0, lambda: btn_e2c.configure(state="normal"))

        threading.Thread(target=translate_async, daemon=True).start()

    btn_c2e.configure(command=lambda: do_translate("c2e"))
    btn_e2c.configure(command=lambda: do_translate("e2c"))

    ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=6)

    status_label = tk.Label(toolbar, text="预处理中...", bg="#e8e8e8", fg="#666",
                            font=("Microsoft YaHei UI", 9))
    status_label.pack(side="left", padx=4)

    close_btn = ttk.Button(toolbar, text="关闭")
    close_btn.pack(side="right", padx=4)

    # ---- main area ----
    main_pw = tk.PanedWindow(win, orient="horizontal", bg="#f0f0f0",
                             sashwidth=1, sashrelief="flat")
    main_pw.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    # Text area
    text_frame = tk.Frame(main_pw, bg="#f0f0f0")
    main_pw.add(text_frame, stretch="always")

    text_widget = tk.Text(text_frame, wrap="word", font=("Microsoft YaHei UI", 11),
                          padx=10, pady=10, relief="flat", borderwidth=0)
    text_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
    text_widget.configure(yscrollcommand=text_scroll.set)

    text_widget.pack(side="left", fill="both", expand=True)
    text_scroll.pack(side="right", fill="y")

    # Preview panel
    preview_frame = tk.Frame(main_pw, bg="#e0e0e0", width=120)
    main_pw.add(preview_frame, stretch="never")

    preview_label = tk.Label(preview_frame, text="截图\n预览", bg="#e0e0e0",
                             fg="#888", font=("Microsoft YaHei UI", 8),
                             justify="center")
    preview_label.pack(expand=True, fill="both")

    # Show thumbnail immediately
    try:
        ratio = min(100 / image.width, 80 / image.height, 1)
        tw, th = int(image.width * ratio), int(image.height * ratio)
        thumb = image.resize((tw, th), Image.LANCZOS)
        tk_thumb = ImageTk.PhotoImage(thumb)
        preview_label.configure(image=tk_thumb, text="")
        preview_label.image = tk_thumb
    except Exception:
        pass

    # Loading indicator
    text_widget.insert("1.0", "正在识别文字，请稍候...")
    text_widget.configure(state="disabled", fg="#999")

    # Thread-safe result: background thread writes here, main thread polls
    result = {"text": "", "error": None, "done": False,
              "elapsed": 0, "status": "预处理中..."}

    def do_ocr():
        t0 = time.time()
        try:
            result["status"] = "预处理中..."
            time.sleep(0.01)  # small yield so poller can update status

            result["status"] = "识别中..."
            result["text"] = ocr_engine.recognize(image)
        except Exception as e:
            result["error"] = str(e)
        result["elapsed"] = time.time() - t0
        result["done"] = True

    # Start OCR in background
    threading.Thread(target=do_ocr, daemon=True).start()

    # Poll from main thread (avoids Tkinter thread-safety issues)
    def poll_result():
        if not win.winfo_exists():
            return

        # Update status
        cur_status = result.get("status", "")
        if cur_status and status_label.cget("text") != cur_status:
            status_label.configure(text=cur_status)

        if result["done"]:
            _on_ocr_done()
        else:
            # Poll every 100ms
            status_label.after(100, poll_result)

    def _on_ocr_done():
        text_widget.configure(state="normal", fg="#000")
        text_widget.delete("1.0", "end")

        if result["error"]:
            text_widget.insert("1.0", f"识别失败: {result['error']}")
            status_label.configure(text="识别失败", fg="red")
        elif not result["text"].strip():
            text_widget.insert("1.0", "(未识别到文字)\n\n"
                               "提示：请确保截图区域包含清晰的文字，\n"
                               "避免选择图标、图片等非文字内容。")
            status_label.configure(text="无文字", fg="#c00")
        else:
            text_widget.insert("1.0", result["text"])
            elapsed = result.get("elapsed", 0)
            word_count = len(result["text"])
            status_label.configure(
                text=f"共 {word_count} 字 | 耗时 {elapsed:.1f}s",
                fg="#333")
            copy_sel_btn.configure(state="normal")
            copy_all_btn.configure(state="normal")
            btn_c2e.configure(state="normal")
            btn_e2c.configure(state="normal")

    def _show_original_with_translation(translated):
        text_widget.configure(state="normal")
        text_widget.delete("1.0", "end")
        text_widget.insert("1.0", result["text"] if result.get("text") else "")
        if translated is not None:
            text_widget.insert("end", "\n\n─── 翻译 ───\n")
            text_widget.insert("end", translated)
        text_widget.configure(state="normal")

    def copy_selected():
        try:
            sel = text_widget.get("sel.first", "sel.last")
            if sel:
                set_text_to_clipboard(sel)
                status_label.configure(text="已复制选中文字", fg="#060")
        except tk.TclError:
            all_text = text_widget.get("1.0", "end-1c").strip()
            if all_text:
                set_text_to_clipboard(all_text)
                status_label.configure(text="已复制全部文字", fg="#060")

    def copy_all():
        all_text = text_widget.get("1.0", "end-1c").strip()
        if all_text:
            set_text_to_clipboard(all_text)
            status_label.configure(text="已复制全部文字", fg="#060")

    def do_close():
        # Prevent further polling
        result["done"] = True
        win.destroy()
        root.destroy()

    copy_sel_btn.configure(command=copy_selected)
    copy_all_btn.configure(command=copy_all)
    close_btn.configure(command=do_close)

    win.bind("<Control-c>", lambda e: copy_selected())
    win.bind("<Escape>", lambda e: do_close())
    win.protocol("WM_DELETE_WINDOW", do_close)

    # Center window
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    ww = win.winfo_width()
    wh = win.winfo_height()
    x = (sw - ww) // 2
    y = (sh - wh) // 2
    win.geometry(f"+{x}+{y}")

    # Start polling (always from main thread)
    poll_result()

    root.wait_window(win)
    root.destroy()


def _show_error(msg):
    import tkinter.messagebox as mb
    mb.showerror("OCR 不可用", msg)
