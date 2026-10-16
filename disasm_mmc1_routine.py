with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
from disasm import disasm

print("=== MMC1 Bankswitching routine around PRG 0x2250 (NES $A250) ===")
disasm(prg[0x2250:0x22d0], 0xa250, 40)
