import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x49f348
off = start_va - base
chunk = data[off:off+120]

print("=== Disassembly of InitKey at 0x49f348 ===")
for i in range(len(chunk)-5):
    curr_va = start_va + i
    b = chunk[i]
    if b == 0xe8:
        rel = struct.unpack('<i', chunk[i+1:i+5])[0]
        target = curr_va + 5 + rel
        print(f"  {hex(curr_va)}: CALL {hex(target)}")
    elif b in [0xa1, 0xa3]:
        addr = struct.unpack('<I', chunk[i+1:i+5])[0]
        op = "MOV EAX, [" if b == 0xa1 else "MOV [, EAX"
        print(f"  {hex(curr_va)}: {op}{hex(addr)}]")
