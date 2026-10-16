import io
import base64
import json
import zlib
import struct
from test_chr import decode_8x8_tile, NES_PALETTE

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# Authentic Metatile Pointers from NES PRG 0x7370 ($F370)
# Subroutine $B580 reads the 16 pointer addresses
pointers = []
for i in range(16):
    lo = prg[0x7370 + i * 2]
    hi = prg[0x7370 + i * 2 + 1]
    pointers.append((lo | (hi << 8)) - 0x8000)

# Authentic Subpalette Table from NES PRG 0x7440 ($F440)
# LDA $F440,X in NES screen building routine
subpalette_map = [prg[0x7440 + nib] & 3 for nib in range(16)]

# Authentic World Palettes from NES PRG 0x3c22 ($BC22)
# Pointer table at $BC16 points to $BC22, $BC32, $BC42, $BC52, $BC62, $BC72
world_palettes = []
for w in range(6):
    pal_off = 0x3c22 + w * 16
    wpal = [
        [prg[pal_off + s * 4 + c] for c in range(4)]
        for s in range(4)
    ]
    world_palettes.append(wpal)

TILE_NAMES = [
    "Empty Space",
    "Empty (Cleared)",
    "Dirt",
    "Steel Wall",
    "Exit Door",
    "Brick Wall",
    "Magic Wall",
    "Boulder / Rock",
    "Diamond",
    "Diamond Sparkle",
    "Explosion Sparkle",
    "Firefly",
    "Butterfly",
    "Amoeba",
    "Rockford / Amoeba Alt",
    "Petrified / Spider"
]

TILE_SHORT_NAMES = [
    "Space",
    "Cleared",
    "Dirt",
    "Steel",
    "Exit",
    "Wall",
    "Magic",
    "Boulder",
    "Diamond",
    "Gem *",
    "Spark *",
    "Firefly",
    "B-Fly",
    "Amoeba",
    "Amoeba2",
    "Spider"
]

def png_bytes(width, height, rgba_data):
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(rgba_data[y * width * 4 : (y + 1) * width * 4])
    compressed = zlib.compress(bytes(scanlines))
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', compressed) + chunk(b'IEND', b'')

def render_metatile_b64(tl, tr, bl, br, pal):
    tl_t = decode_8x8_tile(chr_rom[tl * 16 : (tl + 1) * 16])
    tr_t = decode_8x8_tile(chr_rom[tr * 16 : (tr + 1) * 16])
    bl_t = decode_8x8_tile(chr_rom[bl * 16 : (bl + 1) * 16])
    br_t = decode_8x8_tile(chr_rom[br * 16 : (br + 1) * 16])

    rgba = bytearray(16 * 16 * 4)
    for y in range(8):
        for x in range(8):
            c = NES_PALETTE[pal[tl_t[y][x]]]
            pos = (y * 16 + x) * 4
            rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
        for x in range(8):
            c = NES_PALETTE[pal[tr_t[y][x]]]
            pos = (y * 16 + (x + 8)) * 4
            rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
    for y in range(8):
        for x in range(8):
            c = NES_PALETTE[pal[bl_t[y][x]]]
            pos = ((y + 8) * 16 + x) * 4
            rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
        for x in range(8):
            c = NES_PALETTE[pal[br_t[y][x]]]
            pos = ((y + 8) * 16 + (x + 8)) * 4
            rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])

    p_bytes = png_bytes(16, 16, rgba)
    return "data:image/png;base64," + base64.b64encode(p_bytes).decode('ascii')

tileset_data = {}

for w in range(6):
    tileset_data[w] = []
    pals = world_palettes[w]
    
    # Authentic open exit portal from PRG 0x73E0 ($F3E0: [10, 11, 12, 13]) using wall subpalette 0
    ptl, ptr_t, pbl, pbr = prg[0x73E0 : 0x73E4]
    portal_b64 = render_metatile_b64(ptl, ptr_t, pbl, pbr, pals[subpalette_map[4]])
    
    for nib in range(16):
        # In NES Boulder Dash routine $B580:
        # Nibbles 8, 9, 10, 13, 14, 15 use static pointers
        # Other nibbles advance by w * 4 bytes
        if nib in [8, 9, 10, 13, 14, 15]:
            ptr = pointers[nib]
        else:
            ptr = pointers[nib] + w * 4
            
        tl, tr, bl, br = prg[ptr : ptr + 4]
        sub = subpalette_map[nib]
        pal = pals[sub]
        
        b64 = render_metatile_b64(tl, tr, bl, br, pal)
        entry = {
            'id': nib,
            'name': TILE_NAMES[nib],
            'short_name': TILE_SHORT_NAMES[nib],
            'image': b64
        }
        if nib == 4:
            entry['portal_image'] = portal_b64
        tileset_data[w].append(entry)

# Extract authentic Rockford sprite from CHR Bank 4
# Sprite palette: [0x0F, 0x36, 0x26, 0x0F] at PRG 0x3c82
b4 = chr_rom[4 * 4096 : 5 * 4096]
rockford_pal = [prg[0x3c82 + c] for c in range(4)]

# Rockford facing right (authentic gameplay standing pose)
# TL=32, BL=33, TR=34, BR=35 in 8x16 sprite layout
rf_tl = decode_8x8_tile(b4[32 * 16 : 33 * 16])
rf_bl = decode_8x8_tile(b4[33 * 16 : 34 * 16])
rf_tr = decode_8x8_tile(b4[34 * 16 : 35 * 16])
rf_br = decode_8x8_tile(b4[35 * 16 : 36 * 16])

rf_rgba = bytearray(16 * 16 * 4)
for y in range(8):
    for x in range(8):
        ci = rf_tl[y][x]
        if ci != 0:
            c = NES_PALETTE[rockford_pal[ci]]
            pos = (y * 16 + x) * 4
            rf_rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
    for x in range(8):
        ci = rf_tr[y][x]
        if ci != 0:
            c = NES_PALETTE[rockford_pal[ci]]
            pos = (y * 16 + (x + 8)) * 4
            rf_rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
for y in range(8):
    for x in range(8):
        ci = rf_bl[y][x]
        if ci != 0:
            c = NES_PALETTE[rockford_pal[ci]]
            pos = ((y + 8) * 16 + x) * 4
            rf_rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])
    for x in range(8):
        ci = rf_br[y][x]
        if ci != 0:
            c = NES_PALETTE[rockford_pal[ci]]
            pos = ((y + 8) * 16 + (x + 8)) * 4
            rf_rgba[pos:pos+4] = bytes([c[0], c[1], c[2], 255])

rf_bytes = png_bytes(16, 16, rf_rgba)
rockford_b64 = "data:image/png;base64," + base64.b64encode(rf_bytes).decode('ascii')
tileset_data['rockford'] = rockford_b64

with open('tiles_library.json', 'w') as f:
    json.dump(tileset_data, f)

print("Generated authentic tiles_library.json successfully!")
