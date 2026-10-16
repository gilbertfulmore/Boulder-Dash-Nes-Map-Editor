import struct
import json
from pure_png import write_png
from test_chr import decode_8x8_tile, NES_PALETTE

with open('levels_dump.json', 'r') as f:
    dump = json.load(f)

levels = dump['levels']

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# Authentic Metatile Pointers from NES PRG 0x7370 ($F370)
pointers = []
for i in range(16):
    lo = prg[0x7370 + i * 2]
    hi = prg[0x7370 + i * 2 + 1]
    pointers.append((lo | (hi << 8)) - 0x8000)

# Authentic Subpalette Table from NES PRG 0x7440 ($F440)
subpalette_map = [prg[0x7440 + nib] & 3 for nib in range(16)]

# Authentic World Palettes from NES PRG 0x3c22 ($BC22)
world_palettes = []
for w in range(6):
    pal_off = 0x3c22 + w * 16
    wpal = [
        [prg[pal_off + s * 4 + c] for c in range(4)]
        for s in range(4)
    ]
    world_palettes.append(wpal)

def get_chr_tile(tile_idx):
    off = tile_idx * 16
    return decode_8x8_tile(chr_rom[off:off+16])

def render_level_image(lvl, filename):
    grid = lvl['grid'] # 22 rows x 40 cols
    world_idx = lvl['world'] - 1
    pals = world_palettes[world_idx]
    
    img_w = 40 * 16
    img_h = 22 * 16
    pixels = bytearray(img_w * img_h * 3)
    
    for r in range(22):
        for c in range(40):
            nib = grid[r][c]
            if nib in [8, 9, 10, 13, 14, 15]:
                ptr = pointers[nib]
            else:
                ptr = pointers[nib] + world_idx * 4
                
            tl, tr, bl, br = prg[ptr : ptr + 4]
            sub = subpalette_map[nib]
            pal = pals[sub]
            
            tl_t = get_chr_tile(tl)
            tr_t = get_chr_tile(tr)
            bl_t = get_chr_tile(bl)
            br_t = get_chr_tile(br)
            
            base_x = c * 16
            base_y = r * 16
            
            for y in range(8):
                for x in range(8):
                    color = NES_PALETTE[pal[tl_t[y][x]]]
                    px = (base_y + y) * img_w + (base_x + x)
                    pixels[px*3 : px*3+3] = bytes(color)
                for x in range(8):
                    color = NES_PALETTE[pal[tr_t[y][x]]]
                    px = (base_y + y) * img_w + (base_x + x + 8)
                    pixels[px*3 : px*3+3] = bytes(color)
                    
            for y in range(8):
                for x in range(8):
                    color = NES_PALETTE[pal[bl_t[y][x]]]
                    px = (base_y + y + 8) * img_w + (base_x + x)
                    pixels[px*3 : px*3+3] = bytes(color)
                for x in range(8):
                    color = NES_PALETTE[pal[br_t[y][x]]]
                    px = (base_y + y + 8) * img_w + (base_x + x + 8)
                    pixels[px*3 : px*3+3] = bytes(color)

    write_png(filename, img_w, img_h, bytes(pixels))
    print(f"Rendered {lvl['name']} to {filename}")

# Render World 1-1 to World 6-1
for w in range(6):
    lvl = levels[w * 4]
    render_level_image(lvl, f"level_{w+1}_1.png")
