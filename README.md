# Vintage Image Viewer

A Python GUI application for viewing and converting vintage and legacy image formats including .ART (AOL Art), .MAC (MacPaint), .PIC (PICtor), .PCX (PC Paintbrush), and .TIF (TIFF).

## Features

- **Multi-format support**: Open .ART, .MAC, .PIC, .PCX, and .TIF image files
- **User-friendly GUI**: Clean interface with file browser and navigation
- **Image navigation**: Browse through all supported images in a directory
  - Previous/Next buttons
  - Keyboard shortcuts (Left/Right arrow keys)
  - Automatic directory scanning
- **Export capability**: Save opened images as PNG format
- **Scrollable canvas**: View large images with scrollbars
- **Format auto-detection**: Automatically identifies file format variants
- **Robust decoding**: Handles multiple format variants and compression schemes

## Supported Formats

### .ART (AOL Art)
- Multiple variants: AOL compressed, PFS First Publisher, standard bitmap
- Various compression schemes including RLE
- Color depths: 1, 4, 8, or 24-bit
- Platform: DOS/Windows (1991+)

### .MAC (MacPaint)
- Standard 576×720 monochrome images
- PackBits RLE compression
- PNTG variant support
- Platform: Classic Macintosh (1984)

### .PIC (PICtor/PNTG)
- PICtor format (DOS/PC)
- PNTG variant (Macintosh/PC)
- RLE and PackBits compression
- Color depths: 1, 4, or 8-bit
- Platform: DOS/PC/Mac (1984-1990)

### .PCX (PC Paintbrush)
- Industry standard DOS format
- PCX RLE compression
- Monochrome, EGA, VGA, and true color support
- Color depths: 1, 4, 8, or 24-bit
- Planar and packed modes
- Platform: DOS/Windows (1985+)

### .TIF/.TIFF (TIFF)
- Modern industry standard format
- Multiple compression options (LZW, PackBits, JPEG, ZIP, etc.)
- Full color depth support
- Cross-platform
- Platform: All (1986-present)

## Installation

### Requirements
- Python 3.7 or higher
- Pillow (PIL Fork) for image handling
- tkinter (usually included with Python)

### Install Dependencies

```bash
pip install -r requirements.txt
```

The `requirements.txt` contains:
```
Pillow>=9.0.0
```

## Usage

### Running the Application

```bash
python vintage_image_viewer.py
```

### Opening Images

1. Click **"Open Image"** button or use **File → Open Image** menu
2. Browse and select an image file (.art, .mac, .pic, .pcx, .tif, .tiff)
3. The image will be displayed in the viewer

### Navigating Images

When you open an image, the viewer automatically scans the directory for other supported images:

- **Next button** or **Right arrow key**: View next image in directory
- **Previous button** or **Left arrow key**: View previous image in directory
- Status bar shows current position (e.g., "3/12")

### Saving Images

1. Open an image file
2. Click **"Save as PNG"** button or use **File → Save as PNG** menu
3. Choose a destination and filename for the PNG export
4. The image will be converted and saved

## Documentation

Comprehensive technical documentation for each format is available in the [`docs/`](docs/) directory:

- **[Format Overview](docs/README.md)** - Quick reference and comparison
- **[ART Format](docs/ART.md)** - AOL Art format specification
- **[MAC Format](docs/MAC.md)** - MacPaint format specification
- **[PIC Format](docs/PIC.md)** - PICtor/PNTG format specification
- **[PCX Format](docs/PCX.md)** - PC Paintbrush format specification
- **[TIF Format](docs/TIF.md)** - TIFF format specification

Each document includes:
- File structure details
- Compression algorithms
- Decoding procedures
- Common challenges and solutions
- Historical context
- Implementation references

## Technical Details

### Custom Decoders

The application includes custom decoders for legacy formats:

#### ARTImageDecoder
- Handles various ART format variants
- Supports word-aligned scanline padding
- Multiple decompression algorithms
- Fallback detection for unknown variants

#### MACImageDecoder
- Decodes MacPaint files (576×720, 1-bit monochrome)
- PackBits compression support
- PNTG variant detection and handling
- 512-byte header processing

#### PICImageDecoder
- Dual-mode decoder (PICtor and PNTG)
- Format signature detection
- RLE and PackBits compression
- Palette handling and color scaling

#### PCXImageDecoder
- Full PCX specification support
- Monochrome, EGA, VGA, and true color
- Planar and packed pixel modes
- 16-color and 256-color palettes
- Scanline-based RLE decompression

#### TIFImageDecoder
- Uses PIL's native TIFF support
- Handles all standard TIFF variants
- Automatic color mode conversion
- Support for all TIFF compression types

### Compression Algorithms

- **PackBits RLE**: Used in .MAC and PNTG formats
- **PCX RLE**: Specialized run-length encoding for PCX
- **AOL RLE**: Variant used in some .ART files
- **PICtor RLE**: Simple RLE for PICtor format
- **TIFF compressions**: LZW, JPEG, ZIP, and more (via PIL)

## Project Structure

```
vintageimageviewe/
├── vintage_image_viewer.py    # Main application
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── CHANGELOG.md                # Version history
├── PROJECT_SUMMARY.md          # Project overview
├── docs/                       # Format documentation
│   ├── README.md               # Documentation index
│   ├── ART.md                  # AOL Art format spec
│   ├── MAC.md                  # MacPaint format spec
│   ├── PIC.md                  # PICtor/PNTG format spec
│   ├── PCX.md                  # PCX format spec
│   └── TIF.md                  # TIFF format spec
└── [sample files]              # Test images in various formats
```

## Notes

These are vintage file formats from the 1980s-1990s era, with the exception of TIFF which remains current. The decoder attempts to handle various format variants, but some exotic or corrupted files may not load properly.

### Format Challenges

- **Multiple variants**: Some extensions (.ART, .PIC) are used by incompatible formats
- **Misleading headers**: PNTG files contain incorrect dimension information
- **Scanline alignment**: Many formats use word-aligned scanlines with padding
- **Endianness**: Mac formats use big-endian, PC formats use little-endian
- **Color scaling**: Vintage palettes use 6-bit color requiring scaling to 8-bit

The decoders implement format detection cascades and fallback strategies to handle these challenges gracefully.

## Development

### Adding Format Support

To add support for a new format:

1. Create a new decoder class (e.g., `NewFormatDecoder`)
2. Implement the `decode(file_path)` static method
3. Add format detection in `open_file()` and `_load_file_by_index()`
4. Update file type filters
5. Update `_scan_directory()` supported extensions
6. Create format documentation in `docs/`
7. Update this README

### Testing

Test with various file variants:
- Minimum size images
- Maximum size images
- Different compression types
- Corrupted/truncated files
- Edge cases (non-zero origins, unusual dimensions)

## License

Free to use and modify.

## Acknowledgments

- Format specifications reverse-engineered from actual vintage files
- PackBits algorithm from Apple Technical Note TN1023
- PCX specification from ZSoft Technical Reference Manual
- TIFF support via Pillow library (PIL Fork)

---

*Last updated: 2025-11-04*
