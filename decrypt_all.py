import base64
from test_decrypt import DCPRijndaelCFB8, decrypt_val

c_quarry = DCPRijndaelCFB8('QUARRY')
c_floppy = DCPRijndaelCFB8('FLOPPY')

def decrypt_double(val_enc):
    # Pass 1: FLOPPY
    step1 = decrypt_val(c_floppy, val_enc)
    # Pass 2: QUARRY
    step2 = decrypt_val(c_quarry, step1)
    return step2

with open('Data/AmericanData.dat', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

curr_sec = ""
for line in lines:
    if line.startswith('['):
        curr_sec = decrypt_val(c_quarry, line[1:-1])
        print(f"\n[{curr_sec}]")
    elif '=' in line:
        k_enc, v_enc = line.split('=', 1)
        k = decrypt_val(c_quarry, k_enc)
        try:
            v = decrypt_double(v_enc)
        except Exception as e:
            v = f"ERR: {e}"
        print(f"  {k} = {v} (hex: {hex(int(v)) if v.isdigit() else v})")
