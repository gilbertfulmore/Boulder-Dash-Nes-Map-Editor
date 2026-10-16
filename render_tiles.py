import struct
import zlib
from pure_png import write_png
from test_chr import decode_8x8_tile, NES_PALETTE

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# TSA table: 44 blocks (each 4 bytes: TL, TR, BL, BR)
tsa_off = 0x73a0
tsa_blocks = []
for i in range(44):
    tl, tr, bl, br = prg[tsa_off + i*4 : tsa_off + (i+1)*4]
    tsa_blocks.append((tl, tr, bl, br))

# Palettes at 0x3c32
# World 0 subpalettes:
# Pal0 = 0 -> prg[0x3c32 : 0x3c36] = [0x0c, 0x20, 0x23, 0x13]
# Pal1 = 1 -> prg[0x3c36 : 0x3c3a] = [0x0c, 0x27, 0x17, 0x0f]
# Pal2 = 2 -> prg[0x3c3a : 0x3c3e] = [0x0c, 0x32, 0x22, 0x12]
# Pal3 = 3 -> prg[0x3c3e : 0x3c42] = [0x0c, 0x38, 0x12, 0x0f]

world0_pals = [
    [prg[0x3c32 + 4*p + c] for c in range(4)]
    for p in range(4)
]

# CHR bank 0 for tiles:
# 8x8 tile is 16 bytes.
def get_chr_tile(tile_idx):
    off = tile_idx * 16
    return decode_8x8_tile(chr_rom[off:off+16])

def render_16x16(tl_idx, tr_idx, bl_idx, br_idx, subpal):
    tl = get_chr_tile(tl_idx)
    tr = get_chr_tile(tr_idx)
    bl = get_chr_tile(bl_idx)
    br = get_chr_tile(br_idx)
    
    img = []
    # top 8 rows
    for y in range(8):
        row = []
        for x in range(8):
            color_idx = world0_pals[subpal][tl[y][x]]
            row.append(NES_PALETTE[color_idx] + (255,))
        for x in range(8):
            color_idx = world0_pals[subpal][tr[y][x]]
            row.append(NES_PALETTE[color_idx] + (255,))
        img.append(row)
    # bottom 8 rows
    for y in range(8):
        row = []
        for x in range(8):
            color_idx = world0_pals[subpal][bl[y][x]]
            row.append(NES_PALETTE[color_idx] + (255,))
        for x in range(8):
            color_idx = world0_pals[subpal][br[y][x]]
            row.append(NES_PALETTE[color_idx] + (255,))
        img.append(row)
    return img

# Let's render a grid of 44 blocks (e.g. 11 cols x 4 rows)
# Width = 11 * 16 = 176, Height = 4 * 16 = 64
# For each block, let's determine best subpalette:
# Steel wall (12): subpal 0 (blue/white)
# Dirt (6): subpal 1 (brown/orange)
# Rock (21): subpal 2 (sand/gray)
# Diamond (27): subpal 0 or 3
# Let's test with subpalette 1 (dirt) and 0 (steel) and 2 (rock)
for sub in range(4):
    sheet = bytearray(176 * 64 * 4)
    for i in range(44):
        bx = (i % 11) * 16
        by = (i // 11) * 16
        tl, tr, bl, br = tsa_blocks[i]
        block_img = render_16x16(tl, tr, bl, br, sub)
        for y in range(16):
            for x in range(16):
                px = bx + x
                py = by + y
                r, g, b, a = block_img[y][x]
                pos = (py * 176 + px) * 4
                sheet[pos:pos+4] = bytes([r, g, b, a])
    write_png(f'tileset_subpal{sub}.png', 176, 64, sheet)

print("Rendered tileset_subpal0..3.png successfully!")
