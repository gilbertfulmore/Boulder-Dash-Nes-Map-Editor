import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
vmt = 0x0049f4e0
off = vmt - base

print("=== TDCP_rijndael Virtual Methods ===")
for i in range(25):
    entry_va = int.from_bytes(data[off + i*4 : off + (i+1)*4], 'little')
    print(f"VMT + {hex(i*4)}: {hex(entry_va)}")
