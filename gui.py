"""Windowed version of Auto-Cotrans: python gui.py"""

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from batch import ORIGINALS_DIR_NAME, OUTPUT_DIR_NAME, translate_folder
from cotrans import OPTION_TABLES
from settings import load_settings, save_settings

OPTION_LABELS = {
    "target_language": "Language",
    "size": "Detection resolution",
    "detector": "Text detector",
    "direction": "Text direction",
    "translator": "Translator",
}


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto-Cotrans")
        self.minsize(520, 460)
        self.settings = load_settings()
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.worker = None

        frame = ttk.Frame(self, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)

        # Folder picker
        ttk.Label(frame, text="Folder").grid(row=0, column=0, sticky="w", pady=4)
        self.folder_var = tk.StringVar(value=self.settings["last_folder"])
        ttk.Entry(frame, textvariable=self.folder_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(frame, text="Browse…", command=self.browse).grid(row=0, column=2)

        # Cotrans options: one dropdown per menu on the website
        self.option_boxes = {}
        for row, (key, table) in enumerate(OPTION_TABLES.items(), start=1):
            ttk.Label(frame, text=OPTION_LABELS[key]).grid(row=row, column=0, sticky="w", pady=4)
            box = ttk.Combobox(frame, values=list(table.values()), state="readonly")
            box.set(table[self.settings[key]])
            box.grid(row=row, column=1, columnspan=2, sticky="ew", padx=6)
            self.option_boxes[key] = box

        row = len(OPTION_TABLES) + 1
        self.move_var = tk.BooleanVar(value=self.settings["move_originals"])
        ttk.Checkbutton(
            frame, variable=self.move_var,
            text=f"Move translated originals into an '{ORIGINALS_DIR_NAME}' folder (enables resuming)",
        ).grid(row=row, column=0, columnspan=3, sticky="w", pady=(8, 4))

        # Start / stop
        buttons = ttk.Frame(frame)
        buttons.grid(row=row + 1, column=0, columnspan=3, sticky="ew", pady=6)
        self.start_button = ttk.Button(buttons, text="Translate", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Stop", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=6)
        self.open_button = ttk.Button(buttons, text="Open output folder", command=self.open_output)
        self.open_button.pack(side="right")

        # Progress
        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.grid(row=row + 2, column=0, columnspan=3, sticky="ew", pady=(6, 2))
        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(frame, textvariable=self.status_var).grid(row=row + 3, column=0, columnspan=3, sticky="w")

        # Log
        frame.rowconfigure(row + 4, weight=1)
        self.log_text = tk.Text(frame, height=10, state="disabled", wrap="word")
        self.log_text.grid(row=row + 4, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after(100, self.poll_events)

    def browse(self):
        folder = filedialog.askdirectory(title="Select a folder", initialdir=self.folder_var.get() or None)
        if folder:
            self.folder_var.set(folder)

    def selected_options(self):
        options = {}
        for key, table in OPTION_TABLES.items():
            label = self.option_boxes[key].get()
            options[key] = next(value for value, text in table.items() if text == label)
        return options

    def start(self):
        folder = self.folder_var.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Auto-Cotrans", "Please select a valid folder.")
            return
        options = self.selected_options()
        self.settings.update(options, move_originals=self.move_var.get(), last_folder=folder)
        save_settings(self.settings)

        self.stop_event.clear()
        self.set_running(True)
        self.log(f"Translating {folder}")
        self.worker = threading.Thread(
            target=self.run, args=(folder, options, self.move_var.get()), daemon=True)
        self.worker.start()

    def run(self, folder, options, move_originals):
        # Runs on a background thread; talk to the UI only through the queue.
        try:
            translated, failed = translate_folder(
                folder,
                options,
                move_originals=move_originals,
                on_progress=lambda done, total, name: self.events.put(("progress", done, total, name)),
                on_status=lambda text: self.events.put(("status", text)),
                on_log=lambda text: self.events.put(("log", text)),
                should_stop=self.stop_event.is_set,
            )
            summary = f"Translated {len(translated)} file(s)."
            if failed:
                summary += f" {len(failed)} failed and were left in the folder; press Translate to retry."
            self.events.put(("done", summary))
        except Exception as e:
            self.events.put(("done", f"Error: {e}"))

    def poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "progress":
                    _, done, total, name = event
                    self.progress.configure(maximum=max(total, 1), value=done)
                    if name:
                        self.status_var.set(f"{done + 1}/{total}: {name}")
                elif kind == "status":
                    current = self.status_var.get().split(" — ")[0]
                    self.status_var.set(f"{current} — {event[1]}")
                elif kind == "log":
                    self.log(event[1])
                elif kind == "done":
                    self.log(event[1])
                    self.status_var.set(event[1])
                    self.set_running(False)
        except queue.Empty:
            pass
        self.after(100, self.poll_events)

    def stop(self):
        self.stop_event.set()
        self.stop_button.configure(state="disabled")
        self.status_var.set("Stopping…")

    def set_running(self, running):
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")
        for box in self.option_boxes.values():
            box.configure(state="disabled" if running else "readonly")

    def log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def open_output(self):
        path = os.path.join(self.folder_var.get(), OUTPUT_DIR_NAME)
        if not os.path.isdir(path):
            messagebox.showinfo("Auto-Cotrans", "Nothing has been translated in this folder yet.")
            return
        if os.name == "nt":
            os.startfile(path)
        else:
            import subprocess
            import sys
            subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])

    def on_close(self):
        self.stop_event.set()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
