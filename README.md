# Auto-Cotrans
A Tool used to Translate folders of images with [Cotrans](https://github.com/VoileLabs/cotrans).

Earlier versions drove the Cotrans website through Selenium, which broke whenever the page changed. It now talks directly to the public API the website itself uses (`api.cotrans.touhou.ai`), so no browser or Chromedriver is needed.

## Requirements:
 - Python 3.8+ with Tkinter (included with the standard Windows/macOS installers)
 - `pip install -r requirements.txt` (requests, Pillow, tqdm)

## Execution:
### GUI
  - `python gui.py`
  - Browse to the Input Folder, choose the Cotrans options, and press **Translate**
  - Your choices are remembered for next time (stored in `~/.auto-cotrans.json`)

### Command line
  - `python script.py` — select the Input Folder in File-Explorer, using your saved (or the default) options
  - `python script.py "path/to/folder" --translator deepl --size L` — see `python script.py --help` for all options

## Options
| Option | Values | Default |
| --- | --- | --- |
| Language | CHS, CHT, CSY, NLD, ENG, FRA, DEU, HUN, ITA, JPN, KOR, PLK, PTB, ROM, RUS, ESP, TRK, UKR, VIN | ENG |
| Detection Resolution | S (1024px), M (1536px), L (2048px), X (2560px) | X |
| Text Detector | default, ctd (Comic Text Detector) | ctd |
| Text Direction | default (follow language), auto (follow image), h, v | auto |
| Translator | gpt3.5, youdao, baidu, google, deepl, papago, offline, none, original | gpt3.5 |

## Output & Resuming
  - Each translated page is saved to a `TL` folder inside the Input Folder, named after the original (`page01.jpg` → `TL/page01.png`)
  - Once a page is translated, its original is moved into an `Originals` folder inside the Input Folder
  - If a run fails or is stopped part-way, simply select the same Input Folder again: only the pages still left in it are translated
  - Pages that fail (after 3 attempts) are left in place and reported, so re-running retries just those
  - Use the checkbox in the GUI (or `--keep-originals`) to leave originals where they are
