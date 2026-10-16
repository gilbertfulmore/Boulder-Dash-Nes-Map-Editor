with open('Quarry.exe', 'rb') as f:
    exe = f.read()

# PE header
pe_off = int.from_bytes(exe[0x3c:0x40], 'little')
ep = int.from_bytes(exe[pe_off+0x28:pe_off+0x2c], 'little')
image_base = int.from_bytes(exe[pe_off+0x34:pe_off+0x38], 'little')
print(f"Entry point RVA: {hex(ep)}, ImageBase: {hex(image_base)}")

# Let's find UPX section
num_sec = int.from_bytes(exe[pe_off+6:pe_off+8], 'little')
sec_hdr = pe_off + 0x18 + int.from_bytes(exe[pe_off+0x14:pe_off+0x16], 'little')
for i in range(num_sec):
    sec = exe[sec_hdr+i*40:sec_hdr+(i+1)*40]
    name = sec[:8].rstrip(b'\x00').decode('latin1')
    vsize = int.from_bytes(sec[8:12], 'little')
    va = int.from_bytes(sec[12:16], 'little')
    rsize = int.from_bytes(sec[16:20], 'little')
    roff = int.from_bytes(sec[20:24], 'little')
    print(f"Section {name}: VA={hex(va)}, VSize={hex(vsize)}, RawOff={hex(roff)}, RawSize={hex(rsize)}")
    if va <= ep < va + rsize:
        ep_file_off = roff + (ep - va)
        print(f"EP is in section {name} at file offset {hex(ep_file_off)}")
        # print first 100 bytes of EP code
        print("EP bytes:", ' '.join(f"{b:02x}" for b in exe[ep_file_off:ep_file_off+100]))
