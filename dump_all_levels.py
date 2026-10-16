import json
from test_decrypt import DCPRijndaelCFB8, decrypt_val

c_quarry = DCPRijndaelCFB8('QUARRY')
c_floppy = DCPRijndaelCFB8('FLOPPY')

def decrypt_double(val_enc):
    step1 = decrypt_val(c_floppy, val_enc)
    step2 = decrypt_val(c_quarry, step1)
    return step2

with open('Data/AmericanData.dat', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

config = {}
curr_sec = ""
for line in lines:
    if line.startswith('['):
        curr_sec = decrypt_val(c_quarry, line[1:-1])
        config[curr_sec] = {}
    elif '=' in line:
        k_enc, v_enc = line.split('=', 1)
        k = decrypt_val(c_quarry, k_enc)
        v = decrypt_double(v_enc)
        config[curr_sec][k] = v

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

levels_data = []
for i in range(24):
    sec_name = f"LevelData{i}"
    sec = config.get(sec_name, {})
    name = sec.get('LevelName', f"World {i//4 + 1}-{i%4 + 1}")
    lvl_off = int(sec.get('LevelOffset', 0))
    crystal_off = int(sec.get('LevelCrystalOffset', 0))
    time_off = int(sec.get('LevelTimeOffset', 0))
    start_x_off = int(sec.get('LevelStartXOffset', 0))
    start_y_off = int(sec.get('LevelStartYOffset', 0))
    tileset = int(sec.get('LevelTileSet', 0))
    scroll_off = int(sec.get('LevelScrollDataOffset', 0))
    
    # Read properties from ROM
    # In NES ROM, file offset = PRG offset + 16 for PRG, or direct file offset
    # Notice: LevelOffset was directly in the file (e.g. 34832 = 0x8810)
    # What about crystal_off? Let's check:
    # In AmericanData: LevelCrystalOffset = 29284 (0x7264)
    # File offset: 29284 + 16 = 29300 (0x7274) OR 29284 direct?
    # Earlier we checked rom[29284] and found diamonds=10, time=120!
    # So 29284 is the EXACT FILE OFFSET in Boulder Dash.nes!
    
    diamonds = rom[crystal_off]
    time_limit = rom[time_off]
    start_x = rom[start_x_off]
    start_y = rom[start_y_off]
    
    # Read 440 bytes of cave map
    cave_bytes = rom[lvl_off : lvl_off + 440]
    
    # Unpack 40x22 tiles (low nibble first)
    grid = []
    for r in range(22):
        row = []
        for c_idx in range(20):
            b = cave_bytes[r * 20 + c_idx]
            row.append(b & 0x0f)
            row.append((b >> 4) & 0x0f)
        grid.append(row)
        
    levels_data.append({
        'index': i,
        'name': name,
        'world': i // 4 + 1,
        'cave': i % 4 + 1,
        'tileset': tileset,
        'level_offset': lvl_off,
        'crystal_offset': crystal_off,
        'time_offset': time_off,
        'start_x_offset': start_x_off,
        'start_y_offset': start_y_off,
        'scroll_offset': scroll_off,
        'diamonds_needed': diamonds,
        'time_limit': time_limit,
        'start_x': start_x,
        'start_y': start_y,
        'grid': grid
    })

print(f"Loaded all {len(levels_data)} levels!")
with open('levels_dump.json', 'w') as f:
    json.dump({'levels': levels_data, 'config': config}, f, indent=2)
print("Saved levels_dump.json successfully!")
