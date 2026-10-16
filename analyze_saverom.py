import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4b39b0
end_va = 0x4b3a60
start_off = start_va - base
end_off = end_va - base
code = data[start_off:end_off]

print(f"Analyzing actSaveROMExecute (VA {hex(start_va)} to {hex(end_va)}):")
for i in range(len(code)-5):
    b = code[i]
    va = start_va + i
    if b == 0xe8:
        rel = struct.unpack('<i', code[i+1:i+5])[0]
        target = va + 5 + rel
        print(f"  {hex(va)}: CALL {hex(target)}")
    elif b in [0xa1, 0xa3]:
        addr = struct.unpack('<I', code[i+1:i+5])[0]
        op = "MOV EAX, [" if b == 0xa1 else "MOV [, EAX"
        print(f"  {hex(va)}: {op}{hex(addr)}]")
