with open('Quarry.exe', 'rb') as f:
    exe = f.read()

ep_file_off = 0x4e500
code = exe[ep_file_off:ep_file_off+600]

# Let's inspect the end of the decompressor where unfilter and jmp to OEP happens
# Usually `popad` (0x61) followed by `jmp OEP` (0xe9 or 0xeb)
for i in range(len(code)-10):
    if code[i] == 0x61: # popad
        print(f"popad at offset {hex(ep_file_off + i)}:")
        print("Bytes:", ' '.join(f"{b:02x}" for b in code[i-40:i+30]))
