import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000

def dump_detailed(va, length=250):
    off = va - base
    print(f"\n=== Detailed dump of {hex(va)} ===")
    code = data[off:off+length]
    for i in range(len(code)-5):
        b = code[i]
        curr_va = va + i
        if b == 0xe8:
            rel = struct.unpack('<i', code[i+1:i+5])[0]
            target = curr_va + 5 + rel
            print(f"  {hex(curr_va)}: CALL {hex(target)}")
        elif b in [0xa1, 0xa3]:
            addr = struct.unpack('<I', code[i+1:i+5])[0]
            op = "MOV EAX, [" if b == 0xa1 else "MOV [, EAX"
            print(f"  {hex(curr_va)}: {op}{hex(addr)}]")
        elif b == 0x8b and code[i+1] == 0x15: # mov edx, [addr]
            addr = struct.unpack('<I', code[i+2:i+6])[0]
            print(f"  {hex(curr_va)}: MOV EDX, [{hex(addr)}]")
        elif b == 0x8b and code[i+1] == 0x0d: # mov ecx, [addr]
            addr = struct.unpack('<I', code[i+2:i+6])[0]
            print(f"  {hex(curr_va)}: MOV ECX, [{hex(addr)}]")

dump_detailed(0x4a0f3c, 300)
dump_detailed(0x4b2f10, 150)
dump_detailed(0x4b17e4, 150)
