with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

import struct

addr = struct.pack('<I', 0x004b96a8)
for i in range(len(data)-4):
    if data[i:i+4] == addr:
        va = 0x401000 + i
        b_before = list(data[max(0, i-4):i])
        print(f"Ref at VA {hex(va)}: before={[hex(x) for x in b_before]}")
