# AOL Art (.ART) Format

## Overview

AOL Art files (.ART) were used by America Online (AOL) for graphics in the 1990s. The format has multiple incompatible variants, making it one of the most challenging vintage formats to decode.

## Key Characteristics

- **Dimensions**: Variable (often 640×480 or 320×200)
- **Color Depth**: 1, 4, 8, or 24 bits per pixel
- **Compression**: Various (RLE, none, proprietary)
- **No consistent magic bytes**: Multiple format variants
- **Platform**: DOS/Windows (AOL software)
- **Year**: 1991+
- **Developer**: AOL Inc.

## Format Variants

### Variant 1: Standard Bitmap ART

```
Offset    Size    Description
------    ----    -----------
0x00      2       Format marker (often 0x00 0x00)
0x02      2       Width (16-bit, little-endian)
0x04      2       Reserved/flags
0x06      2       Height (16-bit, little-endian)
0x08      8       Additional header data
0x10      var     Bitmap data (word-aligned scanlines)
```

**Scanline Alignment**:
- Scanlines are aligned to 16-bit (2-byte) boundaries
- Each scanline may have padding bytes at the end
- Formula: `bytes_per_line = ((width + 7) / 8 + 1) / 2 * 2`

**Scanline Offset Quirk**:
- Image data has an 8-byte horizontal offset within each scanline
- Must skip first 8 bytes of padding per scanline
- This causes a "shift" that needs correction during decoding

### Variant 2: AOL-Signature ART

```
Offset    Size    Description
------    ----    -----------
0x00      4       Signature: "ART\x00"
0x04      2       Width (16-bit, little-endian)
0x06      2       Height (16-bit, little-endian)
0x08      var     Header data
0x10      var     RLE-compressed data
```

### Variant 3: PFS First Publisher ART

```
Offset    Size    Description
------    ----    -----------
0x00      2       Format marker: 0x01 0x00
0x02      2       Width (16-bit, little-endian)
0x04      2       Height (16-bit, little-endian)
0x06      4       Additional header
0x0A      var     Bitmap data
```

## Decoding Process

### General ART Decoding Strategy

Since .ART has no consistent format, use a detection cascade:

1. **Check first 2 bytes for 0x00 0x00**:
   - Try standard bitmap format
   - Validate dimensions are reasonable (1-4096)
   - Check if file size matches expected bitmap size

2. **Check for "ART\x00" signature**:
   - Parse AOL-style header
   - Decompress using AOL RLE variant

3. **Check for 0x01 0x00 marker**:
   - Try PFS First Publisher format
   - Simple bitmap interpretation

4. **Fall back to generic decoding**:
   - Try common resolutions (320×200, 640×480, etc.)
   - Interpret as raw bitmap data

### AOL RLE Decompression

AOL uses a RLE variant:

- **Byte > 128**: Run-length indicator
  - Count = byte - 128
  - Next byte is the value to repeat

- **Byte ≤ 128 and byte > 0**: Literal run
  - Count = byte
  - Copy next `count` bytes literally

- **Byte = 0**: Skip/padding

**Example**:
```
0x85 0xFF  →  Repeat 0xFF five times (0x85 - 0x80 = 5)
0x03 0x12 0x34 0x56  →  Copy three bytes: 0x12, 0x34, 0x56
```

### Standard Bitmap ART Decoding

1. **Parse header** (get width, height)
2. **Calculate scanline parameters**:
   ```
   unaligned_bytes = (width + 7) / 8
   bytes_per_line = ((unaligned_bytes + 1) / 2) * 2  # Round to even
   scanline_offset = bytes_per_line - 8  # Skip first 8 bytes
   ```
3. **For each scanline**:
   - Start at: `header_size + row * bytes_per_line + scanline_offset`
   - Read `width` pixels from bitmap data
   - Convert bits to pixels (MSB first)

## Validation and Error Handling

When decoding .ART files:

1. **Validate dimensions**: Reject if width or height is 0, negative, or > 4096
2. **Check file size**: Ensure file is large enough for claimed dimensions
3. **Try multiple approaches**: If first decoder fails, try alternatives
4. **Use fallback dimensions**: Default to 320×200 or 640×480 if detection fails

## Implementation Reference

See `vintage_image_viewer.py`:
- `ARTImageDecoder.decode()` - Main decoder entry point
- `ARTImageDecoder._decode_bitmap_art()` - Standard bitmap decoding
- `ARTImageDecoder._decode_aol_art()` - AOL compressed format
- `ARTImageDecoder._decode_pfs_art()` - PFS First Publisher format
- `ARTImageDecoder._decode_generic_art()` - Generic fallback decoder
- `ARTImageDecoder._decompress_rle()` - RLE decompression

## Common Challenges

### Challenge 1: Multiple Format Variants

**Problem**: Same extension (.ART) used by incompatible formats.

**Solution**: Implement format detection cascade:
```python
# Try signatures first
if data[0:2] == b'\x00\x00':
    # Try standard bitmap
    return decode_bitmap_art()
elif data[0:4] == b'ART\x00':
    return decode_aol_art()
elif data[0:2] == b'\x01\x00':
    return decode_pfs_art()
else:
    return decode_generic()
```

### Challenge 2: Scanline Alignment and Padding

**Problem**: Scanlines padded to word boundaries with horizontal offset.

**Solution**: Calculate aligned scanline width and offset:
```python
bytes_per_line_unaligned = (width + 7) // 8
bytes_per_line = ((bytes_per_line_unaligned + 1) // 2) * 2
scanline_offset = bytes_per_line - 8

for row in range(height):
    row_start = offset + row * bytes_per_line + scanline_offset
    # Read pixels from row_start
```

### Challenge 3: Incomplete or Corrupt Data

**Problem**: Files may be truncated or have missing data.

**Solution**: Always validate and pad:
```python
if offset + required_bytes > len(data):
    pixels.extend([0] * (width * height - len(pixels)))

if width <= 0 or height <= 0 or width > 4096 or height > 4096:
    raise ValueError(f"Invalid dimensions: {width}x{height}")
```

## Best Practices

1. **Validate dimensions early**: Check for reasonable values before allocating memory
2. **Try multiple decoders**: If one variant fails, try others
3. **Graceful fallback**: Use default dimensions if detection fails
4. **Pad output**: Always ensure output has correct pixel count

## Related Formats

- PCX: More standardized DOS image format
- BMP: Windows bitmap format
- MacPaint: Macintosh equivalent from the same era

---

*Last updated: 2025-11-04*
