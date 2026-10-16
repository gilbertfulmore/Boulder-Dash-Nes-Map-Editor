with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
from disasm import disasm

print("=== Disassembly around 0x2430 (NES $A430) ===")
disasm(prg[0x2430:0x2510], 0xa430, 80)
