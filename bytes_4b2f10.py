with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

base = 0x401000
off = 0x4b2f10 - base
chunk = data[off:off+80]
print(' '.join(f"{b:02x}" for b in chunk))
