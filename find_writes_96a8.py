with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

import struct

addr = struct.pack('<I', 0x004b96a8)
for i in range(len(data)-4):
    if data[i:i+4] == addr:
        # Check if it's a write (mov [0x4b96a8], reg)
        # a3 a8 96 4b 00 -> mov [0x4b96a8], eax
        # 89 05/0d/15/1d/25/2d/35/3d a8 96 4b 00 -> mov [0x4b96a8], reg
        if i >= 1 and data[i-1] == 0xa3:
            print(f"MOV [0x4b96a8], EAX at VA {hex(0x401000 + i - 1)}")
        elif i >= 2 and data[i-2] == 0x89:
            print(f"MOV [0x4b96a8], reg at VA {hex(0x401000 + i - 2)}")
        elif i >= 1 and data[i-1] == 0xc7:
            print(f"MOV [0x4b96a8], imm at VA {hex(0x401000 + i - 1)}")
