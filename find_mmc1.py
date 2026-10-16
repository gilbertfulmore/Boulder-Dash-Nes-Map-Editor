with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

# Search for writes to MMC1 register 1 ($A000-$BFFF, CHR bank 0)
# and register 2 ($C000-$DFFF, CHR bank 1)
# In MMC1, writing involves 5 consecutive writes with ROR or LSR, or a subroutne
# Let's search for MMC1 write routines in PRG ROM
for i in range(len(prg)-5):
    # STA $A000 ($8d 0x00 0xa0) or STA $8000 ($8d 0x00 0x80)
    if prg[i] == 0x8d:
        addr = prg[i+1] | (prg[i+2] << 8)
        if 0x8000 <= addr <= 0xffff and addr & 0x1fff == 0:
            print(f"Write to MMC1 reg ${addr:04x} at PRG {hex(i)}")
