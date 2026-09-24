import tempfile
from pathlib import Path

from ingest_external import convert_labels, find_source_pairs, load_class_names


def test_convert_labels_maps_and_renumbers_class():
    with tempfile.TemporaryDirectory() as tmp:
        label_path = Path(tmp) / "a.txt"
        label_path.write_text("1 0.5 0.5 0.2 0.3\n", encoding="utf-8")
        class_names = {0: "table", 1: "chair"}
        result = convert_labels(label_path, class_names, {"chair": "seat"})
        assert result == ["0 0.5 0.5 0.2 0.3"]


def test_convert_labels_drops_unmapped_classes():
    with tempfile.TemporaryDirectory() as tmp:
        label_path = Path(tmp) / "a.txt"
        label_path.write_text("0 0.5 0.5 0.2 0.3\n1 0.1 0.1 0.1 0.1\n", encoding="utf-8")
        class_names = {0: "table", 1: "chair"}
        # Only "chair" is mapped; "table" boxes should be dropped.
        result = convert_labels(label_path, class_names, {"chair": "seat"})
        assert result == ["0 0.1 0.1 0.1 0.1"]


def test_convert_labels_maps_multiple_target_classes():
    with tempfile.TemporaryDirectory() as tmp:
        label_path = Path(tmp) / "a.txt"
        label_path.write_text("0 0.2 0.2 0.1 0.1\n1 0.5 0.5 0.2 0.3\n", encoding="utf-8")
        class_names = {0: "teacher", 1: "chair"}
        result = convert_labels(label_path, class_names, {"teacher": "instructor", "chair": "seat"})
        assert result == ["1 0.2 0.2 0.1 0.1", "0 0.5 0.5 0.2 0.3"]


def test_convert_labels_missing_file_returns_empty():
    result = convert_labels(Path("does-not-exist.txt"), {0: "chair"}, {"chair": "seat"})
    assert result == []


def test_load_class_names_dict_format():
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp)
        (source_dir / "data.yaml").write_text("names:\n  0: table\n  1: chair\n", encoding="utf-8")
        assert load_class_names(source_dir) == {0: "table", 1: "chair"}


def test_load_class_names_list_format():
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp)
        (source_dir / "data.yaml").write_text("names: ['table', 'chair']\n", encoding="utf-8")
        assert load_class_names(source_dir) == {0: "table", 1: "chair"}


def test_find_source_pairs_flat_layout():
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp)
        (source_dir / "images").mkdir()
        (source_dir / "labels").mkdir()
        (source_dir / "images" / "a.jpg").write_bytes(b"fake")
        (source_dir / "labels" / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")

        pairs = find_source_pairs(source_dir)
        assert len(pairs) == 1
        assert pairs[0][0].name == "a.jpg"
        assert pairs[0][1].name == "a.txt"


def test_find_source_pairs_split_layout():
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = Path(tmp)
        (source_dir / "images" / "train").mkdir(parents=True)
        (source_dir / "labels" / "train").mkdir(parents=True)
        (source_dir / "images" / "train" / "a.jpg").write_bytes(b"fake")
        (source_dir / "labels" / "train" / "a.txt").write_text("0 0.5 0.5 0.1 0.1\n", encoding="utf-8")

        pairs = find_source_pairs(source_dir)
        assert len(pairs) == 1
        assert pairs[0][0].name == "a.jpg"
        assert pairs[0][1] == source_dir / "labels" / "train" / "a.txt"
