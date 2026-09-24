"""Tile geometry for sliced inference.

Running YOLO once on a downscaled full image shrinks small, distant objects
below what the detector can reliably classify — a chair 20px tall in a
1280-wide classroom photo carries almost no visual signal. Splitting the
image into overlapping tiles and running detection on each tile at its own
resolution recovers that detail (a technique often called "slicing aided
hyper inference"), at the cost of extra forward passes per image.
"""
from __future__ import annotations

TILE_GRID = (2, 2)  # (rows, cols)
TILE_OVERLAP_FRACTION = 0.15  # overlap as a fraction of tile size, so objects near a seam still land whole in at least one tile


def make_tiles(width: int, height: int) -> list[tuple[int, int, int, int]]:
    """Pixel-space (x1, y1, x2, y2) regions covering the image with overlap."""
    rows, cols = TILE_GRID
    tile_w = width / cols
    tile_h = height / rows
    overlap_w = tile_w * TILE_OVERLAP_FRACTION
    overlap_h = tile_h * TILE_OVERLAP_FRACTION

    tiles = []
    for row in range(rows):
        for col in range(cols):
            x1 = max(0, int(col * tile_w - overlap_w))
            y1 = max(0, int(row * tile_h - overlap_h))
            x2 = min(width, int((col + 1) * tile_w + overlap_w))
            y2 = min(height, int((row + 1) * tile_h + overlap_h))
            tiles.append((x1, y1, x2, y2))
    return tiles
