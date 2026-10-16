with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
start_va = 0x49fc3c
off = start_va - base
chunk = data[off:off+400]

print("=== Disassembly of TDCP_rijndael.Init ===")
for i in range(0, len(chunk), 16):
    print(hex(start_va + i), ' '.join(f"{b:02x}" for b in chunk[i:i+16]))
