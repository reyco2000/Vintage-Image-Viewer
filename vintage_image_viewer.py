#!/usr/bin/env python3
"""
Vintage Image Viewer
Opens and displays .ART (AOL Legacy), .MAC (MacPaint), .PIC (PICtor), .PCX (PC Paintbrush), and .TIF (TIFF) image files
Allows saving as PNG format
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import struct
import os


class ARTImageDecoder:
    """Decoder for AOL .ART image format"""

    @staticmethod
    def decode(file_path):
        """
        Decode AOL ART format image
        ART files can be various formats - this handles the common AOL compressed format
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Check for ART header signatures
            if len(data) < 16:
                raise ValueError("File too small to be a valid ART file")

            # Try to detect ART format variant
            # Check for standard bitmap format (width at offset 2, height at offset 6)
            if data[0:2] == b'\x00\x00':
                # Try standard bitmap format
                width = struct.unpack('<H', data[2:4])[0]
                height = struct.unpack('<H', data[6:8])[0]

                # Validate dimensions
                if 1 <= width <= 4096 and 1 <= height <= 4096:
                    bytes_needed = (width * height + 7) // 8
                    if len(data) >= 16 + bytes_needed - 100:  # Allow some tolerance
                        return ARTImageDecoder._decode_bitmap_art(data, width, height)

            # Try other format variants
            if data[0:4] == b'ART\x00':
                return ARTImageDecoder._decode_aol_art(data)
            elif data[0:2] == b'\x01\x00':
                return ARTImageDecoder._decode_pfs_art(data)
            else:
                # Try generic bitmap interpretation
                return ARTImageDecoder._decode_generic_art(data)

        except Exception as e:
            raise ValueError(f"Failed to decode ART file: {str(e)}")

    @staticmethod
    def _decode_bitmap_art(data, width, height):
        """Decode standard bitmap ART format (1-bit per pixel with word-aligned scanlines)"""
        # Data starts at offset 16
        offset = 16

        # Calculate scanline width with 2-byte (word) alignment
        # Scanlines are padded to even byte boundaries
        bytes_per_line_unaligned = (width + 7) // 8
        bytes_per_line = ((bytes_per_line_unaligned + 1) // 2) * 2  # Round up to even

        # ART format quirk: image data starts 8 bytes before the end of each scanline
        # This causes a horizontal offset that needs to be corrected
        scanline_offset = bytes_per_line - 8

        pixels = []

        # Read each scanline with the correct offset
        for row in range(height):
            # Start reading from (scanline_offset) bytes into each scanline
            row_start = offset + row * bytes_per_line + scanline_offset

            # Read the actual width pixels
            for col in range(width):
                byte_idx = col // 8
                bit_idx = 7 - (col % 8)

                if row_start + byte_idx < len(data):
                    byte = data[row_start + byte_idx]
                    pixel = 255 if (byte >> bit_idx) & 1 else 0
                    pixels.append(pixel)
                else:
                    pixels.append(0)

        img = Image.new('L', (width, height))
        img.putdata(pixels)
        return img

    @staticmethod
    def _decode_aol_art(data):
        """Decode AOL-style ART format"""
        # Skip header
        offset = 4

        # Try to read dimensions (common location)
        if len(data) < offset + 8:
            raise ValueError("Invalid ART file structure")

        width = struct.unpack('<H', data[offset:offset+2])[0]
        height = struct.unpack('<H', data[offset+2:offset+4])[0]

        # Validate dimensions
        if width == 0 or height == 0 or width > 4096 or height > 4096:
            # Try alternative header parsing
            width, height = 640, 480  # Common default

        offset += 8

        # Decompress RLE-style data
        pixels = ARTImageDecoder._decompress_rle(data[offset:], width, height)

        # Create image from pixel data
        img = Image.new('L', (width, height))
        img.putdata(pixels)

        return img

    @staticmethod
    def _decode_pfs_art(data):
        """Decode PFS First Publisher ART format"""
        # PFS ART format structure
        offset = 2

        if len(data) < 10:
            raise ValueError("Invalid PFS ART file")

        # Try to extract dimensions
        width = struct.unpack('<H', data[2:4])[0] if len(data) >= 4 else 320
        height = struct.unpack('<H', data[4:6])[0] if len(data) >= 6 else 200

        # Validate and adjust if needed
        if width == 0 or height == 0 or width > 4096 or height > 4096:
            width, height = 320, 200

        offset = 10

        # Read bitmap data
        pixels = []
        for byte in data[offset:]:
            # Expand each bit to a pixel
            for bit in range(7, -1, -1):
                pixels.append(255 if (byte >> bit) & 1 else 0)
                if len(pixels) >= width * height:
                    break
            if len(pixels) >= width * height:
                break

        # Pad if needed
        while len(pixels) < width * height:
            pixels.append(0)

        img = Image.new('L', (width, height))
        img.putdata(pixels[:width * height])

        return img

    @staticmethod
    def _decode_generic_art(data):
        """Generic bitmap interpretation for unknown ART variants"""
        # Try common resolutions
        common_sizes = [
            (320, 200), (640, 480), (640, 350), (320, 240),
            (512, 384), (640, 400), (800, 600)
        ]

        for width, height in common_sizes:
            expected_size = width * height
            if len(data) >= expected_size:
                # Try interpreting as raw bitmap
                pixels = list(data[:expected_size])
                img = Image.new('L', (width, height))
                img.putdata(pixels)
                return img

        # Fallback: try to interpret as paletted data
        width = 320
        height = min(200, len(data) // width)
        pixels = list(data[:width * height])
        img = Image.new('L', (width, height))
        img.putdata(pixels)

        return img

    @staticmethod
    def _decompress_rle(data, width, height):
        """Decompress RLE (Run-Length Encoded) data"""
        pixels = []
        i = 0

        while i < len(data) and len(pixels) < width * height:
            if i + 1 < len(data):
                count = data[i]
                value = data[i + 1]

                # Check if this is a run or literal
                if count > 128:  # Run
                    run_length = count - 128
                    pixels.extend([value] * run_length)
                    i += 2
                elif count > 0:  # Literal
                    pixels.extend(data[i+1:i+1+count])
                    i += count + 1
                else:
                    i += 2
            else:
                pixels.append(data[i])
                i += 1

        # Pad if needed
        while len(pixels) < width * height:
            pixels.append(0)

        return pixels[:width * height]


class PICImageDecoder:
    """Decoder for PICtor .PIC image format and variants"""

    @staticmethod
    def decode(file_path):
        """
        Decode PIC format image
        Supports multiple .PIC format variants:
        - PICtor (PC Paint) format
        - PICT-style formats
        - Other PC graphics formats
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Check minimum file size
            if len(data) < 17:
                raise ValueError("File too small to be a valid PIC file")

            # Try to detect format variant
            # Check for PNTG/PICT signature (around offset 56-64)
            if b'PNTG' in data[:100] or b'PICT' in data[:100]:
                return PICImageDecoder._decode_pict_variant(data)

            # Check for standard PICtor magic bytes (0x1234 in little-endian)
            elif data[0] == 0x34 and data[1] == 0x12:
                return PICImageDecoder._decode_pictor_standard(data)

            # Try other common .PIC signatures
            else:
                # Try to decode as generic bitmap
                return PICImageDecoder._decode_generic_pic(data)

        except Exception as e:
            raise ValueError(f"Failed to decode PIC file: {str(e)}")

    @staticmethod
    def _decode_pict_variant(data):
        """Decode PICT-style or PNTG variant of PIC format"""
        # PNTG format structure:
        # 0x00-0x3F: Filename and padding (64 bytes)
        # 0x40: "PNTGMPNT" signature (8 bytes)
        # 0x48-0x4F: Version/flags (8 bytes)
        # 0x50-0x53: Width (4 bytes, little-endian)
        # 0x54-0x57: Height (4 bytes, little-endian)
        # 0x58-0x7F: Additional header data
        # 0x80-0x27F: Fill patterns (512 bytes, 64 patterns × 8 bytes)
        # 0x280+: RLE compressed image data

        # PNTG files often have misleading dimensions in the header
        # Use standard MacPaint dimensions (576x720) for better compatibility
        width = 576
        height = 720

        # Image data starts after fill patterns (typically at 0x280 = 640)
        # Fill patterns are at 0x80, 64 patterns of 8 bytes each = 512 bytes
        image_data_offset = 0x280

        if len(data) < image_data_offset:
            # If file doesn't have pattern data, try alternative offset
            image_data_offset = 0x80

        # Try PackBits decompression (same as MacPaint)
        # Note: MACImageDecoder is defined later in this file
        try:
            pixels = PICImageDecoder._decompress_packbits_for_pntg(data[image_data_offset:], width, height)

            # Create image
            img = Image.new('1', (width, height))
            img.putdata(pixels)
            img = img.convert('L')
            return img
        except:
            # Fallback to original RLE decoder
            pixels = PICImageDecoder._decode_pntg_rle(data[image_data_offset:], width, height)

            # Create image
            img = Image.new('L', (width, height))
            img.putdata(pixels[:width * height])
            return img

    @staticmethod
    def _decode_pictor_standard(data):
        """Decode standard PICtor format"""
        # Read header information
        width = struct.unpack('<H', data[2:4])[0]
        height = struct.unpack('<H', data[4:6])[0]

        # Validate dimensions
        if width == 0 or height == 0 or width > 4096 or height > 4096:
            raise ValueError(f"Invalid dimensions: {width}x{height}")

        # Read color depth and encoding info
        bits_per_pixel = data[6] if len(data) > 6 else 8
        offset = 17

        # Read palette if 8-bit image
        palette = None
        if bits_per_pixel == 8:
            if len(data) >= offset + 768:
                palette_data = data[offset:offset + 768]
                palette = []
                for i in range(0, 768, 3):
                    r = (palette_data[i] * 255) // 63
                    g = (palette_data[i + 1] * 255) // 63
                    b = (palette_data[i + 2] * 255) // 63
                    palette.extend([r, g, b])
                offset += 768

        # Read image data
        pixels = PICImageDecoder._decode_pic_data(data[offset:], width, height, bits_per_pixel)

        # Create image
        if bits_per_pixel == 8 and palette:
            img = Image.new('P', (width, height))
            img.putpalette(palette)
            img.putdata(pixels[:width * height])
            img = img.convert('RGB')
        elif bits_per_pixel == 1:
            img = Image.new('L', (width, height))
            img.putdata([255 if p else 0 for p in pixels[:width * height]])
        else:
            img = Image.new('L', (width, height))
            img.putdata(pixels[:width * height])

        return img

    @staticmethod
    def _decode_generic_pic(data):
        """Generic decoder for unknown .PIC variants"""
        # Try common resolutions
        common_sizes = [(640, 480), (320, 200), (640, 400), (800, 600), (512, 384)]

        for width, height in common_sizes:
            expected_size = width * height
            if len(data) >= expected_size + 256:
                pixels = PICImageDecoder._decode_pic_bitmap(data[256:], width, height)
                img = Image.new('L', (width, height))
                img.putdata(pixels[:width * height])
                return img

        # Fallback
        width = 320
        height = 200
        pixels = PICImageDecoder._decode_pic_bitmap(data[256:], width, height)
        img = Image.new('L', (width, height))
        img.putdata(pixels[:width * height])
        return img

    @staticmethod
    def _decompress_packbits_for_pntg(data, width, height):
        """Decompress PackBits compressed data for PNTG format (same as MacPaint)"""
        pixels = []
        bits = []
        i = 0

        while i < len(data) and len(bits) < width * height:
            if i >= len(data):
                break

            flag = data[i]

            if flag < 128:
                # Literal run: copy next (flag + 1) bytes
                count = flag + 1
                i += 1
                for j in range(count):
                    if i < len(data):
                        byte = data[i]
                        # Expand bits
                        for bit in range(7, -1, -1):
                            bits.append(1 if (byte >> bit) & 1 else 0)
                        i += 1
            elif flag > 128:
                # Repeat run: repeat next byte (257 - flag) times
                count = 257 - flag
                i += 1
                if i < len(data):
                    byte = data[i]
                    for _ in range(count):
                        # Expand bits
                        for bit in range(7, -1, -1):
                            bits.append(1 if (byte >> bit) & 1 else 0)
                    i += 1
            else:
                # flag == 128: no-op
                i += 1

        # Convert bits to pixels (0 = white, 1 = black)
        pixels = [255 if bit == 0 else 0 for bit in bits[:width * height]]

        # Pad if needed
        while len(pixels) < width * height:
            pixels.append(255)

        return pixels[:width * height]

    @staticmethod
    def _decode_pntg_rle(data, width, height):
        """Decode PNTG PackBits RLE compressed bitmap data

        Uses MacPaint PackBits compression scanline-by-scanline:
        - If control byte high bit = 1 (>= 128): Two's complement = repeat count, repeat next byte
        - If control byte high bit = 0 (< 128): Add 1 = literal count, copy next N bytes
        - 128 (0x80) is a no-op marker
        """
        bytes_per_line = (width + 7) // 8
        all_scanlines = []
        i = 0

        # Decode each scanline
        for row in range(height):
            scanline_bytes = []

            # Decode until we have a full scanline
            while len(scanline_bytes) < bytes_per_line and i < len(data):
                if i >= len(data):
                    break

                control_byte = data[i]
                i += 1

                if control_byte == 128:
                    # No-op marker, skip
                    continue
                elif control_byte > 128:
                    # Repeat run: two's complement gives repeat count
                    # In Python: 257 - control_byte (or: 256 - control_byte + 1)
                    count = 257 - control_byte
                    if i < len(data):
                        byte_val = data[i]
                        i += 1
                        for j in range(count):
                            if len(scanline_bytes) < bytes_per_line:
                                scanline_bytes.append(byte_val)
                else:
                    # Literal run: control_byte + 1 bytes follow
                    count = control_byte + 1
                    for j in range(count):
                        if i < len(data) and len(scanline_bytes) < bytes_per_line:
                            scanline_bytes.append(data[i])
                            i += 1

            # Pad scanline if needed
            while len(scanline_bytes) < bytes_per_line:
                scanline_bytes.append(0)

            all_scanlines.extend(scanline_bytes[:bytes_per_line])

        # Convert bytes to pixels
        pixels = []
        for byte_val in all_scanlines:
            for bit in range(7, -1, -1):
                pixel_value = 255 if (byte_val >> bit) & 1 else 0
                pixels.append(pixel_value)

        # Pad if needed
        target_pixels = width * height
        while len(pixels) < target_pixels:
            pixels.append(0)

        return pixels[:target_pixels]

    @staticmethod
    def _decode_pic_bitmap(data, width, height):
        """Decode bitmap data (1-bit per pixel)"""
        pixels = []
        target_pixels = width * height

        for byte in data:
            # Expand each bit to a pixel
            for bit in range(7, -1, -1):
                pixel_value = 255 if (byte >> bit) & 1 else 0
                pixels.append(pixel_value)
                if len(pixels) >= target_pixels:
                    break
            if len(pixels) >= target_pixels:
                break

        # Pad if needed
        while len(pixels) < target_pixels:
            pixels.append(0)

        return pixels[:target_pixels]

    @staticmethod
    def _decode_pic_data(data, width, height, bits_per_pixel):
        """Decode PICtor image data (may be RLE compressed)"""
        pixels = []
        i = 0

        # PICtor can use run-length encoding
        # Format: if byte has high bit set, it's a run count, next byte is the value
        # Otherwise, it's a literal pixel value

        target_pixels = width * height

        while i < len(data) and len(pixels) < target_pixels:
            if i >= len(data):
                break

            byte = data[i]

            # Check for RLE marker (0xC0 - 0xFF range often indicates run)
            if byte >= 0xC0:
                # Run-length encoded
                run_length = byte - 0xC0
                i += 1
                if i < len(data):
                    value = data[i]
                    pixels.extend([value] * run_length)
                    i += 1
            else:
                # Literal pixel
                pixels.append(byte)
                i += 1

        # If we don't have enough pixels, try treating rest as literal data
        if len(pixels) < target_pixels:
            remaining = target_pixels - len(pixels)
            if len(data) >= remaining:
                pixels.extend(data[:remaining])
            else:
                # Pad with black
                pixels.extend([0] * (target_pixels - len(pixels)))

        return pixels[:target_pixels]


class PCXImageDecoder:
    """Decoder for PCX (PC Paintbrush) image format"""

    @staticmethod
    def decode(file_path):
        """
        Decode PCX format image
        PCX is a common DOS-era image format with RLE compression
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Check minimum file size
            if len(data) < 128:
                raise ValueError("File too small to be a valid PCX file")

            # Check manufacturer byte (should be 0x0A)
            if data[0] != 0x0A:
                raise ValueError("Invalid PCX file signature")

            # Read header
            version = data[1]
            encoding = data[2]  # 1 = RLE
            bits_per_pixel = data[3]

            # Image dimensions
            xmin = struct.unpack('<H', data[4:6])[0]
            ymin = struct.unpack('<H', data[6:8])[0]
            xmax = struct.unpack('<H', data[8:10])[0]
            ymax = struct.unpack('<H', data[10:12])[0]

            width = xmax - xmin + 1
            height = ymax - ymin + 1

            # Validate dimensions
            if width <= 0 or height <= 0 or width > 4096 or height > 4096:
                raise ValueError(f"Invalid dimensions: {width}x{height}")

            # Number of color planes
            nplanes = data[65]
            bytes_per_line = struct.unpack('<H', data[66:68])[0]
            palette_type = struct.unpack('<H', data[68:70])[0]

            # Image data starts at offset 128
            image_data_offset = 128

            # Decode based on bits per pixel and planes
            if bits_per_pixel == 8 and nplanes == 1:
                # 256-color image
                pixels, palette = PCXImageDecoder._decode_8bit(
                    data, image_data_offset, width, height, bytes_per_line, encoding
                )

                if palette:
                    img = Image.new('P', (width, height))
                    img.putpalette(palette)
                    img.putdata(pixels)
                    img = img.convert('RGB')
                else:
                    img = Image.new('L', (width, height))
                    img.putdata(pixels)

            elif bits_per_pixel == 1 and nplanes == 1:
                # Monochrome
                pixels = PCXImageDecoder._decode_1bit(
                    data, image_data_offset, width, height, bytes_per_line, encoding
                )
                img = Image.new('L', (width, height))
                img.putdata(pixels)

            elif bits_per_pixel == 4 and nplanes == 1:
                # 16-color image
                pixels = PCXImageDecoder._decode_4bit(
                    data, image_data_offset, width, height, bytes_per_line, encoding, data[16:64]
                )
                img = Image.new('RGB', (width, height))
                img.putdata(pixels)

            elif bits_per_pixel == 1 and nplanes in [3, 4]:
                # 8-color or 16-color planar (EGA/VGA)
                # Extract palette from header (16 colors at offset 16-63)
                header_palette = data[16:64] if len(data) >= 64 else None
                pixels = PCXImageDecoder._decode_planar(
                    data, image_data_offset, width, height, bytes_per_line, nplanes, encoding, header_palette
                )
                img = Image.new('RGB', (width, height))
                img.putdata(pixels)

            else:
                raise ValueError(f"Unsupported PCX format: {bits_per_pixel} bpp, {nplanes} planes")

            return img

        except Exception as e:
            raise ValueError(f"Failed to decode PCX file: {str(e)}")

    @staticmethod
    def _decode_rle(data, offset, bytes_per_line, height, encoding):
        """Decode PCX RLE compressed data"""
        scanlines = []
        i = offset

        for row in range(height):
            scanline = []

            while len(scanline) < bytes_per_line and i < len(data):
                byte = data[i]
                i += 1

                if encoding == 1 and (byte & 0xC0) == 0xC0:
                    # RLE run: top 2 bits set
                    count = byte & 0x3F
                    if i < len(data):
                        value = data[i]
                        i += 1
                        scanline.extend([value] * count)
                else:
                    # Literal byte
                    scanline.append(byte)

            scanlines.append(scanline[:bytes_per_line])

        return scanlines

    @staticmethod
    def _decode_8bit(data, offset, width, height, bytes_per_line, encoding):
        """Decode 8-bit PCX image"""
        scanlines = PCXImageDecoder._decode_rle(data, offset, bytes_per_line, height, encoding)

        # Extract palette (at end of file)
        palette = None
        if len(data) >= 769 and data[-769] == 0x0C:
            # VGA palette
            palette_data = data[-768:]
            palette = []
            for i in range(0, 768, 3):
                palette.extend([palette_data[i], palette_data[i+1], palette_data[i+2]])

        # Convert scanlines to pixels
        pixels = []
        for scanline in scanlines:
            pixels.extend(scanline[:width])

        return pixels, palette

    @staticmethod
    def _decode_1bit(data, offset, width, height, bytes_per_line, encoding):
        """Decode 1-bit monochrome PCX image"""
        scanlines = PCXImageDecoder._decode_rle(data, offset, bytes_per_line, height, encoding)

        pixels = []
        for scanline in scanlines:
            for byte_val in scanline[:bytes_per_line]:
                for bit in range(7, -1, -1):
                    if len(pixels) % width < width:
                        pixel_value = 255 if (byte_val >> bit) & 1 else 0
                        pixels.append(pixel_value)

        return pixels[:width * height]

    @staticmethod
    def _decode_4bit(data, offset, width, height, bytes_per_line, encoding, header_palette):
        """Decode 4-bit PCX image"""
        scanlines = PCXImageDecoder._decode_rle(data, offset, bytes_per_line, height, encoding)

        # Build palette from header
        palette = []
        for i in range(0, 48, 3):
            palette.append((header_palette[i], header_palette[i+1], header_palette[i+2]))

        pixels = []
        for scanline in scanlines:
            for byte_val in scanline[:bytes_per_line]:
                # Two pixels per byte
                if len(pixels) < width * height:
                    px1 = (byte_val >> 4) & 0x0F
                    pixels.append(palette[px1] if px1 < len(palette) else (0, 0, 0))
                if len(pixels) < width * height:
                    px2 = byte_val & 0x0F
                    pixels.append(palette[px2] if px2 < len(palette) else (0, 0, 0))

        return pixels[:width * height]

    @staticmethod
    def _decode_planar(data, offset, width, height, bytes_per_line, nplanes, encoding, header_palette=None):
        """Decode planar PCX image (EGA/VGA 16-color or RGB)"""
        scanlines = PCXImageDecoder._decode_rle(data, offset, bytes_per_line * nplanes, height, encoding)

        # Build palette from header if provided, otherwise use default EGA palette
        if header_palette and len(header_palette) >= 48:
            # Parse 16 RGB triplets from header palette (bytes 16-63)
            palette = []
            for i in range(0, 48, 3):
                palette.append((header_palette[i], header_palette[i+1], header_palette[i+2]))
        else:
            # EGA default palette (16 colors)
            palette = [
                (0, 0, 0),       # Black
                (0, 0, 170),     # Blue
                (0, 170, 0),     # Green
                (0, 170, 170),   # Cyan
                (170, 0, 0),     # Red
                (170, 0, 170),   # Magenta
                (170, 85, 0),    # Brown
                (170, 170, 170), # Light Gray
                (85, 85, 85),    # Dark Gray
                (85, 85, 255),   # Light Blue
                (85, 255, 85),   # Light Green
                (85, 255, 255),  # Light Cyan
                (255, 85, 85),   # Light Red
                (255, 85, 255),  # Light Magenta
                (255, 255, 85),  # Yellow
                (255, 255, 255), # White
            ]

        pixels = []
        for scanline in scanlines:
            # Split into planes
            planes = []
            for p in range(nplanes):
                plane_start = p * bytes_per_line
                planes.append(scanline[plane_start:plane_start + bytes_per_line])

            # Combine planes into pixels - only extract 'width' pixels per scanline
            pixels_in_row = 0
            for byte_idx in range(bytes_per_line):
                for bit in range(7, -1, -1):
                    if pixels_in_row < width:  # Only process up to width pixels per scanline
                        if nplanes == 4:
                            # 16-color EGA: 4 bitplanes
                            # Extract bit from each plane
                            bit0 = (planes[0][byte_idx] >> bit) & 1
                            bit1 = (planes[1][byte_idx] >> bit) & 1
                            bit2 = (planes[2][byte_idx] >> bit) & 1
                            bit3 = (planes[3][byte_idx] >> bit) & 1

                            # Calculate color index from 4 bits
                            color_idx = (bit3 << 3) | (bit2 << 2) | (bit1 << 1) | bit0
                            pixels.append(palette[color_idx])
                        else:
                            # 3-plane RGB
                            r = 255 if (planes[0][byte_idx] >> bit) & 1 else 0
                            g = 255 if (nplanes > 1 and (planes[1][byte_idx] >> bit) & 1) else 0
                            b = 255 if (nplanes > 2 and (planes[2][byte_idx] >> bit) & 1) else 0
                            pixels.append((r, g, b))
                        pixels_in_row += 1

        return pixels[:width * height]


class MACImageDecoder:
    """Decoder for MacPaint .MAC image format"""

    @staticmethod
    def decode(file_path):
        """
        Decode MacPaint MAC format image
        MacPaint images are 576x720 pixels, 1-bit monochrome
        Also handles PNTG variant files with .MAC extension
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            # Check for PNTG variant (some .MAC files use this format)
            if b'PNTG' in data[:100]:
                # PNTG .MAC files use standard MacPaint dimensions (576x720)
                # but with PNTG-style compression starting at offset 0x280
                width = 576
                height = 720
                offset = 0x280  # Data starts after pattern table

                # Use PackBits decompression from this offset
                pixels = MACImageDecoder._decompress_packbits(data[offset:], width, height)

                # Create image
                img = Image.new('1', (width, height))
                img.putdata(pixels)
                img = img.convert('L')
                return img

            # MacPaint file structure:
            # - 512 bytes header (often empty or contains patterns)
            # - Image data (compressed or uncompressed)

            # Standard MacPaint dimensions
            width = 576
            height = 720

            # Skip header (512 bytes)
            offset = 512 if len(data) > 512 else 0

            # Check if data is compressed (PackBits)
            if offset < len(data) and data[offset] > 128:
                # Likely compressed
                pixels = MACImageDecoder._decompress_packbits(data[offset:], width, height)
            else:
                # Uncompressed bitmap
                pixels = MACImageDecoder._decode_bitmap(data[offset:], width, height)

            # Create image
            img = Image.new('1', (width, height))
            img.putdata(pixels)

            # Convert to grayscale for better display
            img = img.convert('L')

            return img

        except Exception as e:
            raise ValueError(f"Failed to decode MAC file: {str(e)}")

    @staticmethod
    def _decompress_packbits(data, width, height):
        """Decompress PackBits compressed data (used in MacPaint)"""
        pixels = []
        bits = []
        i = 0

        while i < len(data) and len(bits) < width * height:
            if i >= len(data):
                break

            flag = data[i]

            if flag < 128:
                # Literal run: copy next (flag + 1) bytes
                count = flag + 1
                i += 1
                for j in range(count):
                    if i < len(data):
                        byte = data[i]
                        # Expand bits
                        for bit in range(7, -1, -1):
                            bits.append(1 if (byte >> bit) & 1 else 0)
                        i += 1
            elif flag > 128:
                # Repeat run: repeat next byte (257 - flag) times
                count = 257 - flag
                i += 1
                if i < len(data):
                    byte = data[i]
                    for _ in range(count):
                        # Expand bits
                        for bit in range(7, -1, -1):
                            bits.append(1 if (byte >> bit) & 1 else 0)
                    i += 1
            else:
                # flag == 128: no-op
                i += 1

        # Convert bits to pixels (0 = white, 1 = black)
        pixels = [255 if bit == 0 else 0 for bit in bits[:width * height]]

        # Pad if needed
        while len(pixels) < width * height:
            pixels.append(255)

        return pixels[:width * height]

    @staticmethod
    def _decode_bitmap(data, width, height):
        """Decode uncompressed bitmap data"""
        pixels = []

        for byte in data:
            # Expand each bit to a pixel
            for bit in range(7, -1, -1):
                pixel_value = 255 if (byte >> bit) & 1 == 0 else 0
                pixels.append(pixel_value)
                if len(pixels) >= width * height:
                    break
            if len(pixels) >= width * height:
                break

        # Pad if needed
        while len(pixels) < width * height:
            pixels.append(255)

        return pixels[:width * height]


class TIFImageDecoder:
    """Decoder for TIFF .TIF/.TIFF image format"""

    @staticmethod
    def decode(file_path):
        """
        Decode TIFF format image
        TIFF is well-supported by PIL, so we use native support
        """
        try:
            # Use PIL's native TIFF support
            img = Image.open(file_path)

            # Convert to RGB if needed for consistent display
            if img.mode in ('RGBA', 'P', 'LA'):
                img = img.convert('RGB')
            elif img.mode not in ('RGB', 'L', '1'):
                # Convert any other modes to RGB
                img = img.convert('RGB')

            return img

        except Exception as e:
            raise ValueError(f"Failed to decode TIF file: {str(e)}")


class VintageImageViewer:
    """Main GUI application for viewing vintage image formats"""

    def __init__(self, root):
        self.root = root
        self.root.title("Vintage Image Viewer - .ART, .MAC, .PIC, .PCX & .TIF")
        self.root.geometry("900x700")

        self.current_image = None
        self.current_image_pil = None
        self.current_file_path = None

        # Navigation state
        self.directory_files = []  # List of all supported images in current directory
        self.current_file_index = -1  # Index of current file in directory_files

        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface"""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Image...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save as PNG", command=self.save_as_png, state=tk.DISABLED)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        self.file_menu = file_menu

        # Toolbar
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Open Image", command=self.open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save as PNG", command=self.save_as_png, state=tk.DISABLED).pack(side=tk.LEFT, padx=2)

        # Navigation buttons (initially disabled)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        self.prev_button = ttk.Button(toolbar, text="◄ Previous", command=self.previous_image, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT, padx=2)
        self.next_button = ttk.Button(toolbar, text="Next ►", command=self.next_image, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT, padx=2)

        self.save_button = toolbar.winfo_children()[1]

        # Info label
        self.info_label = ttk.Label(self.root, text="Open a .ART, .MAC, .PIC, .PCX, or .TIF file to begin", relief=tk.SUNKEN, anchor=tk.W)
        self.info_label.pack(side=tk.BOTTOM, fill=tk.X)

        # Canvas for image display with scrollbars
        canvas_frame = ttk.Frame(self.root)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL)

        self.canvas = tk.Canvas(canvas_frame, bg='#2b2b2b',
                               xscrollcommand=h_scrollbar.set,
                               yscrollcommand=v_scrollbar.set)

        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Keyboard shortcuts for navigation
        self.root.bind('<Left>', lambda e: self.previous_image())
        self.root.bind('<Right>', lambda e: self.next_image())

    def open_file(self):
        """Open and display an image file"""
        filetypes = [
            ("All Supported Images", "*.art *.mac *.pic *.pcx *.tif *.tiff"),
            ("AOL ART files", "*.art"),
            ("MacPaint files", "*.mac"),
            ("PICtor files", "*.pic"),
            ("PCX files", "*.pcx"),
            ("TIFF files", "*.tif *.tiff"),
            ("All files", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            title="Open Vintage Image File",
            filetypes=filetypes
        )

        if not file_path:
            return

        try:
            # Auto-detect file format based on extension
            file_ext = os.path.splitext(file_path)[1].lower()

            # Decode the image based on extension
            if file_ext == '.art':
                img = ARTImageDecoder.decode(file_path)
                file_type = 'ART'
            elif file_ext == '.mac':
                img = MACImageDecoder.decode(file_path)
                file_type = 'MAC'
            elif file_ext == '.pic':
                img = PICImageDecoder.decode(file_path)
                file_type = 'PIC'
            elif file_ext == '.pcx':
                img = PCXImageDecoder.decode(file_path)
                file_type = 'PCX'
            elif file_ext in ['.tif', '.tiff']:
                img = TIFImageDecoder.decode(file_path)
                file_type = 'TIFF'
            else:
                # Try to auto-detect by attempting each decoder
                try:
                    img = PCXImageDecoder.decode(file_path)
                    file_type = 'PCX'
                except:
                    try:
                        img = ARTImageDecoder.decode(file_path)
                        file_type = 'ART'
                    except:
                        try:
                            img = MACImageDecoder.decode(file_path)
                            file_type = 'MAC'
                        except:
                            img = PICImageDecoder.decode(file_path)
                            file_type = 'PIC'

            self.current_image_pil = img
            self.current_file_path = file_path

            # Display the image
            self._display_image(img)

            # Scan directory for other supported images
            self._scan_directory(file_path)

            # Update info
            file_name = os.path.basename(file_path)
            nav_info = f" ({self.current_file_index + 1}/{len(self.directory_files)})" if len(self.directory_files) > 1 else ""
            self.info_label.config(
                text=f"Loaded: {file_name}{nav_info} | Size: {img.width}x{img.height} | Format: {file_type}"
            )

            # Enable save button
            self.file_menu.entryconfig("Save as PNG", state=tk.NORMAL)
            self.save_button.config(state=tk.NORMAL)

            # Update navigation buttons
            self._update_navigation_buttons()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")

    def _display_image(self, pil_image):
        """Display PIL image on canvas"""
        # Convert PIL image to PhotoImage
        self.current_image = ImageTk.PhotoImage(pil_image)

        # Clear canvas
        self.canvas.delete("all")

        # Update canvas scroll region
        self.canvas.config(scrollregion=(0, 0, pil_image.width, pil_image.height))

        # Display image
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)

    def save_as_png(self):
        """Save current image as PNG"""
        if self.current_image_pil is None:
            messagebox.showwarning("No Image", "No image loaded to save")
            return

        # Get save file path
        file_path = filedialog.asksaveasfilename(
            title="Save as PNG",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            # Convert to RGB if needed for better PNG compatibility
            if self.current_image_pil.mode in ('1', 'L'):
                img_to_save = self.current_image_pil.convert('RGB')
            else:
                img_to_save = self.current_image_pil

            # Save as PNG
            img_to_save.save(file_path, 'PNG')

            messagebox.showinfo("Success", f"Image saved successfully to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{str(e)}")

    def _scan_directory(self, file_path):
        """Scan directory for all supported image files"""
        directory = os.path.dirname(file_path)
        if not directory:
            directory = '.'

        # Supported extensions
        supported_exts = {'.art', '.mac', '.pic', '.pcx', '.tif', '.tiff'}

        # Get all files in directory with supported extensions
        all_files = []
        try:
            for filename in os.listdir(directory):
                file_ext = os.path.splitext(filename)[1].lower()
                if file_ext in supported_exts:
                    full_path = os.path.join(directory, filename)
                    all_files.append(full_path)
        except Exception:
            # If we can't read directory, just use current file
            all_files = [file_path]

        # Sort files alphabetically
        all_files.sort()

        # Store the list and find current file index
        self.directory_files = all_files
        try:
            self.current_file_index = all_files.index(file_path)
        except ValueError:
            self.current_file_index = 0

    def _update_navigation_buttons(self):
        """Update navigation button states based on current position"""
        if len(self.directory_files) <= 1:
            # No other files, disable both buttons
            self.prev_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)
        else:
            # Enable/disable based on position
            if self.current_file_index > 0:
                self.prev_button.config(state=tk.NORMAL)
            else:
                self.prev_button.config(state=tk.DISABLED)

            if self.current_file_index < len(self.directory_files) - 1:
                self.next_button.config(state=tk.NORMAL)
            else:
                self.next_button.config(state=tk.DISABLED)

    def previous_image(self):
        """Load the previous image in the directory"""
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self._load_file_by_index(self.current_file_index)

    def next_image(self):
        """Load the next image in the directory"""
        if self.current_file_index < len(self.directory_files) - 1:
            self.current_file_index += 1
            self._load_file_by_index(self.current_file_index)

    def _load_file_by_index(self, index):
        """Load a file from the directory list by index"""
        if 0 <= index < len(self.directory_files):
            file_path = self.directory_files[index]

            try:
                # Auto-detect file format based on extension
                file_ext = os.path.splitext(file_path)[1].lower()

                # Decode the image based on extension
                if file_ext == '.art':
                    img = ARTImageDecoder.decode(file_path)
                    file_type = 'ART'
                elif file_ext == '.mac':
                    img = MACImageDecoder.decode(file_path)
                    file_type = 'MAC'
                elif file_ext == '.pic':
                    img = PICImageDecoder.decode(file_path)
                    file_type = 'PIC'
                elif file_ext == '.pcx':
                    img = PCXImageDecoder.decode(file_path)
                    file_type = 'PCX'
                elif file_ext in ['.tif', '.tiff']:
                    img = TIFImageDecoder.decode(file_path)
                    file_type = 'TIFF'
                else:
                    # Try to auto-detect
                    try:
                        img = PCXImageDecoder.decode(file_path)
                        file_type = 'PCX'
                    except:
                        try:
                            img = ARTImageDecoder.decode(file_path)
                            file_type = 'ART'
                        except:
                            try:
                                img = MACImageDecoder.decode(file_path)
                                file_type = 'MAC'
                            except:
                                img = PICImageDecoder.decode(file_path)
                                file_type = 'PIC'

                self.current_image_pil = img
                self.current_file_path = file_path

                # Display the image
                self._display_image(img)

                # Update info
                file_name = os.path.basename(file_path)
                nav_info = f" ({self.current_file_index + 1}/{len(self.directory_files)})"
                self.info_label.config(
                    text=f"Loaded: {file_name}{nav_info} | Size: {img.width}x{img.height} | Format: {file_type}"
                )

                # Update navigation buttons
                self._update_navigation_buttons()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to open file:\n{str(e)}")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = VintageImageViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
