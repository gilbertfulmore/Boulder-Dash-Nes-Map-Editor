import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_off = 0x4bafc4 - base

print("=== 24 Cave Records at 0x004bafc4 ===")
for i in range(24):
    rec_off = start_off + i * 32
    rec = data[rec_off:rec_off+32]
    # Each record has 8 32-bit integers (32 bytes)
    fields = struct.unpack('<8I', rec)
    print(f"Cave {i+1:2d} (World {i//4 + 1}-{i%4 + 1}):")
    for f_idx, val in enumerate(fields):
        print(f"  Field {f_idx*4:02x}: {hex(val)} ({val})")
