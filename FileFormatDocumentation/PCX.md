# PCX (.PCX) Format

## Overview

PCX (PC Paintbrush eXchange) is a raster image file format developed by ZSoft Corporation for their PC Paintbrush software in 1985. It became one of the first widely accepted DOS imaging standards and remained popular throughout the 1980s and 1990s.

## Key Characteristics

- **Dimensions**: Variable (stored in header)
- **Color Depth**: 1, 2, 4, 8, or 24 bits per pixel
- **Compression**: PCX RLE (Run-Length Encoding)
- **Magic Byte**: 0x0A (manufacturer byte)
- **File Extension**: .PCX
- **Platform**: DOS/Windows/PC
- **Year**: 1985
- **Developer**: ZSoft Corporation
- **Endianness**: Little-endian (Intel byte order)

## Historical Context

PCX was one of the first image formats to gain widespread adoption on IBM PC-compatible computers. It predates more sophisticated formats like GIF (1987) and JPEG (1992). Despite being superseded by more efficient formats, PCX files are still encountered in legacy systems and retro computing.

## File Structure

### PCX Header (128 bytes)

```
Offset    Size    Type      Description
------    ----    ----      -----------
0x00      1       byte      Manufacturer (always 0x0A for PCX)
0x01      1       byte      Version
                              0 = PC Paintbrush v2.5
                              2 = PC Paintbrush v2.8 with palette
                              3 = PC Paintbrush v2.8 without palette
                              4 = PC Paintbrush for Windows
                              5 = PC Paintbrush v3.0+
0x02      1       byte      Encoding (1 = RLE compression)
0x03      1       byte      Bits per pixel per plane (1, 2, 4, or 8)
0x04      2       word      X minimum (left) - usually 0
0x06      2       word      Y minimum (top) - usually 0
0x08      2       word      X maximum (right)
0x0A      2       word      Y maximum (bottom)
0x0C      2       word      Horizontal DPI
0x0E      2       word      Vertical DPI
0x10      48      bytes     16-color EGA palette (16 RGB triplets)
0x40      1       byte      Reserved (should be 0)
0x41      1       byte      Number of bit planes
                              1 = Monochrome, grayscale, or 256-color
                              3 = 24-bit RGB (8 bits per plane)
                              4 = 16-color (EGA/VGA)
0x42      2       word      Bytes per line per plane (always even)
0x44      2       word      Palette type
                              1 = Color or monochrome
                              2 = Grayscale
0x46      2       word      Horizontal screen size (optional)
0x48      2       word      Vertical screen size (optional)
0x4A      54      bytes     Reserved (filler to complete 128 bytes)
```

### Image Dimensions Calculation

```
width = (x_max - x_min) + 1
height = (y_max - y_min) + 1
```

### Image Data (starts at offset 128)

Immediately after the 128-byte header, the RLE-compressed image data begins. The data is organized as follows:

- **Scanline-based**: Image is encoded line by line from top to bottom
- **Planar organization**: For multi-plane images, all planes for one scanline are stored before moving to the next scanline
- **Plane order**: Red, Green, Blue, Intensity (for 4-plane images)

### VGA Palette (256-color images only)

For 8-bit images (256 colors), an extended palette is stored at the end of the file:

```
Offset              Size    Description
------              ----    -----------
file_end - 769      1       Palette marker (0x0C)
file_end - 768      768     VGA palette (256 RGB triplets, 3 bytes each)
```

Each RGB triplet uses full 8-bit values (0-255).

## PCX RLE Compression

PCX uses a byte-oriented RLE compression scheme that is simpler than PackBits.

### Compression Rules

- **Bytes 0x00-0xBF** (0-191): Single pixel value (copy literally)
  - These bytes represent actual pixel data
  - No repetition, just the pixel value itself

- **Bytes 0xC0-0xFF** (192-255): Run-length indicator
  - Top 2 bits are set (bitwise AND with 0xC0 = 0xC0)
  - Run count = byte AND 0x3F (mask off top 2 bits)
  - Next byte is the pixel value to repeat
  - Count ranges from 0 to 63

### Algorithm Pseudocode

```python
def decompress_pcx_scanline(data, bytes_per_line):
    scanline = []
    i = 0

    while len(scanline) < bytes_per_line and i < len(data):
        byte = data[i]
        i += 1

        if (byte & 0xC0) == 0xC0:
            # Run-length encoded
            count = byte & 0x3F
            if i < len(data):
                value = data[i]
                i += 1
                scanline.extend([value] * count)
        else:
            # Literal pixel value
            scanline.append(byte)

    return scanline, i
```

### Encoding Examples

**Example 1: Literal Values**
```
Input:  0x42
Output: 0x42 (single pixel with value 66)

Input:  0x00 0x7F 0xBF
Output: 0x00 0x7F 0xBF (three pixels)
```

**Example 2: Run-Length Encoded**
```
Input:  0xC5 0xFF
        0xC0 + 5 = run of 5
Output: 0xFF 0xFF 0xFF 0xFF 0xFF (five pixels, value 255)

Input:  0xC1 0x00
        0xC0 + 1 = run of 1
Output: 0x00 (one pixel, value 0)
```

**Example 3: Mixed Data**
```
Input:  0x42 0xC3 0xFF 0x7E 0xC8 0x00

0x42         → Literal: 0x42
0xC3 0xFF    → Run of 3: 0xFF 0xFF 0xFF
0x7E         → Literal: 0x7E
0xC8 0x00    → Run of 8: 0x00 (8 times)

Output: 0x42 0xFF 0xFF 0xFF 0x7E 0x00 0x00 0x00 0x00 0x00 0x00 0x00 0x00
```

## Color Modes

PCX supports multiple color modes determined by bits_per_pixel and num_planes:

### Mode 1: Monochrome (1-bit, 1 plane)

- **Configuration**: 1 bit/pixel, 1 plane
- **Colors**: 2 (black and white)
- **Data Organization**: 1 bit per pixel, packed into bytes
- **Decoding**: Expand bits MSB-first

```python
for byte in scanline:
    for bit in range(7, -1, -1):
        pixel = 255 if (byte >> bit) & 1 else 0
```

### Mode 2: 16-Color EGA/VGA (1-bit, 4 planes)

- **Configuration**: 1 bit/pixel, 4 planes (RGBI)
- **Colors**: 16 colors from EGA palette
- **Data Organization**: 4 bitplanes, one bit per pixel per plane
- **Palette**: 16 colors from header (offset 0x10-0x3F)

**Plane Organization**:
```
Scanline layout: [Plane0: bytes_per_line] [Plane1: bytes_per_line]
                 [Plane2: bytes_per_line] [Plane3: bytes_per_line]
```

**Pixel Decoding** (4-plane to color index):
```python
# Extract one bit from each plane
bit0 = (plane0_byte >> bit_position) & 1
bit1 = (plane1_byte >> bit_position) & 1
bit2 = (plane2_byte >> bit_position) & 1
bit3 = (plane3_byte >> bit_position) & 1

# Combine into color index (0-15)
color_index = (bit3 << 3) | (bit2 << 2) | (bit1 << 1) | bit0

# Look up color in EGA palette
rgb = palette[color_index]
```

**Standard EGA Palette**:
```
0: Black         (0,0,0)         8: Dark Gray      (85,85,85)
1: Blue          (0,0,170)       9: Light Blue     (85,85,255)
2: Green         (0,170,0)       10: Light Green   (85,255,85)
3: Cyan          (0,170,170)     11: Light Cyan    (85,255,255)
4: Red           (170,0,0)       12: Light Red     (255,85,85)
5: Magenta       (170,0,170)     13: Light Magenta (255,85,255)
6: Brown         (170,85,0)      14: Yellow        (255,255,85)
7: Light Gray    (170,170,170)   15: White         (255,255,255)
```

### Mode 3: 16-Color (4-bit, 1 plane)

- **Configuration**: 4 bits/pixel, 1 plane
- **Colors**: 16 colors
- **Data Organization**: 2 pixels per byte (upper and lower nibbles)
- **Palette**: 16 colors from header

```python
for byte in scanline:
    pixel1 = (byte >> 4) & 0x0F  # Upper nibble
    pixel2 = byte & 0x0F          # Lower nibble
```

### Mode 4: 256-Color (8-bit, 1 plane)

- **Configuration**: 8 bits/pixel, 1 plane
- **Colors**: 256 colors from VGA palette
- **Data Organization**: 1 byte per pixel
- **Palette**: 768 bytes at end of file (after marker 0x0C)

**Palette Location**:
```python
if len(file_data) >= 769 and file_data[-769] == 0x0C:
    palette_data = file_data[-768:]  # Last 768 bytes
```

**Palette Format**: 256 RGB triplets (R, G, B), each component 0-255

### Mode 5: 24-bit RGB (8-bit, 3 planes)

- **Configuration**: 8 bits/pixel, 3 planes (RGB)
- **Colors**: 16.7 million (true color)
- **Data Organization**: 3 planes of 8-bit data
- **No palette**: Direct RGB values

**Scanline Organization**:
```
[Red plane: bytes_per_line] [Green plane: bytes_per_line] [Blue plane: bytes_per_line]
```

## Decoding Process

### General PCX Decoding Steps

1. **Read and validate header**:
   ```python
   if data[0] != 0x0A:
       raise ValueError("Not a valid PCX file")
   ```

2. **Parse header fields**:
   ```python
   version = data[1]
   encoding = data[2]  # Should be 1 for RLE
   bits_per_pixel = data[3]
   x_min = struct.unpack('<H', data[4:6])[0]
   y_min = struct.unpack('<H', data[6:8])[0]
   x_max = struct.unpack('<H', data[8:10])[0]
   y_max = struct.unpack('<H', data[10:12])[0]
   width = x_max - x_min + 1
   height = y_max - y_min + 1
   num_planes = data[65]
   bytes_per_line = struct.unpack('<H', data[66:68])[0]
   ```

3. **Extract palette** (if needed):
   - 16-color: Read from header offset 0x10
   - 256-color: Read from end of file (last 768 bytes)

4. **Decompress image data**:
   - Start at offset 128
   - Decode scanline by scanline
   - Each scanline has `bytes_per_line × num_planes` bytes

5. **Convert to pixels**:
   - Depends on color mode
   - Handle bit expansion, plane combining, or palette lookup

6. **Create final image**

### Scanline Padding

**Important**: PCX scanlines are padded to ensure `bytes_per_line` is always even. When extracting pixels:

```python
# Only extract 'width' pixels from each scanline
# Ignore padding bytes at the end

for scanline in scanlines:
    if mode == '1-bit':
        # Extract 'width' bits, ignore extra
        pixels_extracted = 0
        for byte in scanline:
            if pixels_extracted >= width:
                break
            # Extract bits...
```

## Implementation Reference

See `vintage_image_viewer.py`:
- `PCXImageDecoder.decode()` - Main decoder entry point
- `PCXImageDecoder._decode_rle()` - RLE decompression
- `PCXImageDecoder._decode_8bit()` - 8-bit image decoding
- `PCXImageDecoder._decode_1bit()` - Monochrome decoding
- `PCXImageDecoder._decode_4bit()` - 16-color (4-bit) decoding
- `PCXImageDecoder._decode_planar()` - Planar (EGA/VGA) decoding

## Common Challenges

### Challenge 1: Images with x_min/y_min ≠ 0

Some PCX files have non-zero origin coordinates:

```python
x_min, y_min = 100, 50
x_max, y_max = 739, 549

# Correct calculation
width = x_max - x_min + 1   # 640
height = y_max - y_min + 1  # 500

# Not: width = x_max + 1 (wrong!)
```

### Challenge 2: Scanline Padding

**Problem**: Scanlines may be padded to word/byte boundaries.

**Solution**: Only extract 'width' pixels, ignore padding:
```python
bytes_per_line = struct.unpack('<H', data[66:68])[0]
# bytes_per_line may be larger than (width * bits_per_pixel) / 8
# Only extract 'width' pixels per scanline
```

### Challenge 3: Endianness

**Problem**: PCX uses little-endian byte order.

**Solution**: Use appropriate unpacking:
```python
import struct
# Little-endian (PCX format)
width = struct.unpack('<H', data[0:2])[0]  # '<' = little-endian
```

## Advantages and Limitations

### Advantages

- **Simple format**: Easy to implement
- **Widely supported**: Most imaging software can read PCX
- **Flexible**: Supports 1 to 24-bit color
- **Compressed**: RLE reduces file size for simple images
- **No licensing**: Public format, no patents or fees

### Limitations

- **Poor compression**: RLE is less efficient than modern algorithms (PNG, JPEG)
- **Scanline-based**: Cannot skip to arbitrary positions
- **File size overhead**: 128-byte header for every image
- **Palette limitations**: 256-color palette not ideal for photographs
- **Obsolete**: Superseded by GIF, PNG, JPEG

## Related Formats

- **PICtor (.PIC)**: Earlier ZSoft format
- **BMP**: Windows bitmap (uncompressed)
- **GIF**: More advanced LZW compression
- **TIFF**: More sophisticated with multiple compression options

---

*Last updated: 2025-11-04*
