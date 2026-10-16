import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
off = 0x4a6a80 - base
chunk = data[off:off+300]
print(f"Function at 0x4a6a80:")
for i in range(0, len(chunk), 16):
    print(hex(0x4a6a80 + i), ' '.join(f"{b:02x}" for b in chunk[i:i+16]))
