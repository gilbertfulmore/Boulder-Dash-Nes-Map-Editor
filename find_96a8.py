with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

import struct

addr = struct.pack('<I', 0x004b96a8)
for i in range(len(data)-4):
    if data[i:i+4] == addr:
        va = 0x401000 + i
        # print preceding opcode
        op = data[i-1] if i > 0 else 0
        op2 = data[i-2] if i > 1 else 0
        print(f"Ref at VA {hex(va-4)} (file offset {hex(i-4)}): op={hex(op2)}, {hex(op)}")
