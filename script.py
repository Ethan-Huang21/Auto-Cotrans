"""Command-line version of Auto-Cotrans.

    python script.py                     # pick a folder, use saved/default options
    python script.py "C:/manga/ch1" --translator deepl --size L

Run `python script.py --help` for every option; use gui.py for the windowed app.
"""

import argparse

from tqdm import tqdm

from batch import translate_folder
from cotrans import OPTION_TABLES
from settings import load_settings, save_settings


def select_folder():
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select a folder")
    root.destroy()
    return folder


def main():
    settings = load_settings()
    parser = argparse.ArgumentParser(description="Translate a folder of images with Cotrans.")
    parser.add_argument("folder", nargs="?", help="folder of images (asks if omitted)")
    for key, table in OPTION_TABLES.items():
        parser.add_argument(f"--{key.replace('_', '-')}", dest=key, choices=list(table),
                            default=settings[key], help=f"default: {settings[key]}")
    parser.add_argument("--keep-originals", action="store_true",
                        help="don't move translated originals into the 'Originals' folder")
    args = parser.parse_args()

    folder = args.folder or select_folder()
    if not folder:
        return
    options = {key: getattr(args, key) for key in OPTION_TABLES}
    save_settings(dict(settings, **options, last_folder=folder))
    print(folder)

    bar = tqdm(desc="Translating Files...")

    def on_progress(done, total, name):
        bar.total = total
        bar.n = done
        bar.set_postfix_str(name)
        bar.refresh()

    translated, failed = translate_folder(
        folder,
        options,
        move_originals=not args.keep_originals,
        on_progress=on_progress,
        on_log=bar.write,
    )
    bar.close()
    print(f"Translated {len(translated)} file(s).")
    if failed:
        print(f"{len(failed)} file(s) failed and were left in place; run again to retry: {', '.join(failed)}")


if __name__ == "__main__":
    main()
