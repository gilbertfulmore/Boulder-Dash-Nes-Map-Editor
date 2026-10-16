with open('Quarry.exe', 'rb') as f:
    exe = f.read()

ep_file_off = 0x4e500
code = exe[ep_file_off:0x4e670]

# Print bytes with offsets
for i in range(0, len(code), 16):
    chunk = code[i:i+16]
    hex_str = ' '.join(f"{b:02x}" for b in chunk)
    print(f"{hex(ep_file_off + i)}: {hex_str}")
