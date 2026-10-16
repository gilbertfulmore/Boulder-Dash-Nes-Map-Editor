import zlib
import struct

def write_png(filename, width, height, rgba_data):
    # rgba_data is a bytes/bytearray of size width * height * 4
    # Scanline: 1 filter byte (0 = None) followed by width * 4 bytes
    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0) # filter type 0
        scanlines.extend(rgba_data[y * width * 4 : (y + 1) * width * 4])
    
    compressed = zlib.compress(bytes(scanlines))
    
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    
    png = (
        b'\x89PNG\r\n\x1a\n' +
        chunk(b'IHDR', ihdr) +
        chunk(b'IDAT', compressed) +
        chunk(b'IEND', b'')
    )
    
    with open(filename, 'wb') as f:
        f.write(png)

if __name__ == "__main__":
    # Test write
    test_data = bytearray([255, 0, 0, 255] * 16 * 16)
    write_png('test.png', 16, 16, test_data)
    print("PNG written successfully!")
