with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

off = 34832 # Level 1-1
cave_bytes = rom[off:off+440]

TILE_CHARS = {
    0x0: ' ',  # Empty / space
    0x1: '.',  # Dirt (or 0x2)
    0x2: '.',  # Dirt
    0x3: '#',  # Steel wall
    0x4: 'M',  # Magic wall
    0x5: 'X',  # Exit
    0x6: 'W',  # Brick wall
    0x7: 'O',  # Boulder / Rock
    0x8: '*',  # Diamond
    0x9: 'A',  # Amoeba
    0xa: 'F',  # Firefly
    0xb: 'B',  # Butterfly
    0xc: 'R',  # Rockford
}

# Let's test low-nibble first vs high-nibble first
print("=== Cave 1-1 (Low nibble first) ===")
for r in range(22):
    row_bytes = cave_bytes[r*20:(r+1)*20]
    row_tiles = []
    for b in row_bytes:
        t0 = b & 0x0f
        t1 = (b >> 4) & 0x0f
        row_tiles.append(t0)
        row_tiles.append(t1)
    print(''.join(TILE_CHARS.get(t, f"{t:X}") for t in row_tiles))

print("\n=== Cave 1-1 (High nibble first) ===")
for r in range(22):
    row_bytes = cave_bytes[r*20:(r+1)*20]
    row_tiles = []
    for b in row_bytes:
        t0 = (b >> 4) & 0x0f
        t1 = b & 0x0f
        row_tiles.append(t0)
        row_tiles.append(t1)
    print(''.join(TILE_CHARS.get(t, f"{t:X}") for t in row_tiles))
