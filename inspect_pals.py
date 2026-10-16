with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

# Header is 16 bytes
prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

# TSA table: 44 blocks, 4 bytes each
tsa_off = 0x73a0
tsa_blocks = []
for i in range(44):
    tl, tr, bl, br = prg[tsa_off + i*4 : tsa_off + (i+1)*4]
    tsa_blocks.append((tl, tr, bl, br))

# Block palette attributes (44 bytes?): at 0x7450
pal_att_off = 0x7450
block_pals = list(prg[pal_att_off:pal_att_off+44])
print("Block palettes (0..43):", block_pals)

# Palettes at 0x3c32
pal_off = 0x3c32
print("Palettes at 0x3c32 (first 48 bytes):", [hex(b) for b in prg[pal_off:pal_off+48]])
