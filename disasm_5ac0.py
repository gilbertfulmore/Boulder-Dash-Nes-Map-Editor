with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
from disasm import disasm

print("=== Disassembly around PRG 0x5ac0 ===")
disasm(prg[0x5ac0:0x5b30], 0xdac0, 60)
