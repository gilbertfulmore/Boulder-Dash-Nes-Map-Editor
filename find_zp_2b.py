with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

# Search for STA $2B (0x85 0x2b) or STA $2B,X (0x95 0x2b) or STA $2B,Y
for i in range(len(prg)-2):
    b0, b1 = prg[i], prg[i+1]
    if b1 == 0x2b and b0 in [0x85, 0x95, 0x91, 0x81]:
        print(f"Write to $2b at PRG {hex(i)}: op={hex(b0)}")
