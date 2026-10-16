with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

for i in range(len(prg)-5):
    if prg[i] == 0xa9 and prg[i+1] == 0x3f and prg[i+2] == 0x8d and prg[i+3] == 0x06 and prg[i+4] == 0x20:
        print(f"PPU palette write setup at PRG offset {hex(i)}")
