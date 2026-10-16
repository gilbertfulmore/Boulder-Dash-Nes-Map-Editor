with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
chr_rom = rom[16+32768:]

tsa_off = 0x73a0
print("=== All 44 TSA Blocks (PRG 0x73a0) ===")
for i in range(44):
    tl, tr, bl, br = prg[tsa_off + i*4 : tsa_off + (i+1)*4]
    print(f"Block {i:2d}: TL={hex(tl)}, TR={hex(tr)}, BL={hex(bl)}, BR={hex(br)}")
