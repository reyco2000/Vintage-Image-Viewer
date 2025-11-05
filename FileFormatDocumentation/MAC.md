# MacPaint (.MAC) Format

## Overview

MacPaint was a bitmap graphics painting software developed by Apple Computer for the original Macintosh personal computer (released 1984). The .MAC format stores monochrome (black and white) bitmap images.

## Key Characteristics

- **Standard Dimensions**: 576 × 720 pixels (fixed size)
- **Color Depth**: 1-bit monochrome (black and white only)
- **Compression**: PackBits RLE (Run-Length Encoding)
- **File Extension**: .MAC
- **Platform**: Classic Macintosh
- **Year**: 1984
- **Developer**: Apple Computer

## File Structure

### Standard MacPaint Format

```
Offset    Size    Description
------    ----    -----------
0x000     512     Header (often empty or contains fill patterns)
0x200     var     Compressed image data (PackBits encoded)
```

### Header (512 bytes)

The header is typically 512 bytes and may contain:
- Version information
- Fill patterns (8×8 pixel patterns for paint bucket tool)
- Often empty or zeroed out in saved files

### Image Data

The image data immediately follows the 512-byte header and is compressed using PackBits algorithm. The data represents a 576×720 pixel monochrome bitmap.

**Pixel Layout**:
- Each byte represents 8 horizontal pixels
- Bit value 0 = white pixel
- Bit value 1 = black pixel
- Most significant bit (MSB) first
- Total uncompressed size: 72 bytes/line × 720 lines = 51,840 bytes

## PNTG Variant (.MAC files)

Some .MAC files use a different format called PNTG (PaiNT Group), which has a different structure but the same final dimensions.

### PNTG .MAC File Structure

```
Offset    Size    Description
------    ----    -----------
0x00      64      Filename and padding
0x40      8       Signature: "PNTGMPNT" (identifies PNTG format)
0x48      8       Version/flags
0x50      4       Width in header (MISLEADING - ignore!)
0x54      4       Height in header (MISLEADING - ignore!)
0x58      40      Additional header data
0x80      512     Pattern table (64 patterns × 8 bytes each)
0x280     var     PackBits compressed image data
```

**Important Note**: The width and height stored in the PNTG header (at offsets 0x50-0x57) are often incorrect or misleading. Always use the standard MacPaint dimensions (576×720) for decoding.

## PackBits Compression

PackBits is a simple run-length encoding (RLE) compression algorithm developed by Apple for MacPaint.

### Algorithm Specification

PackBits uses a single flag byte to indicate whether data should be copied literally or repeated:

#### Flag Byte Interpretation

- **Flag < 128** (0-127): **Literal run**
  - Count = flag + 1 (1 to 128 bytes)
  - Copy the next `count` bytes literally from input to output

- **Flag > 128** (129-255): **Repeat run**
  - Count = 257 - flag (2 to 128 repetitions)
  - Repeat the next byte `count` times

- **Flag == 128**: **No-op**
  - Skip this byte (reserved/padding)
  - No data follows

### Encoding Examples

**Example 1: Literal Run**
```
Input bytes:    0x03 0xAA 0xBB 0xCC 0xDD
Interpretation: flag=0x03 → count = 3 + 1 = 4 literal bytes
Output:         0xAA 0xBB 0xCC 0xDD
```

**Example 2: Repeat Run**
```
Input bytes:    0xFE 0x42
Interpretation: flag=0xFE → count = 257 - 254 = 3 repetitions
Output:         0x42 0x42 0x42
```

**Example 3: Mixed Data**
```
Input:  0x00 0xFF 0xFD 0xAA 0x02 0x11 0x22 0x33

0x00 0xFF        → Literal run (count=1): 0xFF
0xFD 0xAA        → Repeat run (count=4): 0xAA 0xAA 0xAA 0xAA
0x02 0x11 0x22 0x33 → Literal run (count=3): 0x11 0x22 0x33

Output: 0xFF 0xAA 0xAA 0xAA 0xAA 0x11 0x22 0x33
```

## Decoding Process

### Standard MacPaint Decoding

1. **Read file into memory**
2. **Skip header** (first 512 bytes)
3. **Detect compression**: Check if data appears compressed (first byte > 128 often indicates PackBits)
4. **Decompress using PackBits algorithm**
5. **Convert bits to pixels**:
   - Each byte contains 8 pixels
   - MSB first (bit 7 → bit 0)
   - 0 = white (255), 1 = black (0)
6. **Create 576×720 monochrome image**

### PNTG .MAC Decoding

1. **Read file into memory**
2. **Check for "PNTG" signature** at offset 0x40
3. **Ignore dimensions in header** (use 576×720 instead)
4. **Skip to offset 0x280** (data starts after pattern table)
5. **Decompress using PackBits algorithm**
6. **Convert bits to pixels** (same as standard MacPaint)
7. **Create 576×720 monochrome image**

## Bit Expansion for Monochrome Images

After PackBits decompression, each byte must be expanded to 8 pixels:

```python
def expand_bits_to_pixels(bytes_data, width, height):
    pixels = []

    for byte in bytes_data:
        # Process bits from MSB to LSB (bit 7 → bit 0)
        for bit_position in range(7, -1, -1):
            bit_value = (byte >> bit_position) & 1

            # Convention: 0 = white, 1 = black
            pixel_value = 255 if bit_value == 0 else 0
            pixels.append(pixel_value)

            if len(pixels) >= width * height:
                break

    return pixels[:width * height]
```

## Implementation Reference

See `vintage_image_viewer.py`:
- `MACImageDecoder.decode()` - Main decoder entry point
- `MACImageDecoder._decompress_packbits()` - PackBits decompression
- `MACImageDecoder._decode_bitmap()` - Uncompressed bitmap decoding

## Common Challenges

### Challenge 1: PNTG Misleading Dimensions

**Problem**: PNTG files store incorrect dimensions in their headers.

**Solution**:
- Detect PNTG signature ("PNTG" or "PNTGMPNT")
- Ignore header dimensions
- Use fixed 576×720 dimensions

```python
if b'PNTG' in data[:100]:
    # PNTG variant - ignore header dimensions
    width = 576
    height = 720
```

### Challenge 2: Bit Order and Pixel Polarity

**Problem**: Need to correctly interpret bit order and pixel values.

**Solution**:
- MacPaint/PNTG: MSB first, 0=white, 1=black

```python
for bit in range(7, -1, -1):  # MSB first
    bit_value = (byte >> bit) & 1
    pixel = 255 if bit_value == 0 else 0  # 0=white
```

## Compression Efficiency

PackBits is most efficient for:
- **Highly repetitive data** (solid colors, patterns)
- **Monochrome images** with large solid regions
- **Simple graphics** (line drawings, text)

Worst case: Data expands by ~0.8% when no runs exist:
- Every byte requires 2 bytes in output (flag + data)
- 100 bytes of random data → 101 bytes compressed (1% expansion)

Best case: Highly repetitive data compresses dramatically:
- 1000 identical bytes → 2 bytes compressed (99.8% reduction)

## Historical Context

PackBits was developed by Apple in 1984 for MacPaint and later standardized in TIFF (Tag Image File Format) as compression type 32773. It remains in use today for its simplicity and speed.

MacPaint was revolutionary as one of the first widely-used bitmap graphics editors on a personal computer, introducing many users to digital painting concepts.

## Related Formats

- **TIFF**: Uses PackBits as compression option 32773
- **PNTG (.PIC)**: Same compression, different header
- **BMP**: Uncompressed Windows equivalent

---

*Last updated: 2025-11-04*
