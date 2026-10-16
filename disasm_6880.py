with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
from disasm import disasm

print("=== Disassembly around PRG 0x6880 ===")
disasm(prg[0x6870:0x68c0], 0xe870, 30)
