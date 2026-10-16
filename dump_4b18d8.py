with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
off = 0x4b18d8 - base
chunk = data[off:off+200]
print("Function 0x4b18d8:")
for i in range(0, len(chunk), 16):
    print(hex(0x4b18d8 + i), ' '.join(f"{b:02x}" for b in chunk[i:i+16]))
