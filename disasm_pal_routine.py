with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
from disasm import disasm

print("=== Disassembly around 0x20b5 (NES $A0B5) ===")
# PRG 0x20b5 is NES address $a0b5 (bank 0: 0x0000 = $8000, so 0x20b5 = $a0b5)
disasm(prg[0x20a0:0x2120], 0xa0a0, 40)
