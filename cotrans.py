"""Minimal client for the Cotrans translation API.

The Cotrans website (https://cotrans.touhou.ai) is a thin front-end over a
public HTTP API. Talking to that API directly avoids Selenium entirely, so the
script no longer breaks whenever the page layout or element IDs change.

API reference (from the Cotrans source, https://github.com/VoileLabs/cotrans):
  PUT  /task/upload/v1        multipart form -> {"id", "status", "result"?}
  GET  /task/<id>/status/v1   -> {"type": "pending" | "status" | "result" | "error" | "not_found", ...}
The result holds a URL to a transparent "translation mask" PNG, which is laid
over the original image to produce the translated page.
"""

import base64
import io
import mimetypes
import os
import time

import requests
from PIL import Image

API_BASE = "https://api.cotrans.touhou.ai"

# Option tables: API value -> label shown on the Cotrans website.
LANGUAGES = {
    "CHS": "简体中文",
    "CHT": "繁體中文",
    "CSY": "čeština",
    "NLD": "Nederlands",
    "ENG": "English",
    "FRA": "français",
    "DEU": "Deutsch",
    "HUN": "magyar nyelv",
    "ITA": "italiano",
    "JPN": "日本語",
    "KOR": "한국어",
    "PLK": "polski",
    "PTB": "português",
    "ROM": "limba română",
    "RUS": "русский язык",
    "ESP": "español",
    "TRK": "Türk dili",
    "UKR": "українська",
    "VIN": "Tiếng Việt",
}
SIZES = {
    "S": "1024px",
    "M": "1536px",
    "L": "2048px",
    "X": "2560px",
}
DETECTORS = {
    "default": "Default",
    "ctd": "Comic Text Detector",
}
DIRECTIONS = {
    "default": "Follow language",
    "auto": "Follow image",
    "h": "All horizontal",
    "v": "All vertical",
}
TRANSLATORS = {
    "gpt3.5": "GPT-3.5",
    "youdao": "Youdao",
    "baidu": "Baidu",
    "google": "Google",
    "deepl": "DeepL",
    "papago": "Papago",
    "offline": "Sugoi / M2M100",
    "none": "Remove text",
    "original": "Untranslated",
}

# The settings the original script had hard-coded.
DEFAULT_OPTIONS = {
    "target_language": "ENG",
    "size": "X",
    "detector": "ctd",
    "direction": "auto",
    "translator": "gpt3.5",
}

OPTION_TABLES = {
    "target_language": LANGUAGES,
    "size": SIZES,
    "detector": DETECTORS,
    "direction": DIRECTIONS,
    "translator": TRANSLATORS,
}

FILE_SIZE_LIMIT = 20 * 1024 * 1024


class CotransError(Exception):
    pass


class Cancelled(Exception):
    pass


def validate_options(options):
    for key, table in OPTION_TABLES.items():
        if options.get(key) not in table:
            raise ValueError(f"Invalid {key} {options.get(key)!r}; choose from {', '.join(table)}")


def submit(session, image_path, options, retry=False):
    """Upload an image and return the API's JSON response."""
    if os.path.getsize(image_path) >= FILE_SIZE_LIMIT:
        raise CotransError("File is larger than Cotrans' 20 MB limit")
    mime = mimetypes.guess_type(image_path)[0] or "application/octet-stream"
    data = {key: options[key] for key in OPTION_TABLES}
    data["mime"] = mime
    data["retry"] = "true" if retry else "false"
    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, mime)}
        res = session.put(f"{API_BASE}/task/upload/v1", data=data, files=files, timeout=120)
    try:
        body = res.json()
    except ValueError:
        body = None
    if not res.ok or not body or not body.get("id"):
        detail = (body or {}).get("error") if isinstance(body, dict) else None
        raise CotransError(f"Upload failed ({res.status_code}): {detail or res.text[:200]}")
    return body


def wait_for_result(session, task_id, on_status=None, timeout=600, should_stop=None):
    """Poll the task status until it finishes; return the translation mask URL."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if should_stop and should_stop():
            raise Cancelled()
        res = session.get(f"{API_BASE}/task/{task_id}/status/v1", timeout=30)
        res.raise_for_status()
        msg = res.json()
        kind = msg.get("type")
        if kind == "result":
            return msg["result"]["translation_mask"]
        if kind == "error":
            raise CotransError(f"Translation failed (error id: {msg.get('error_id')})")
        if kind == "not_found":
            raise CotransError(f"Task {task_id} not found")
        if on_status:
            on_status(f"In queue (position {msg['pos']})" if kind == "pending" else msg.get("status", ""))
        time.sleep(1)
    raise CotransError("Timed out waiting for translation")


def fetch_mask(session, mask_url):
    if mask_url.startswith("data:"):
        return Image.open(io.BytesIO(base64.b64decode(mask_url.split(",", 1)[1])))
    res = session.get(mask_url, timeout=60)
    res.raise_for_status()
    return Image.open(io.BytesIO(res.content))


def compose(image_path, mask):
    """Lay the translation mask over the original image, as the website does."""
    with Image.open(image_path) as original:
        page = original.convert("RGBA")
    mask = mask.convert("RGBA")
    if mask.size != page.size:
        mask = mask.resize(page.size, Image.LANCZOS)
    page.alpha_composite(mask)
    return page


def translate_image(image_path, output_path, options, session=None, on_status=None, should_stop=None):
    """Translate one image with Cotrans and save the result as a PNG."""
    session = session or requests.Session()
    if on_status:
        on_status("Uploading")
    task = submit(session, image_path, options)
    mask_url = (task.get("result") or {}).get("translation_mask")
    if not mask_url:
        mask_url = wait_for_result(session, task["id"], on_status=on_status, should_stop=should_stop)
    if on_status:
        on_status("Downloading")
    page = compose(image_path, fetch_mask(session, mask_url))
    # Write to a temporary name first so an interrupted save never looks finished.
    tmp_path = output_path + ".part"
    page.save(tmp_path, "PNG")
    os.replace(tmp_path, output_path)
