from pathlib import Path

from dataset import find_image_label_pairs, split_dataset, validate_dataset, write_split_files


def _make_dataset(tmp_path: Path, samples: dict[str, str | None]) -> Path:
    """samples: {image_stem: label_content_or_None (None = no label file written)}"""
    dataset_dir = tmp_path / "training_data"
    (dataset_dir / "images").mkdir(parents=True)
    (dataset_dir / "labels").mkdir(parents=True)
    for stem, label_content in samples.items():
        (dataset_dir / "images" / f"{stem}.jpg").write_bytes(b"fake-jpeg-bytes")
        if label_content is not None:
            (dataset_dir / "labels" / f"{stem}.txt").write_text(label_content, encoding="utf-8")
    return dataset_dir


def test_validate_dataset_clean_passes():
    def _run(tmp_path):
        dataset_dir = _make_dataset(tmp_path, {"a": "0 0.5 0.5 0.2 0.3\n1 0.1 0.1 0.05 0.1\n"})
        return validate_dataset(dataset_dir)

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        assert _run(Path(tmp)) == []


def test_validate_dataset_flags_missing_label():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"a": None})
        issues = validate_dataset(dataset_dir)
        assert any("missing label" in issue for issue in issues)


def test_validate_dataset_flags_bad_class_id():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"a": "5 0.5 0.5 0.2 0.3\n"})
        issues = validate_dataset(dataset_dir)
        assert any("invalid class id" in issue for issue in issues)


def test_validate_dataset_flags_out_of_range_coordinate():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"a": "0 1.5 0.5 0.2 0.3\n"})
        issues = validate_dataset(dataset_dir)
        assert any("out of [0,1] range" in issue for issue in issues)


def test_validate_dataset_flags_wrong_field_count():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"a": "0 0.5 0.5\n"})
        issues = validate_dataset(dataset_dir)
        assert any("expected 5 fields" in issue for issue in issues)


def test_validate_dataset_empty_directory_flagged():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = Path(tmp) / "training_data"
        (dataset_dir / "images").mkdir(parents=True)
        issues = validate_dataset(dataset_dir)
        assert any("No images found" in issue for issue in issues)


def test_find_image_label_pairs_counts_images():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"a": "0 0.5 0.5 0.2 0.3\n", "b": "0 0.5 0.5 0.2 0.3\n"})
        pairs = find_image_label_pairs(dataset_dir)
        assert len(pairs) == 2


def test_split_dataset_respects_val_fraction():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        samples = {f"img{i}": "0 0.5 0.5 0.2 0.3\n" for i in range(20)}
        dataset_dir = _make_dataset(Path(tmp), samples)
        train, val = split_dataset(dataset_dir, val_fraction=0.2)
        assert len(train) + len(val) == 20
        assert 3 <= len(val) <= 5  # ~20% of 20, with rounding


def test_split_dataset_tiny_dataset_has_no_val_holdout():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"only": "0 0.5 0.5 0.2 0.3\n"})
        train, val = split_dataset(dataset_dir, val_fraction=0.15)
        assert len(train) == 1
        assert len(val) == 0


def test_write_split_files_falls_back_to_train_for_val_when_empty():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        dataset_dir = _make_dataset(Path(tmp), {"only": "0 0.5 0.5 0.2 0.3\n"})
        train, val = split_dataset(dataset_dir, val_fraction=0.15)
        data_yaml = write_split_files(dataset_dir, train, val)

        assert data_yaml.exists()
        val_txt = (dataset_dir / "splits" / "val.txt").read_text(encoding="utf-8")
        train_txt = (dataset_dir / "splits" / "train.txt").read_text(encoding="utf-8")
        assert val_txt.strip() == train_txt.strip()  # val falls back to the same single image


def test_write_split_files_generates_valid_yaml_content():
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        samples = {f"img{i}": "0 0.5 0.5 0.2 0.3\n" for i in range(5)}
        dataset_dir = _make_dataset(Path(tmp), samples)
        train, val = split_dataset(dataset_dir, val_fraction=0.2)
        data_yaml = write_split_files(dataset_dir, train, val)

        content = data_yaml.read_text(encoding="utf-8")
        assert "train:" in content
        assert "val:" in content
        assert "0: seat" in content
        assert "1: instructor" in content
