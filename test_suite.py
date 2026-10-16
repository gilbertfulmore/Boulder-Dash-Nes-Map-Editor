import os
import shutil
import json
from boulder_rom import BoulderDashROM

def run_tests():
    print("=== Boulder Dash NES Map Editor Test Suite ===")
    
    # 1. Test BoulderDashROM initialization
    rom = BoulderDashROM("Boulder Dash.nes", "levels_dump.json")
    assert len(rom.levels_meta) == 24, f"Expected 24 levels, got {len(rom.levels_meta)}"
    print("✓ Successfully loaded 24 level metadata entries")

    # 2. Test reading all 24 levels
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

    # 3. Test modifying and saving Level 0
    test_rom_path = "test_patch.nes"
    shutil.copyfile("Boulder Dash.nes", test_rom_path)
    
    test_rom = BoulderDashROM(test_rom_path, "levels_dump.json")
    orig_lvl0 = test_rom.get_level(0)
    
    # Create modified level data
    modified_grid = [row[:] for row in orig_lvl0['grid']]
    # Place diamonds in row 5, cols 10..15
    for c in range(10, 16):
        modified_grid[5][c] = 8 # Diamond
        
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
    print("✓ Committed modifications to test_patch.nes")
    
    # Reload test_patch.nes fresh from disk
    reloaded_rom = BoulderDashROM(test_rom_path, "levels_dump.json")
    reloaded_lvl0 = reloaded_rom.get_level(0)
    
    assert reloaded_lvl0['diamonds_needed'] == 42, f"Diamonds mismatch: {reloaded_lvl0['diamonds_needed']}"
    assert reloaded_lvl0['time_limit'] == 199, f"Time mismatch: {reloaded_lvl0['time_limit']}"
    assert reloaded_lvl0['start_x'] == 5, f"StartX mismatch: {reloaded_lvl0['start_x']}"
    assert reloaded_lvl0['start_y'] == 6, f"StartY mismatch: {reloaded_lvl0['start_y']}"
    assert reloaded_lvl0['password'] == '123456', f"Password mismatch: {reloaded_lvl0['password']}"
    
    for c in range(10, 16):
        assert reloaded_lvl0['grid'][5][c] == 8, f"Grid tile mismatch at (5, {c}): {reloaded_lvl0['grid'][5][c]}"
        
    print("✓ Reloaded patched ROM: All modified fields (tiles, diamonds, time, spawn, password) match 100%!")
    
    # Clean up test file
    if os.path.exists(test_rom_path):
        os.remove(test_rom_path)
    if os.path.exists(test_rom_path + ".original.bak"):
        os.remove(test_rom_path + ".original.bak")

    # 4. Verify tiles library
    with open("tiles_library.json", "r") as f:
        tiles = json.load(f)
    world_keys = [k for k in tiles if k.isdigit()]
    assert len(world_keys) == 6, f"Expected 6 worlds, got {len(world_keys)}"
    assert 'rockford' in tiles, "Expected rockford sprite in tiles library"
    for w in range(6):
        w_tiles = tiles[str(w)]
        assert len(w_tiles) == 16, f"World {w}: expected 16 tiles, got {len(w_tiles)}"
        for t in w_tiles:
            assert t['image'].startswith("data:image/png;base64,"), f"Invalid data URI for tile {t['id']}"
    print("✓ Tiles library validated: 96 base64 PNG tiles across 6 worlds + Rockford sprite")

    print("\n🎉 ALL TESTS PASSED SUCCESSFULLY! The Map Editor backend & ROM engine are rock solid!")

if __name__ == "__main__":
    run_tests()
