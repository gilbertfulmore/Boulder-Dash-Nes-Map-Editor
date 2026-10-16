import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x4b34cc
end_va = 0x4b38d4
start_off = start_va - base
end_off = end_va - base
code = data[start_off:end_off]

print(f"Analyzing actOpenROMExecute (VA {hex(start_va)} to {hex(end_va)}):")
for i in range(len(code)-5):
    b = code[i]
    va = start_va + i
    if b == 0xe8: # CALL rel32
        rel = struct.unpack('<i', code[i+1:i+5])[0]
        target = va + 5 + rel
        print(f"  {hex(va)}: CALL {hex(target)}")
    elif b == 0xa1: # MOV EAX, [addr]
        addr = struct.unpack('<I', code[i+1:i+5])[0]
        print(f"  {hex(va)}: MOV EAX, [{hex(addr)}]")
