import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4a05a0
off = start_va - base
chunk = data[off:off+180]

print(f"=== Function at 0x4a05a0 (The Decryption Function!) ===")
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
    elif b == 0xff: # indirect call
        print(f"  {hex(curr_va)}: FF {hex(chunk[i+1])} {hex(chunk[i+2])}")
