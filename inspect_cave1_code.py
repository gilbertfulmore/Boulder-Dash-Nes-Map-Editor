with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000

# Let's inspect 0x4a7de0 to 0x4a7e60 (Cave 1)
off = 0x4a7de0 - base
chunk = data[off:off+150]
print("Cave 1 loading code:")
for i in range(0, len(chunk), 16):
    print(hex(0x4a7de0 + i), ' '.join(f"{b:02x}" for b in chunk[i:i+16]))
