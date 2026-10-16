import struct

with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]

target = 0x8d24
b = struct.pack('<H', target)
for i in range(len(prg)-1):
    if prg[i:i+2] == b:
        print(f"Found $8d24 at PRG 0x{i:04x}")
