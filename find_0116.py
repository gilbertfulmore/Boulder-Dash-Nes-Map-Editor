with open('Boulder Dash.nes', 'rb') as f:
    rom = f.read()

prg = rom[16:16+32768]
import struct

# Search for writes to $0116 or $0116,X ($8d 0x16 0x01 or $9d 0x16 0x01)
target1 = b'\x8d\x16\x01'
target2 = b'\x9d\x16\x01'

for i in range(len(prg)-3):
    if prg[i:i+3] == target1 or prg[i:i+3] == target2:
        print(f"Write to $0116 at PRG {hex(i)}: {hex(prg[i])}")
