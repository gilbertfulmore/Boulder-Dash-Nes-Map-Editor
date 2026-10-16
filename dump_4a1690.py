import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4a1690
start_off = start_va - base

# Dump 0x4a1690
code = data[start_off:start_off+500]
print(f"=== Function at 0x4a1690 (len {len(code)}) ===")
for i in range(len(code)-5):
    curr_va = start_va + i
    b = code[i]
    if b == 0xe8:
        rel = struct.unpack('<i', code[i+1:i+5])[0]
        target = curr_va + 5 + rel
        print(f"  {hex(curr_va)}: CALL {hex(target)}")
    elif b in [0xa1, 0xa3]:
        addr = struct.unpack('<I', code[i+1:i+5])[0]
        op = "MOV EAX, [" if b == 0xa1 else "MOV [, EAX"
        print(f"  {hex(curr_va)}: {op}{hex(addr)}]")
