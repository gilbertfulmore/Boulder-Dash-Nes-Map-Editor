import os
import base64
import json
import zlib
import struct

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ROM_PATH = os.path.join(DATA_DIR, "Boulder Dash.nes")
TILES_JSON_PATH = os.path.join(DATA_DIR, "tiles_library.json")

# Standard 2C02 NES palette (64 RGB colors)
NES_PALETTE = [
    (0x7C, 0x7C, 0x7C), (0x00, 0x00, 0xFC), (0x00, 0x00, 0xBC), (0x44, 0x28, 0xBC),
    (0x94, 0x00, 0x84), (0xA8, 0x00, 0x20), (0xA8, 0x10, 0x00), (0x88, 0x14, 0x00),
    (0x50, 0x30, 0x00), (0x00, 0x78, 0x00), (0x00, 0x68, 0x00), (0x00, 0x58, 0x00),
    (0x00, 0x40, 0x58), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xBC, 0xBC, 0xBC), (0x00, 0x78, 0xF8), (0x00, 0x58, 0xF8), (0x68, 0x44, 0xFC),
    (0xD8, 0x00, 0xCC), (0xE4, 0x00, 0x58), (0xF8, 0x38, 0x00), (0xE4, 0x5C, 0x10),
    (0xAC, 0x7C, 0x00), (0x00, 0xB8, 0x00), (0x00, 0xA8, 0x00), (0x00, 0xA8, 0x44),
    (0x00, 0x88, 0x88), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xF8, 0xF8, 0xF8), (0x3C, 0xBC, 0xFC), (0x68, 0x88, 0xFC), (0x98, 0x78, 0xF8),
    (0xF8, 0x78, 0xF8), (0xF8, 0x58, 0x98), (0xF8, 0x78, 0x58), (0xFC, 0xA0, 0x44),
    (0xF8, 0xB8, 0x00), (0xB8, 0xF8, 0x18), (0x58, 0xD8, 0x54), (0x58, 0xF8, 0x98),
    (0x00, 0xE8, 0xD8), (0x78, 0x78, 0x78), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00),
    (0xFC, 0xFC, 0xFC), (0xA4, 0xE4, 0xFC), (0xB8, 0xB8, 0xF8), (0xD8, 0xB8, 0xF8),
    (0xF8, 0xB8, 0xF8), (0xF8, 0xA4, 0xC0), (0xF0, 0xD0, 0xB0), (0xFC, 0xE0, 0xA8),
    (0xF8, 0xD8, 0x78), (0xD8, 0xF8, 0x78), (0xB8, 0xF8, 0xB8), (0xB8, 0xF8, 0xD8),
    (0x00, 0xFC, 0xFC), (0xF8, 0xD8, 0xF8), (0x00, 0x00, 0x00), (0x00, 0x00, 0x00)
]

def decode_8x8_tile(tile_bytes):
    pixels = []
    for y in range(8):
        b0 = tile_bytes[y]
        b1 = tile_bytes[y + 8]
        row = []
        for x in range(8):
            bit0 = (b0 >> (7 - x)) & 1
            bit1 = (b1 >> (7 - x)) & 1
            row.append((bit1 << 1) | bit0)
        pixels.append(row)
    return pixels

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

def generate():
    with open(ROM_PATH, 'rb') as f:
        rom = f.read()

    prg = rom[16:16+32768]
    chr_rom = rom[16+32768:]

    pointers = []
    for i in range(16):
        lo = prg[0x7370 + i * 2]
        hi = prg[0x7370 + i * 2 + 1]
        pointers.append((lo | (hi << 8)) - 0x8000)

    subpalette_map = [prg[0x7440 + nib] & 3 for nib in range(16)]

    world_palettes = []
    for w in range(6):
        pal_off = 0x3c22 + w * 16
        wpal = [
            [prg[pal_off + s * 4 + c] for c in range(4)]
            for s in range(4)
        ]
        world_palettes.append(wpal)

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

        ptl, ptr_t, pbl, pbr = prg[0x73E0 : 0x73E4]
        portal_b64 = render_metatile_b64(ptl, ptr_t, pbl, pbr, pals[subpalette_map[4]])

        for nib in range(16):
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

    b4 = chr_rom[4 * 4096 : 5 * 4096]
    rockford_pal = [prg[0x3c82 + c] for c in range(4)]

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

    with open(TILES_JSON_PATH, 'w') as f:
        json.dump(tileset_data, f)

    print("Generated authentic data/tiles_library.json successfully!")

if __name__ == "__main__":
    generate()
