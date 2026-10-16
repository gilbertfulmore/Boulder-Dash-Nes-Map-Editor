import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4a0764
off = start_va - base
chunk = data[off:off+300]

print(f"=== Function 0x4a0764 (TSecurityIni.Create) ===")
for i in range(len(chunk)-5):
    curr_va = start_va + i
    b = chunk[i]
    if b == 0xe8:
        rel = struct.unpack('<i', chunk[i+1:i+5])[0]
        target = curr_va + 5 + rel
        print(f"  {hex(curr_va)}: CALL {hex(target)}")
