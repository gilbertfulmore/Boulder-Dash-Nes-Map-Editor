with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# Let's inspect block 3 (steel wall) and block 7 (rock) and block 8 (diamond)
# TSA blocks at 0x73a0
tsa_off = 0x73a0

# Let's see the CHR tiles for block 12 (steel wall) and block 21 (rock)
# For block 12:
tl, tr, bl, br = prg[tsa_off + 12*4 : tsa_off + 13*4]
print(f"Block 12 (Steel wall): TL={hex(tl)}, TR={hex(tr)}, BL={hex(bl)}, BR={hex(br)}")

# For block 21 (Rock):
tl, tr, bl, br = prg[tsa_off + 21*4 : tsa_off + 22*4]
print(f"Block 21 (Rock): TL={hex(tl)}, TR={hex(tr)}, BL={hex(bl)}, BR={hex(br)}")

# For block 27 (Diamond):
tl, tr, bl, br = prg[tsa_off + 27*4 : tsa_off + 28*4]
print(f"Block 27 (Diamond): TL={hex(tl)}, TR={hex(tr)}, BL={hex(bl)}, BR={hex(br)}")

# For block 6 (Dirt):
tl, tr, bl, br = prg[tsa_off + 6*4 : tsa_off + 7*4]
print(f"Block  6 (Dirt): TL={hex(tl)}, TR={hex(tr)}, BL={hex(bl)}, BR={hex(br)}")
