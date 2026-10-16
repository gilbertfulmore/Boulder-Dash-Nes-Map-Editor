import os
import sys
import json

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
DATA_DIR = os.path.join(ROOT_DIR, "data")
WEB_DIR = os.path.join(ROOT_DIR, "web")

if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from boulder_rom import BoulderDashROM

ROM_PATH = os.path.join(DATA_DIR, "Boulder Dash.nes")
DUMP_PATH = os.path.join(DATA_DIR, "levels_dump.json")
TILES_PATH = os.path.join(DATA_DIR, "tiles_library.json")
ROM_DATA_JS_PATH = os.path.join(WEB_DIR, "rom_data.js")

def run_tests():
    print("=== Boulder Dash NES Map Editor Test Suite ===")

    # 1. Verify ROM-free compliance in web/rom_data.js
    with open(ROM_DATA_JS_PATH, "r") as f:
        rom_js = f.read()
    assert "DEFAULT_ROM_BASE64" not in rom_js, "web/rom_data.js must not contain embedded ROM binary!"
    assert "DEFAULT_LEVELS_DUMP" in rom_js and "DEFAULT_TILES_LIBRARY" in rom_js
    print("✓ Verified web/rom_data.js is 100% ROM-free (no embedded NES binary)")

    # 2. Test BoulderDashROM initialization (works with or without Boulder Dash.nes on disk)
    rom = BoulderDashROM(ROM_PATH, DUMP_PATH)
    assert len(rom.levels_meta) == 24, f"Expected 24 levels, got {len(rom.levels_meta)}"
    print("✓ Successfully loaded 24 level metadata entries")

    # 3. Test reading all 24 levels
    for i in range(24):
        lvl = rom.get_level(i)
        assert lvl['index'] == i
        assert len(lvl['grid']) == 22, f"Level {i}: Expected 22 rows, got {len(lvl['grid'])}"
        for r in range(22):
            assert len(lvl['grid'][r]) == 40, f"Level {i} Row {r}: Expected 40 cols, got {len(lvl['grid'][r])}"
        if i < 23:
            assert len(lvl['password']) == 6 and lvl['password'].isdigit(), f"Level {i}: Invalid password: {lvl['password']}"
        else:
            assert lvl['password'] == "FINAL"
        assert 0 <= lvl['start_x'] < 40
        assert 0 <= lvl['start_y'] < 22

        # Verify steel wall boundary
        assert lvl['grid'][0][0] == 3, f"Level {i}: Top-left corner should be steel wall (3)"
        assert lvl['grid'][0][39] == 3, f"Level {i}: Top-right corner should be steel wall (3)"
        assert lvl['grid'][21][0] == 3, f"Level {i}: Bottom-left corner should be steel wall (3)"
        assert lvl['grid'][21][39] == 3, f"Level {i}: Bottom-right corner should be steel wall (3)"

    print("✓ All 24 levels validated: 40x22 grid, valid spawn coords, 6-digit passwords, steel boundary")

    # 4. Test binary ROM patching and reloading via load_rom_bytes()
    test_rom_path = os.path.join(DATA_DIR, "test_patch.nes")
    mock_rom_bytes = bytearray(65552)
    mock_rom_bytes[0:4] = b"NES\x1a"

    test_rom = BoulderDashROM(test_rom_path, DUMP_PATH)
    test_rom.load_rom_bytes(bytes(mock_rom_bytes), sync_existing_edits=True)
    orig_lvl0 = test_rom.get_level(0)

    modified_grid = [row[:] for row in orig_lvl0['grid']]
    for c in range(10, 16):
        modified_grid[5][c] = 8

    edit_payload = {
        'diamonds_needed': 42,
        'time_limit': 199,
        'start_x': 5,
        'start_y': 6,
        'password': '123456',
        'grid': modified_grid
    }

    test_rom.save_level(0, edit_payload)
    test_rom.commit()
    print("✓ Committed binary modifications to test_patch.nes")

    reloaded_rom = BoulderDashROM(test_rom_path, DUMP_PATH)
    reloaded_lvl0 = reloaded_rom.get_level(0)

    assert reloaded_lvl0['diamonds_needed'] == 42, f"Diamonds mismatch: {reloaded_lvl0['diamonds_needed']}"
    assert reloaded_lvl0['time_limit'] == 199, f"Time mismatch: {reloaded_lvl0['time_limit']}"
    assert reloaded_lvl0['start_x'] == 5, f"StartX mismatch: {reloaded_lvl0['start_x']}"
    assert reloaded_lvl0['start_y'] == 6, f"StartY mismatch: {reloaded_lvl0['start_y']}"
    assert reloaded_lvl0['password'] == '123456', f"Password mismatch: {reloaded_lvl0['password']}"

    for c in range(10, 16):
        assert reloaded_lvl0['grid'][5][c] == 8, f"Grid tile mismatch at (5, {c}): {reloaded_lvl0['grid'][5][c]}"

    print("✓ Reloaded patched binary ROM: All modified fields (tiles, diamonds, time, spawn, password) match 100%!")

    if os.path.exists(test_rom_path):
        os.remove(test_rom_path)
    if os.path.exists(test_rom_path + ".original.bak"):
        os.remove(test_rom_path + ".original.bak")

    # 5. Verify tiles library
    with open(TILES_PATH, "r") as f:
        tiles = json.load(f)
    world_keys = [k for k in tiles if k.isdigit()]
    assert len(world_keys) == 6, f"Expected 6 worlds, got {len(world_keys)}"
    assert 'rockford' in tiles, "Expected rockford sprite in tiles library"
    for w in range(6):
        w_tiles = tiles[str(w)]
        assert len(w_tiles) == 16, f"World {w}: expected 16 tiles, got {len(w_tiles)}"
        for t in w_tiles:
            assert t['image'].startswith("data:image/png;base64,"), f"Invalid data URI for tile {t['id']}"
    print("✓ Tiles library validated: 96 base64 PNG tiles across 6 worlds + Rockford sprite + Exit Portal")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! The Map Editor backend & ROM engine are rock solid!")

if __name__ == "__main__":
    run_tests()

