with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

import struct

addr = struct.pack('<I', 0x004b95f4)
print(f"References to ROM buffer [0x004b95f4]:")
for i in range(len(data)-4):
    if data[i:i+4] == addr:
        va = 0x401000 + i
        # print surrounding bytes
        context = data[max(0, i-6):i+10]
        print(f"  VA {hex(va)} (offset {hex(i)}): context={' '.join(f'{b:02x}' for b in context)}")
