import hashlib
import base64

def aes_sbox():
    # Generate AES Rijndael S-box
    sbox = [0] * 256
    p = 1
    q = 1
    # Generate tables
    while True:
        # multiply p by 3 in GF(2^8)
        p = p ^ ((p << 1) ^ (0x11b if (p & 0x80) else 0)) & 0xff
        # divide q by 3
        q ^= q << 1
        q ^= q << 2
        q ^= q << 4
        q ^= 0x09 if (q & 0x80) else 0
        q &= 0xff
        xformed = q ^ ((q << 1) | (q >> 7)) ^ ((q << 2) | (q >> 6)) ^ ((q << 3) | (q >> 5)) ^ ((q << 4) | (q >> 4)) ^ 0x63
        sbox[p] = xformed & 0xff
        if p == 1:
            break
    sbox[0] = 0x63
    return sbox

SBOX = aes_sbox()

def sub_word(w):
    return (SBOX[(w >> 24) & 0xff] << 24) | (SBOX[(w >> 16) & 0xff] << 16) | (SBOX[(w >> 8) & 0xff] << 8) | SBOX[w & 0xff]

def rot_word(w):
    return ((w << 8) & 0xffffffff) | (w >> 24)

RCON = [0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]

def key_expansion_192(key24):
    # key24 is 24 bytes (Nk = 6, Nr = 12, Nb = 4)
    # Total words = Nb * (Nr + 1) = 4 * 13 = 52 words
    w = [0] * 52
    for i in range(6):
        w[i] = int.from_bytes(key24[4*i:4*i+4], 'big')
    
    for i in range(6, 52):
        temp = w[i - 1]
        if i % 6 == 0:
            temp = sub_word(rot_word(temp)) ^ (RCON[i // 6] << 24)
        w[i] = w[i - 6] ^ temp
    return w

def xtime(a):
    return ((a << 1) ^ (0x1b if (a & 0x80) else 0)) & 0xff

def mix_single_column(a):
    t = a[0] ^ a[1] ^ a[2] ^ a[3]
    u = a[0]
    a[0] ^= t ^ xtime(a[0] ^ a[1])
    a[1] ^= t ^ xtime(a[1] ^ a[2])
    a[2] ^= t ^ xtime(a[2] ^ a[3])
    a[3] ^= t ^ xtime(a[3] ^ u)

def aes192_encrypt_block(block, round_keys):
    # block is 16 bytes
    # round_keys is 52 words (13 rounds: 0..12)
    state = [list(block[4*i:4*i+4]) for i in range(4)] # state[col][row]
    
    # AddRoundKey 0
    for c in range(4):
        kw = round_keys[c]
        state[c][0] ^= (kw >> 24) & 0xff
        state[c][1] ^= (kw >> 16) & 0xff
        state[c][2] ^= (kw >> 8) & 0xff
        state[c][3] ^= kw & 0xff

    # Rounds 1 to 11
    for r in range(1, 12):
        # SubBytes & ShiftRows
        # Row 0: no shift
        s00 = SBOX[state[0][0]]
        s10 = SBOX[state[1][0]]
        s20 = SBOX[state[2][0]]
        s30 = SBOX[state[3][0]]
        # Row 1: shift left 1
        s01 = SBOX[state[1][1]]
        s11 = SBOX[state[2][1]]
        s21 = SBOX[state[3][1]]
        s31 = SBOX[state[0][1]]
        # Row 2: shift left 2
        s02 = SBOX[state[2][2]]
        s12 = SBOX[state[3][2]]
        s22 = SBOX[state[0][2]]
        s32 = SBOX[state[1][2]]
        # Row 3: shift left 3
        s03 = SBOX[state[3][3]]
        s13 = SBOX[state[0][3]]
        s23 = SBOX[state[1][3]]
        s33 = SBOX[state[2][3]]
        
        state[0] = [s00, s01, s02, s03]
        state[1] = [s10, s11, s12, s13]
        state[2] = [s20, s21, s22, s23]
        state[3] = [s30, s31, s32, s33]
        
        # MixColumns
        for c in range(4):
            mix_single_column(state[c])
            
        # AddRoundKey
        for c in range(4):
            kw = round_keys[r*4 + c]
            state[c][0] ^= (kw >> 24) & 0xff
            state[c][1] ^= (kw >> 16) & 0xff
            state[c][2] ^= (kw >> 8) & 0xff
            state[c][3] ^= kw & 0xff

    # Round 12 (final round)
    s00 = SBOX[state[0][0]]
    s10 = SBOX[state[1][0]]
    s20 = SBOX[state[2][0]]
    s30 = SBOX[state[3][0]]
    s01 = SBOX[state[1][1]]
    s11 = SBOX[state[2][1]]
    s21 = SBOX[state[3][1]]
    s31 = SBOX[state[0][1]]
    s02 = SBOX[state[2][2]]
    s12 = SBOX[state[3][2]]
    s22 = SBOX[state[0][2]]
    s32 = SBOX[state[1][2]]
    s03 = SBOX[state[3][3]]
    s13 = SBOX[state[0][3]]
    s23 = SBOX[state[1][3]]
    s33 = SBOX[state[2][3]]
    state[0] = [s00, s01, s02, s03]
    state[1] = [s10, s11, s12, s13]
    state[2] = [s20, s21, s22, s23]
    state[3] = [s30, s31, s32, s33]
    
    for c in range(4):
        kw = round_keys[12*4 + c]
        state[c][0] ^= (kw >> 24) & 0xff
        state[c][1] ^= (kw >> 16) & 0xff
        state[c][2] ^= (kw >> 8) & 0xff
        state[c][3] ^= kw & 0xff
        
    out = bytearray(16)
    for c in range(4):
        for row in range(4):
            out[c*4 + row] = state[c][row]
    return bytes(out)

class DCPRijndaelCFB8:
    def __init__(self, key_str):
        # 1. SHA-1 of key_str
        h = hashlib.sha1(key_str.encode('latin1')).digest()
        # 2. Pad to 24 bytes (192 bits) with zeros
        key24 = h + b'\x00' * 4
        # 3. Expand round keys
        self.round_keys = key_expansion_192(key24)
        # 4. IV = Encrypt(16 x 0xFF)
        self.iv = aes192_encrypt_block(bytes([0xff]*16), self.round_keys)
        self.reset()
        
    def reset(self):
        self.cv = bytearray(self.iv)
        
    def decrypt(self, ciphertext):
        out = bytearray(len(ciphertext))
        for i, c in enumerate(ciphertext):
            enc_cv = aes192_encrypt_block(bytes(self.cv), self.round_keys)
            p = c ^ enc_cv[0]
            out[i] = p
            # CFB8 update: shift left, insert ciphertext byte at end
            self.cv = self.cv[1:] + bytearray([c])
        return bytes(out)

def decrypt_val(cipher, s):
    # Replace ! with =
    s_clean = s.replace('!', '=')
    raw = base64.b64decode(s_clean)
    cipher.reset()
    pt = cipher.decrypt(raw)
    return pt.decode('latin1', errors='replace')

# Test section name and first few lines of AmericanData.dat
sec_cipher = DCPRijndaelCFB8('QUARRY')
val_cipher = DCPRijndaelCFB8('FLOPPY')

print("Testing first section:")
sec_enc = "1Zczaju/Sni!"
print(f"[{sec_enc}] -> [{decrypt_val(sec_cipher, sec_enc)}]")

# Test lines
with open('Data/AmericanData.dat', 'r') as f:
    lines = [line.strip() for line in f if line.strip()]

for line in lines[:15]:
    if line.startswith('['):
        s = line[1:-1]
        print(f"\nSection: [{decrypt_val(sec_cipher, s)}]")
    elif '=' in line:
        k, v = line.split('=', 1)
        dk = decrypt_val(sec_cipher, k)
        dv = decrypt_val(val_cipher, v)
        print(f"  {dk} = {dv}")
