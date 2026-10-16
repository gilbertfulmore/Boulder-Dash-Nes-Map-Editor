with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

pos = 0xaff00
while pos < 0xb0200:
    name_len = data[pos+6] if pos+6 < len(data) else 0
    if 3 <= name_len <= 50:
        name = data[pos+7:pos+7+name_len]
        if name.isalnum():
            code_ptr = int.from_bytes(data[pos+2:pos+6], 'little')
            entry_len = int.from_bytes(data[pos:pos+2], 'little')
            if entry_len == name_len + 7:
                print(f"{hex(code_ptr)}: {name.decode()}")
                pos += entry_len
                continue
    pos += 1
