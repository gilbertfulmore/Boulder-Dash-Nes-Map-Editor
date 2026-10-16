import struct

with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x49e420
off = start_va - base
chunk = data[off:off+400]

print(f"=== Function 0x49e380 (DecryptString body) ===")
for i in range(len(chunk)-5):
    curr_va = start_va + i
    b = chunk[i]
    if b == 0xe8:
        rel = struct.unpack('<i', chunk[i+1:i+5])[0]
        target = curr_va + 5 + rel
        print(f"  {hex(curr_va)}: CALL {hex(target)}")
    elif b == 0xff and (chunk[i+1] & 0xf8) == 0x50:
        disp = chunk[i+2] if (chunk[i+1] & 0xc0) == 0x40 else 0
        print(f"  {hex(curr_va)}: CALL [reg+{hex(disp)}]")
