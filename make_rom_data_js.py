import base64
import json

with open('Boulder Dash.nes', 'rb') as f:
    rom_bytes = f.read()

rom_b64 = base64.b64encode(rom_bytes).decode('ascii')

with open('levels_dump.json', 'r') as f:
    dump = json.load(f)

with open('tiles_library.json', 'r') as f:
    tiles = json.load(f)

js_content = f"""// Pre-bundled Boulder Dash ROM and Level Data for Standalone / Offline Execution
window.DEFAULT_ROM_BASE64 = "{rom_b64}";
window.DEFAULT_LEVELS_DUMP = {json.dumps(dump)};
window.DEFAULT_TILES_LIBRARY = {json.dumps(tiles)};
"""

with open('web/rom_data.js', 'w') as f:
    f.write(js_content)

print(f"Generated web/rom_data.js (size: {len(js_content)} bytes)")
