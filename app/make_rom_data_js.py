import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
WEB_DIR = os.path.join(ROOT_DIR, "web")

DUMP_PATH = os.path.join(DATA_DIR, "levels_dump.json")
TILES_PATH = os.path.join(DATA_DIR, "tiles_library.json")
OUTPUT_JS_PATH = os.path.join(WEB_DIR, "rom_data.js")

def build_rom_data_js():
    with open(DUMP_PATH, 'r') as f:
        dump = json.load(f)

    with open(TILES_PATH, 'r') as f:
        tiles = json.load(f)

    js_content = f"""// Pre-bundled Boulder Dash Level Metadata & Tile Library for Standalone / Offline Execution
// Note: No copyrighted NES ROM binary is bundled here. Use "Load ROM" in the editor to load your own Boulder Dash.nes file.
window.DEFAULT_LEVELS_DUMP = {json.dumps(dump)};
window.DEFAULT_TILES_LIBRARY = {json.dumps(tiles)};
"""

    with open(OUTPUT_JS_PATH, 'w') as f:
        f.write(js_content)

    print(f"Generated ROM-free web/rom_data.js (size: {len(js_content)} bytes)")

if __name__ == "__main__":
    build_rom_data_js()

