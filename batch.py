"""Translate every image in a folder, resuming safely after interruptions.

Each finished page is saved as TL/<original name>.png, and (by default) the
original is then moved into an "Originals" sub-folder. The input folder only
ever holds pages that still need translating, so if a run fails part-way you
can just select the same folder again and it picks up where it left off.
"""

import os
import re
import shutil

import requests

from cotrans import Cancelled, translate_image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
OUTPUT_DIR_NAME = "TL"
ORIGINALS_DIR_NAME = "Originals"


def natural_key(name):
    """Sort "2.png" before "10.png"."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def list_images(folder):
    names = [
        name for name in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, name))
        and os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS
    ]
    return sorted(names, key=natural_key)


def output_name(name, names):
    stem = os.path.splitext(name)[0]
    # Keep "a.jpg" and "a.png" from overwriting each other's translation.
    if sum(os.path.splitext(other)[0] == stem for other in names) > 1:
        stem = name.replace(".", "_")
    return stem + ".png"


def move_original(src, originals_dir):
    os.makedirs(originals_dir, exist_ok=True)
    dest = os.path.join(originals_dir, os.path.basename(src))
    stem, ext = os.path.splitext(dest)
    n = 1
    while os.path.exists(dest):
        dest = f"{stem} ({n}){ext}"
        n += 1
    shutil.move(src, dest)


def translate_folder(
    folder,
    options,
    move_originals=True,
    attempts=3,
    on_progress=None,
    on_status=None,
    on_log=None,
    should_stop=None,
):
    """Translate all images in `folder`. Returns (translated, failed) lists of file names."""
    log = on_log or print
    output_dir = os.path.join(folder, OUTPUT_DIR_NAME)
    originals_dir = os.path.join(folder, ORIGINALS_DIR_NAME)
    os.makedirs(output_dir, exist_ok=True)

    names = list_images(folder)
    # Include already-moved originals so output names stay stable across resumed runs.
    all_names = set(names) | set(list_images(originals_dir) if os.path.isdir(originals_dir) else [])
    total = len(names)
    translated, failed = [], []
    session = requests.Session()
    if total == 0:
        log("No untranslated images found.")

    for index, name in enumerate(names):
        if should_stop and should_stop():
            log("Stopped.")
            break
        if on_progress:
            on_progress(index, total, name)
        src = os.path.join(folder, name)
        dest = os.path.join(output_dir, output_name(name, all_names))

        if os.path.exists(dest):
            # Translated on an earlier run that was interrupted before the move.
            log(f"{name}: already translated, skipping")
        else:
            for attempt in range(1, attempts + 1):
                try:
                    translate_image(src, dest, options, session=session,
                                    on_status=on_status, should_stop=should_stop)
                    break
                except Cancelled:
                    log("Stopped.")
                    return translated, failed
                except Exception as e:
                    log(f"{name}: attempt {attempt}/{attempts} failed: {e}")
            else:
                failed.append(name)
                continue
            log(f"{name}: done")

        translated.append(name)
        if move_originals:
            move_original(src, originals_dir)

    if on_progress:
        on_progress(len(translated) + len(failed), total, "")
    return translated, failed
