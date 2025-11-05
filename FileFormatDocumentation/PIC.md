# PICtor/PNTG (.PIC) Format

## Overview

The .PIC extension is used by multiple incompatible formats from the DOS/early PC era. The two main variants are:

1. **PICtor** (PC Paint) - Standard PC graphics format
2. **PNTG** (PaiNT Group) - Macintosh-origin format with PNTG signature

## Variant 1: Standard PICtor Format

### Key Characteristics

- **Dimensions**: Variable (stored in header)
- **Color Depth**: 1, 4, or 8 bits per pixel
- **Compression**: RLE (Run-Length Encoding)
- **Magic Bytes**: 0x1234 (little-endian: 0x34 0x12)
- **Platform**: DOS/PC
- **Year**: 1984-1985
- **Developer**: ZSoft Corporation

### File Structure

```
Offset    Size    Description
------    ----    -----------
0x00      2       Magic number: 0x1234 (0x34 0x12 in little-endian)
0x02      2       Width (16-bit, little-endian)
0x04      2       Height (16-bit, little-endian)
0x06      1       Bits per pixel (1, 4, or 8)
0x07      10      Additional header info
0x11      var     Optional palette data (for 8-bit images)
var       var     RLE-compressed image data
```

### PICtor RLE Compression

The PICtor format uses a simple RLE scheme:

- **Bytes 0x00-0xBF**: Literal pixel value (copy as-is)
- **Bytes 0xC0-0xFF**: Run-length indicator
  - Run length = byte - 0xC0
  - Next byte is the pixel value to repeat

**Example**:
```
0xC5 0x42  →  Repeat 0x42 five times (0xC5 - 0xC0 = 5)
0x7F       →  Literal pixel value 0x7F
```

### Palette Storage (8-bit images)

For 8-bit PICtor images, the palette is stored after the header:
- 256 colors × 3 bytes (RGB)
- Each component uses 6-bit color (0-63), needs scaling to 8-bit (0-255)
- Scaling formula: `color_8bit = (color_6bit × 255) / 63`

## Variant 2: PNTG Format (.PIC files)

### Key Characteristics

- **Dimensions**: 576 × 720 pixels (same as MacPaint)
- **Color Depth**: 1-bit monochrome
- **Compression**: PackBits (same as MacPaint)
- **Signature**: "PNTGMPNT" or "PNTG" in first 100 bytes
- **Platform**: Originally Macintosh, ported to PC
- **Year**: ~1985-1990

### File Structure

```
Offset    Size    Description
------    ----    -----------
0x00      64      Filename and padding
0x40      8       Signature: "PNTGMPNT"
0x48      8       Version/flags
0x50      4       Width (MISLEADING - do not use!)
0x54      4       Height (MISLEADING - do not use!)
0x58      40      Additional header data
0x80      512     Pattern table (64 patterns × 8 bytes)
0x280     var     PackBits compressed image data
```

### Critical Notes About PNTG

1. **Misleading Dimensions**: The width/height stored at offsets 0x50-0x57 are often incorrect (e.g., 128×30). Always use 576×720 for PNTG files.

2. **Pattern Table**: The 512-byte pattern table at offset 0x80 contains 64 fill patterns (8×8 pixels each) used by the paint program. This data is skipped during image decoding.

3. **Same as MacPaint**: PNTG uses identical compression and pixel layout to MacPaint, just with a different header structure.

## Decoding Process

### Standard PICtor Decoding

1. **Read file and verify magic bytes** (0x34 0x12)
2. **Parse header**:
   - Read width, height (little-endian)
   - Read bits per pixel
3. **Load palette** (if 8-bit image)
4. **Decompress RLE data**:
   - For each byte:
     - If byte ≥ 0xC0: Run (repeat next byte `byte - 0xC0` times)
     - If byte < 0xC0: Literal (copy byte as-is)
5. **Convert to image**:
   - 1-bit: Expand bits to pixels
   - 4-bit: Two pixels per byte (upper and lower nibbles)
   - 8-bit: Apply palette

### PNTG .PIC Decoding

1. **Read file and check for "PNTG" signature**
2. **Ignore header dimensions** (use 576×720)
3. **Skip to offset 0x280** (after pattern table)
4. **Decompress using PackBits algorithm** (see [MAC.md](MAC.md) for details)
5. **Convert bits to pixels** (same as MacPaint)
6. **Create 576×720 monochrome image**

## Format Detection

To distinguish between PICtor and PNTG variants:

```python
if b'PNTG' in data[:100] or b'PICT' in data[:100]:
    # PNTG variant
    use_pntg_decoder()
elif data[0] == 0x34 and data[1] == 0x12:
    # Standard PICtor
    use_pictor_decoder()
else:
    # Unknown or generic format
    use_generic_decoder()
```

## Implementation Reference

See `vintage_image_viewer.py`:
- `PICImageDecoder.decode()` - Main decoder entry point
- `PICImageDecoder._decode_pict_variant()` - PNTG variant decoder
- `PICImageDecoder._decode_pictor_standard()` - Standard PICtor decoder
- `PICImageDecoder._decompress_packbits_for_pntg()` - PackBits decompression
- `PICImageDecoder._decode_pntg_rle()` - PNTG RLE decoder
- `PICImageDecoder._decode_pic_data()` - PICtor RLE decompression

## Common Challenges

### Challenge 1: Multiple File Format Variants

**Problem**: Same extension (.PIC) used by incompatible formats.

**Solution**: Implement format detection cascade:
```python
# Try signatures first
if b'PNTG' in data[:100]:
    return decode_pntg()
elif data[0:2] == b'\x34\x12':
    return decode_pictor()
else:
    return decode_generic()
```

### Challenge 2: PNTG Misleading Dimensions

**Problem**: PNTG files store incorrect dimensions in their headers.

**Solution**:
```python
if b'PNTG' in data[:100]:
    # PNTG variant - ignore header dimensions
    width = 576
    height = 720
```

### Challenge 3: Color Palette Scaling

**Problem**: PICtor uses 6-bit color (0-63), modern displays use 8-bit (0-255).

**Solution**: Scale palette values correctly:
```python
# Read 6-bit palette
for i in range(256):
    r6 = palette_data[i * 3 + 0]  # 0-63
    g6 = palette_data[i * 3 + 1]  # 0-63
    b6 = palette_data[i * 3 + 2]  # 0-63

    # Scale to 8-bit (0-255)
    r8 = (r6 * 255) // 63
    g8 = (g6 * 255) // 63
    b8 = (b6 * 255) // 63
```

## Related Formats

- **MacPaint (.MAC)**: PNTG variant is nearly identical
- **PCX**: More standardized DOS image format
- **GIF**: More advanced compression (replaced PICtor)

---

*Last updated: 2025-11-04*
