import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000

def dump_func(va, length=200):
    off = va - base
    print(f"=== Function at {hex(va)} ===")
    code = data[off:off+length]
    for i in range(len(code)-5):
        b = code[i]
        curr_va = va + i
        if b == 0xe8:
            rel = struct.unpack('<i', code[i+1:i+5])[0]
            target = curr_va + 5 + rel
            if 0x400000 <= target <= 0x500000:
                print(f"  {hex(curr_va)}: CALL {hex(target)}")
        elif b in [0xa1, 0xa3]:
            addr = struct.unpack('<I', code[i+1:i+5])[0]
            op = "MOV EAX, [" if b == 0xa1 else "MOV [, EAX"
            if 0x400000 <= addr <= 0x600000:
                print(f"  {hex(curr_va)}: {op}{hex(addr)}]")

for f_va in [0x4b134c, 0x4ae038, 0x4a1690, 0x4a1624, 0x4b18d8, 0x4b2258, 0x4b2558]:
    dump_func(f_va, 150)
