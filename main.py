import tkinter as tk
import threading
import keyboard
import pyperclip
import deepl
import time
import json

# =========================
# KONFIG PLIKU
# =========================
CONFIG_FILE = "config.json"

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {
            "hotkey": "f2",
            "x": 20,
            "y": 20,
            "auto": True
        }

# =========================
# DEEPL
# =========================
API_KEY = "" 
translator = deepl.Translator(API_KEY, server_url="https://api-free.deepl.com")

# =========================
# OVERLAY
# =========================
class OverlayTranslator:
    def __init__(self, root, config):
        self.root = root
        self.config = config

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.0)
        self.root.configure(bg='black')

        self.label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 22, "bold"),
            fg="#00FFAA",
            bg="black",
            wraplength=700,
            justify="center"
        )
        self.label.pack(padx=25, pady=20)

        self.label.bind("<ButtonPress-1>", self.start_move)
        self.label.bind("<B1-Motion>", self.do_move)

        self.root.withdraw()

        self.last_clipboard = ""

        # HOTKEY
        keyboard.add_hotkey(
            config["hotkey"],
            lambda: threading.Thread(target=self.translate_action, daemon=True).start()
        )

        # AUTO MODE
        if config["auto"]:
            threading.Thread(target=self.monitor_clipboard, daemon=True).start()

        # EXIT
        threading.Thread(target=self.exit_listener, daemon=True).start()

    # =========================
    # DRAG
    # =========================
    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    # =========================
    # TRANSLATE
    # =========================
    def translate_action(self):
        time.sleep(0.15)
        text = pyperclip.paste().strip()

        if not text or len(text) < 3:
            return

        try:
            result = translator.translate_text(text, target_lang="PL")
            self.root.after(0, self.show_text, result.text)
        except Exception as e:
            self.root.after(0, self.show_text, f"Błąd: {e}")

    # =========================
    # UI SHOW
    # =========================
    def show_text(self, text):
        self.label.config(text=text)
        self.root.deiconify()
        self.fade_in()
        self.root.after(3500, self.fade_out)

    def fade_in(self):
        alpha = self.root.attributes("-alpha")
        if alpha < 0.9:
            alpha += 0.05
            self.root.attributes("-alpha", alpha)
            self.root.after(30, self.fade_in)

    def fade_out(self):
        alpha = self.root.attributes("-alpha")
        if alpha > 0:
            alpha -= 0.05
            self.root.attributes("-alpha", alpha)
            self.root.after(30, self.fade_out)
        else:
            self.root.withdraw()

    # =========================
    # AUTO CLIPBOARD
    # =========================
    def monitor_clipboard(self):
        while True:
            try:
                text = pyperclip.paste()
                if text != self.last_clipboard:
                    self.last_clipboard = text
                    threading.Thread(target=self.translate_action, daemon=True).start()
                time.sleep(0.4)
            except:
                pass

    # =========================
    # EXIT
    # =========================
    def exit_listener(self):
        keyboard.wait('esc')
        self.root.quit()


# =========================
# CONFIG WINDOW
# =========================
class ConfigWindow:
    def __init__(self, root, on_start):
        self.root = root
        self.on_start = on_start

        self.root.title("Translator HUD Setup")
        self.root.geometry("320x260")

        config = load_config()

        tk.Label(root, text="Hotkey:").pack()
        self.hotkey_entry = tk.Entry(root)
        self.hotkey_entry.insert(0, config["hotkey"])
        self.hotkey_entry.pack()

        self.auto_var = tk.BooleanVar(value=config["auto"])
        tk.Checkbutton(root, text="Auto translate clipboard", variable=self.auto_var).pack(pady=5)

        tk.Label(root, text="HUD Position X:").pack()
        self.x_entry = tk.Entry(root)
        self.x_entry.insert(0, config["x"])
        self.x_entry.pack()

        tk.Label(root, text="HUD Position Y:").pack()
        self.y_entry = tk.Entry(root)
        self.y_entry.insert(0, config["y"])
        self.y_entry.pack()

        tk.Button(root, text="START", command=self.start).pack(pady=15)

    def start(self):
        config = {
            "hotkey": self.hotkey_entry.get(),
            "auto": self.auto_var.get(),
            "x": int(self.x_entry.get()),
            "y": int(self.y_entry.get())
        }

        save_config(config)
        self.root.destroy()
        self.on_start(config)


# =========================
# START APP
# =========================
def start_overlay(config):
    root = tk.Tk()
    app = OverlayTranslator(root, config)
    root.geometry(f"+{config['x']}+{config['y']}")
    root.mainloop()


if __name__ == "__main__":
    def launch(config):
        start_overlay(config)

    root = tk.Tk()
    ConfigWindow(root, launch)
    root.mainloop()
