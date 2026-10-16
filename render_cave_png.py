import struct
import zlib
from pure_png import write_png
from test_chr import decode_8x8_tile, NES_PALETTE

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# Level 1-1
cave_off = 34832
cave_bytes = rom[cave_off:cave_off+440]

tsa_off = 0x73a0
tsa_blocks = []
for i in range(44):
    tl, tr, bl, br = prg[tsa_off + i*4 : tsa_off + (i+1)*4]
    tsa_blocks.append((tl, tr, bl, br))

# World 0 subpalettes
world0_pals = [
    [prg[0x3c32 + 4*p + c] for c in range(4)]
    for p in range(4)
]

# Mapping of 16 nibble types to (tsa_block_idx, subpalette) for World 0:
# WorldBlocks0:
# Nibble 0: Block 0, subpal 0 (Empty)
# Nibble 1: Block 0, subpal 0 (Empty)
# Nibble 2: Block 6, subpal 1 (Dirt)
# Nibble 3: Block 12, subpal 0 (Steel Wall)
# Nibble 4: Block 20, subpal 3 (Magic Wall)
# Nibble 5: Block 12, subpal 3 (Brick/Wall Line)
# Nibble 6: Block 12, subpal 0
# Nibble 7: Block 21, subpal 2 (Rock)
# Nibble 8: Block 27, subpal 0 (Diamond)
# Nibble 9: Block 28, subpal 3 (Firefly)
# Nibble 10: Block 29, subpal 2 (Butterfly)
# Nibble 11: Block 30, subpal 1 (Amoeba)
# Nibble 12: Block 36, subpal 0 (Exit)
# Nibble 13: Block 42, subpal 0 (Special)

NIBBLE_MAP = {
    0: (0, 0),
    1: (0, 0),
    2: (6, 1),
    3: (12, 0),
    4: (20, 3),
    5: (12, 3),
    6: (12, 0),
    7: (21, 2),
    8: (27, 0),
    9: (28, 3),
    10: (29, 2),
    11: (30, 1),
    12: (36, 0),
    13: (42, 0),
    14: (42, 0),
    15: (43, 0),
}

def get_chr_tile(tile_idx):
    off = tile_idx * 16
    return decode_8x8_tile(chr_rom[off:off+16])

def render_block(block_idx, subpal):
    tl, tr, bl, br = tsa_blocks[block_idx]
    tl_t = get_chr_tile(tl)
    tr_t = get_chr_tile(tr)
    bl_t = get_chr_tile(bl)
    br_t = get_chr_tile(br)
    
    img = []
    # top 8 rows
    for y in range(8):
        row = []
        for x in range(8):
            row.append(NES_PALETTE[world0_pals[subpal][tl_t[y][x]]] + (255,))
        for x in range(8):
            row.append(NES_PALETTE[world0_pals[subpal][tr_t[y][x]]] + (255,))
        img.append(row)
    # bottom 8 rows
    for y in range(8):
        row = []
        for x in range(8):
            row.append(NES_PALETTE[world0_pals[subpal][bl_t[y][x]]] + (255,))
        for x in range(8):
            row.append(NES_PALETTE[world0_pals[subpal][br_t[y][x]]] + (255,))
        img.append(row)
    return img

# Pre-render all 16 nibble blocks
rendered_nibbles = {}
for nib, (b_idx, sub) in NIBBLE_MAP.items():
    rendered_nibbles[nib] = render_block(b_idx, sub)

# Render 40 cols x 22 rows = 640 x 352 pixels
width = 40 * 16
height = 22 * 16
cave_img = bytearray(width * height * 4)

for r in range(22):
    row_bytes = cave_bytes[r*20:(r+1)*20]
    for c_idx in range(20):
        b = row_bytes[c_idx]
        col_tiles = [b & 0x0f, (b >> 4) & 0x0f]
        for sub_c in range(2):
            c = c_idx * 2 + sub_c
            tile_nib = col_tiles[sub_c]
            block_img = rendered_nibbles[tile_nib]
            for py in range(16):
                for px in range(16):
                    x = c * 16 + px
                    y = r * 16 + py
                    pos = (y * width + x) * 4
                    r_val, g_val, b_val, a_val = block_img[py][px]
                    cave_img[pos:pos+4] = bytes([r_val, g_val, b_val, a_val])

write_png('cave1_1.png', width, height, cave_img)
print("Saved cave1_1.png (640x352) successfully!")
