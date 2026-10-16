with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

# Common MMC1 write sequence:
# STA $xxxx; LSR A; STA $xxxx; LSR A; STA $xxxx; LSR A; STA $xxxx; LSR A; STA $xxxx
for i in range(len(prg)-15):
    # check for lsr a (0x4a) or ror a (0x6a) followed by sta abs (0x8d)
    if prg[i] in [0x4a, 0x6a] and prg[i+1] == 0x8d and prg[i+4] in [0x4a, 0x6a] and prg[i+5] == 0x8d:
        addr = prg[i+2] | (prg[i+3] << 8)
        print(f"MMC1 shift write sequence to ${addr:04x} at PRG {hex(i)}")
