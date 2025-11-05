# TIFF (.TIF/.TIFF) Format

## Overview

TIFF (Tagged Image File Format) is a flexible, adaptable file format for handling images and data within a single file. TIFF was originally created by Aldus Corporation in 1986 and is now controlled by Adobe Systems. It remains one of the most widely supported and versatile image formats.

## Key Characteristics

- **Dimensions**: Variable (no limits in specification)
- **Color Depth**: 1 to 64 bits per channel
- **Compression**: Multiple options (uncompressed, LZW, PackBits, JPEG, ZIP, etc.)
- **Magic Bytes**:
  - Little-endian: `0x49 0x49 0x2A 0x00` ("II*\0")
  - Big-endian: `0x4D 0x4D 0x00 0x2A` ("MM\0*")
- **File Extension**: .TIF or .TIFF
- **Platform**: Cross-platform (Windows, Mac, Linux, Unix)
- **Year**: 1986 (ongoing revisions)
- **Developer**: Originally Aldus Corporation, now Adobe Systems

## Historical Context

TIFF was designed to become the standard for storing scanned images and has grown to support a wide variety of image types including:
- Bilevel (black and white)
- Grayscale
- Palette color
- Full color (RGB)
- CMYK (for printing)
- Lab color
- YCbCr

The format's flexibility made it popular for:
- Desktop publishing
- Document imaging and archiving
- Medical imaging (DICOM uses TIFF)
- Geospatial data (GeoTIFF)
- Professional photography

## File Structure

### Basic Structure

TIFF files are organized using a tag-based structure:

```
Offset    Size    Description
------    ----    -----------
0x00      2       Byte order (II = little-endian, MM = big-endian)
0x02      2       Version (always 42, 0x002A)
0x04      4       Offset to first IFD (Image File Directory)
var       var     Image data and IFDs
```

### Image File Directory (IFD)

An IFD contains information about the image:
- Image dimensions
- Color space
- Compression type
- Bits per sample
- Photometric interpretation
- Strip/tile organization
- And many other optional tags

### Common TIFF Tags

- **ImageWidth** (256): Width of the image in pixels
- **ImageLength** (257): Height of the image in pixels
- **BitsPerSample** (258): Number of bits per channel
- **Compression** (259): Compression scheme used
  - 1 = No compression
  - 2 = CCITT Group 3
  - 5 = LZW
  - 32773 = PackBits
  - 7 = JPEG
  - 8 = Deflate (ZIP)
- **PhotometricInterpretation** (262): Color space
  - 0 = WhiteIsZero
  - 1 = BlackIsZero
  - 2 = RGB
  - 3 = Palette color
  - 4 = Transparency mask
  - 5 = CMYK
- **StripOffsets** (273): Byte offset of each strip
- **SamplesPerPixel** (277): Number of channels
- **RowsPerStrip** (278): Number of rows per strip
- **StripByteCounts** (279): Byte count for each strip

## Color Modes

TIFF supports numerous color modes:

### Bilevel (1-bit)
- Black and white images
- Each pixel is 1 bit
- Common in document scanning

### Grayscale (8-bit or 16-bit)
- Shades of gray
- 8-bit: 256 levels
- 16-bit: 65,536 levels (for high dynamic range)

### Palette Color
- Indexed color using a color palette
- Up to 256 colors typically

### RGB (24-bit or 48-bit)
- Full color images
- 24-bit: 8 bits per channel (R, G, B)
- 48-bit: 16 bits per channel (for high color depth)

### CMYK (32-bit or 64-bit)
- For printing and prepress
- Cyan, Magenta, Yellow, Black channels

### RGBA (32-bit or 64-bit)
- RGB with alpha transparency channel

## Compression Methods

TIFF supports multiple compression algorithms:

### No Compression (Type 1)
- Uncompressed pixel data
- Large file sizes but fast to decode
- Lossless

### PackBits (Type 32773)
- Simple run-length encoding
- Same algorithm used in MacPaint
- Lossless
- See [MAC.md](MAC.md) for PackBits details

### LZW (Type 5)
- Lempel-Ziv-Welch compression
- Lossless
- Good compression for most images
- Patent issues resolved (expired)

### JPEG (Type 7)
- Lossy compression
- Used for photographic images
- Can achieve high compression ratios
- Quality/size tradeoff

### Deflate/ZIP (Type 8)
- Lossless compression
- Similar to PNG compression
- Good compression for most images

### CCITT Group 3/4
- Fax compression
- For bilevel (1-bit) images
- Lossless

## Decoding with PIL/Pillow

In the Vintage Image Viewer, TIFF files are decoded using PIL's native TIFF support:

```python
def decode(file_path):
    # Use PIL's native TIFF support
    img = Image.open(file_path)

    # Convert to RGB if needed for consistent display
    if img.mode in ('RGBA', 'P', 'LA'):
        img = img.convert('RGB')
    elif img.mode not in ('RGB', 'L', '1'):
        # Convert any other modes to RGB
        img = img.convert('RGB')

    return img
```

### Supported Modes

PIL/Pillow automatically handles:
- All standard TIFF compressions
- Multiple color modes
- Big-endian and little-endian byte orders
- Multi-page TIFF files
- Various bit depths

## Implementation Reference

See `vintage_image_viewer.py`:
- `TIFImageDecoder.decode()` - TIFF decoder using PIL

## Advantages

- **Universal support**: Widely supported across platforms and applications
- **Flexible**: Supports many color modes and bit depths
- **High quality**: Lossless compression options preserve image quality
- **Metadata**: Extensive tag system for storing image information
- **Multi-page**: Can store multiple images in one file
- **Professional**: Industry standard for publishing, printing, archiving

## Limitations

- **File size**: Uncompressed or losslessly compressed files can be large
- **Complexity**: Tag-based structure more complex than simpler formats
- **Compatibility**: Some TIFF features not supported by all readers
- **No animation**: Unlike GIF, does not support animation

## Common Use Cases

- **Document scanning**: Standard format for scanned documents
- **Professional photography**: RAW conversions and master files
- **Printing and prepress**: CMYK color space support
- **Archival**: Lossless storage of important images
- **Medical imaging**: DICOM standard uses TIFF
- **Geospatial**: GeoTIFF for geographic data

## Relationship to Vintage Formats

TIFF has historical connections to some vintage formats supported by this viewer:

### PackBits Compression
- TIFF compression type 32773 uses PackBits
- Same algorithm as MacPaint (.MAC format)
- See [MAC.md](MAC.md) for details

### LZW Compression
- More advanced than RLE compression in .ART, .PIC, .PCX
- Replaced simple RLE in professional applications

## File Identification

Quick identification of TIFF files:

```bash
# Check magic bytes (little-endian)
xxd -l 4 file.tif
# Should show: 4949 2a00  (II*\0)

# Or big-endian:
# Should show: 4d4d 002a  (MM\0*)

# Python detection
with open('file.tif', 'rb') as f:
    magic = f.read(4)
    is_tiff = (magic == b'II*\x00' or magic == b'MM\x00*')
```

## Extensions and Variants

### BigTIFF
- Extended TIFF for files > 4GB
- Uses 64-bit offsets instead of 32-bit
- Supported by modern software

### GeoTIFF
- TIFF with georeferencing information
- Used for satellite imagery and maps
- Stores coordinate system and projection data

### TIFF/EP
- TIFF for Electronic Photography
- Used in digital cameras
- Supports camera-specific metadata

### DNG (Digital Negative)
- Adobe's open RAW image format
- Based on TIFF/EP
- Stores camera RAW data

## Specifications

- **Official Specification**: TIFF Revision 6.0 (1992)
- **Current Maintainer**: Adobe Systems
- **Standards**: ISO 12639:2004 (Electronic imaging)

## Related Formats

- **PNG**: Simpler lossless format with alpha transparency
- **JPEG**: Lossy compression for photographs
- **BMP**: Windows bitmap (simpler, uncompressed)
- **PCX**: Earlier DOS format (.PCX)
- **GIF**: Indexed color with animation

---

*Last updated: 2025-11-04*
