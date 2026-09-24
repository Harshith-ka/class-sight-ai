from vision.detection.tiling import make_tiles


def test_make_tiles_covers_full_image():
    tiles = make_tiles(1000, 800)
    min_x1 = min(t[0] for t in tiles)
    min_y1 = min(t[1] for t in tiles)
    max_x2 = max(t[2] for t in tiles)
    max_y2 = max(t[3] for t in tiles)
    assert min_x1 == 0
    assert min_y1 == 0
    assert max_x2 == 1000
    assert max_y2 == 800


def test_make_tiles_count_matches_grid():
    tiles = make_tiles(1000, 800)
    assert len(tiles) == 4  # 2x2 grid


def test_make_tiles_adjacent_tiles_overlap():
    tiles = make_tiles(1000, 800)
    # First two tiles in a row should share some x-range (overlap), not butt exactly at the midpoint.
    left, right = tiles[0], tiles[1]
    assert right[0] < left[2]


def test_make_tiles_within_bounds():
    tiles = make_tiles(640, 480)
    for x1, y1, x2, y2 in tiles:
        assert 0 <= x1 < x2 <= 640
        assert 0 <= y1 < y2 <= 480
