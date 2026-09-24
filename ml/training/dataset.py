"""Dataset validation and train/val split helpers for the exported YOLO
training data (see backend/app/services/export.py for how samples get
written to ml/training_data/ every time someone clicks "Export Training
Data" in the app).

Kept dependency-free (no ultralytics/torch import) so it's fast to unit
test and can validate a dataset without pulling in the heavy training stack.
"""
from __future__ import annotations

import random
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
# Keep in sync with backend/app/services/export.py CLASS_NAMES.
NUM_CLASSES = 2  # 0=seat, 1=instructor


def find_image_label_pairs(dataset_dir: Path) -> list[tuple[Path, Path]]:
    images_dir = dataset_dir / "images"
    if not images_dir.exists():
        return []
    labels_dir = dataset_dir / "labels"
    pairs = []
    for image_path in sorted(images_dir.iterdir()):
        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        pairs.append((image_path, labels_dir / f"{image_path.stem}.txt"))
    return pairs


def validate_dataset(dataset_dir: Path) -> list[str]:
    """Returns a list of human-readable issues; empty means the dataset is
    structurally sound (doesn't guarantee label *accuracy*, just format)."""
    issues: list[str] = []
    pairs = find_image_label_pairs(dataset_dir)
    if not pairs:
        issues.append(f"No images found in {dataset_dir / 'images'}.")
        return issues

    for image_path, label_path in pairs:
        if not label_path.exists():
            issues.append(f"{image_path.name}: missing label file {label_path.name}.")
            continue
        for line_no, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            issues.extend(_validate_label_line(label_path.name, line_no, line))

    labels_dir = dataset_dir / "labels"
    if labels_dir.exists():
        image_stems = {image_path.stem for image_path, _ in pairs}
        for label_path in labels_dir.glob("*.txt"):
            if label_path.stem not in image_stems:
                issues.append(f"{label_path.name}: no matching image found (orphan label).")

    return issues


def _validate_label_line(label_filename: str, line_no: int, line: str) -> list[str]:
    issues: list[str] = []
    parts = line.split()
    if len(parts) != 5:
        return [f"{label_filename}:{line_no}: expected 5 fields (class cx cy w h), got {len(parts)}."]

    class_id_str, *coords = parts
    if not class_id_str.isdigit() or int(class_id_str) >= NUM_CLASSES:
        issues.append(f"{label_filename}:{line_no}: invalid class id '{class_id_str}'.")

    for coord in coords:
        try:
            value = float(coord)
        except ValueError:
            issues.append(f"{label_filename}:{line_no}: non-numeric coordinate '{coord}'.")
            continue
        if not (0.0 <= value <= 1.0):
            issues.append(f"{label_filename}:{line_no}: coordinate {value} out of [0,1] range.")
    return issues


def split_dataset(
    dataset_dir: Path, val_fraction: float = 0.15, seed: int = 42
) -> tuple[list[Path], list[Path]]:
    images = [image_path for image_path, _ in find_image_label_pairs(dataset_dir)]
    shuffled = images[:]
    random.Random(seed).shuffle(shuffled)

    val_count = max(1, round(len(shuffled) * val_fraction)) if len(shuffled) > 1 else 0
    val_images = shuffled[:val_count]
    train_images = shuffled[val_count:]
    return train_images, val_images


def write_split_files(dataset_dir: Path, train_images: list[Path], val_images: list[Path]) -> Path:
    """Writes train/val image lists plus a data.yaml pointing at them.
    Falls back to validating against the training set itself when there
    aren't enough images for a separate holdout (better than crashing)."""
    splits_dir = dataset_dir / "splits"
    splits_dir.mkdir(exist_ok=True)

    train_txt = splits_dir / "train.txt"
    val_txt = splits_dir / "val.txt"
    effective_val = val_images or train_images
    train_txt.write_text("\n".join(str(p.resolve()) for p in train_images) + "\n", encoding="utf-8")
    val_txt.write_text("\n".join(str(p.resolve()) for p in effective_val) + "\n", encoding="utf-8")

    data_yaml = splits_dir / "data.yaml"
    data_yaml.write_text(
        f"train: {train_txt.resolve()}\nval: {val_txt.resolve()}\nnames:\n  0: seat\n  1: instructor\n",
        encoding="utf-8",
    )
    return data_yaml
