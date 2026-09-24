"""Convert an external YOLO-format dataset into our ml/training_data/ schema
(class 0 = seat, class 1 = instructor) — spec section 41 "Dataset Class
Normalization".

Classes not covered by the mapping are dropped from converted labels;
images with zero surviving boxes are skipped entirely (an all-dropped-class
image adds nothing and would incorrectly teach the model "no seats here" on
a photo that might actually contain some).

Requires the source to have `images/` (flat, or split into
`images/<train|val|test>/`) and a matching `labels/` layout, plus a
`data.yaml` with a `names` section mapping class id -> class name.

IMPORTANT — vet the source images before running this for real: an external
dataset can share a class *name* (e.g. "chair") while containing completely
different visual content than our problem (isolated product photos on a
white background vs. small/occluded seats in a real classroom scene). Look
at a sample of images first; a class-name match alone doesn't mean the data
will help — see ml/README.md for a documented example of a rejected source.

Usage:
    python ingest_external.py /path/to/source --map chair=seat teacher=instructor
    python ingest_external.py /path/to/source --map chair=seat --dry-run
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from dataset import IMAGE_EXTENSIONS

DEST_DIR = Path(__file__).resolve().parents[1] / "training_data"
OUR_CLASS_IDS = {"seat": 0, "instructor": 1}


def load_class_names(source_dir: Path) -> dict[int, str]:
    data_yaml = source_dir / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"{data_yaml} not found — can't resolve class ids without it.")
    data = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    names = data.get("names")
    if isinstance(names, dict):
        return {int(k): v for k, v in names.items()}
    if isinstance(names, list):
        return dict(enumerate(names))
    raise SystemExit(f"Unrecognized 'names' format in {data_yaml}.")


def find_source_pairs(source_dir: Path) -> list[tuple[Path, Path]]:
    """Handles both a flat images/labels layout and a split
    images/<split>/labels/<split> layout (common in Roboflow/Kaggle exports)."""
    images_root = source_dir / "images"
    labels_root = source_dir / "labels"
    if not images_root.exists():
        return []

    direct_images = sorted(p for p in images_root.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS)
    if direct_images:
        return [(image_path, labels_root / f"{image_path.stem}.txt") for image_path in direct_images]

    pairs: list[tuple[Path, Path]] = []
    for split_dir in sorted(p for p in images_root.iterdir() if p.is_dir()):
        for image_path in sorted(split_dir.iterdir()):
            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            pairs.append((image_path, labels_root / split_dir.name / f"{image_path.stem}.txt"))
    return pairs


def convert_labels(label_path: Path, class_names: dict[int, str], class_map: dict[str, str]) -> list[str]:
    if not label_path.exists():
        return []
    converted = []
    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            continue
        class_id_str, cx, cy, w, h = parts
        source_name = class_names.get(int(class_id_str)) if class_id_str.lstrip("-").isdigit() else None
        target_name = class_map.get(source_name) if source_name else None
        if target_name not in OUR_CLASS_IDS:
            continue
        converted.append(f"{OUR_CLASS_IDS[target_name]} {cx} {cy} {w} {h}")
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source_dir", type=Path)
    parser.add_argument(
        "--map", nargs="+", required=True,
        help="source_class_name=our_class_name pairs, e.g. chair=seat teacher=instructor. "
             "Source classes not listed are dropped.",
    )
    parser.add_argument("--prefix", default="ext", help="Prefix for copied filenames to avoid collisions")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    class_map = dict(pair.split("=", 1) for pair in args.map)
    for target in class_map.values():
        if target not in OUR_CLASS_IDS:
            raise SystemExit(f"Unknown target class '{target}' — must be one of {list(OUR_CLASS_IDS)}.")

    class_names = load_class_names(args.source_dir)
    pairs = find_source_pairs(args.source_dir)
    print(f"Found {len(pairs)} source images. Class map: {class_map}")

    (DEST_DIR / "images").mkdir(parents=True, exist_ok=True)
    (DEST_DIR / "labels").mkdir(parents=True, exist_ok=True)

    copied = 0
    skipped_no_boxes = 0
    for image_path, label_path in pairs:
        converted = convert_labels(label_path, class_names, class_map)
        if not converted:
            skipped_no_boxes += 1
            continue

        dest_stem = f"{args.prefix}_{image_path.stem}"
        if not args.dry_run:
            shutil.copy2(image_path, DEST_DIR / "images" / f"{dest_stem}{image_path.suffix.lower()}")
            (DEST_DIR / "labels" / f"{dest_stem}.txt").write_text("\n".join(converted) + "\n", encoding="utf-8")
        copied += 1

    print(
        f"{'Would copy' if args.dry_run else 'Copied'} {copied} images with usable labels "
        f"({skipped_no_boxes} skipped — no boxes survived the class mapping)."
    )


if __name__ == "__main__":
    main()
