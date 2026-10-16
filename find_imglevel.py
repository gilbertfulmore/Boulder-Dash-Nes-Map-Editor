with open('quarry_perfect.bin', 'rb') as f:
    data = f.read()

# In DFM, imgLevel is TImage
# Let's find published field name imgLevel
pos = data.find(b'imgLevel\x00')
if pos == -1:
    pos = data.find(b'imgLevel')
print('imgLevel at', hex(pos))

# In TfrmQuarry, published fields have offsets
# Let's search for references to imgLevel
import re
for m in re.finditer(rb'imgLevel\b', data):
    print(hex(m.start()))
