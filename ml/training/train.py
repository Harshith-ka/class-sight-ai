"""Fine-tune the classroom seat/instructor detector (Phase 3 bridge).

Run after exporting enough corrected samples via the app's "Export Training
Data" button (backend/app/services/export.py writes to ../training_data/).

Realistic expectations: transfer learning from COCO weights can show a
useful signal with as few as ~30-50 diverse images, but the product spec's
500-1,500 image target is what it would take to reliably beat the current
heuristic pipeline (tiled inference + desk-based seat inference) across
varied classrooms. Below MIN_RECOMMENDED_IMAGES this refuses to run
without --force, so an accidental tiny-dataset run doesn't produce a
checkpoint that looks trained but isn't actually useful.

Usage:
    python train.py --dry-run          # validate the dataset, no training
    python train.py                    # fine-tune yolov8s.pt on ml/training_data/
    python train.py --force            # train even below the recommended size
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dataset import find_image_label_pairs, split_dataset, validate_dataset, write_split_files

DATASET_DIR = Path(__file__).resolve().parents[1] / "training_data"
RUNS_DIR = Path(__file__).resolve().parent / "runs"
MIN_RECOMMENDED_IMAGES = 30


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--weights", default="yolov8s.pt", help="Base checkpoint to fine-tune from")
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--imgsz", type=int, default=1280, help="Should match vision/detection/detector.py's imgsz")
    parser.add_argument("--val-fraction", type=float, default=0.15)
    parser.add_argument("--dry-run", action="store_true", help="Validate + split the dataset, then stop")
    parser.add_argument("--force", action="store_true", help="Train even below the recommended image count")
    args = parser.parse_args()

    issues = validate_dataset(DATASET_DIR)
    if issues:
        print(f"Found {len(issues)} dataset issue(s):")
        for issue in issues[:20]:
            print(f"  - {issue}")
        if len(issues) > 20:
            print(f"  ... and {len(issues) - 20} more")
        sys.exit(1)

    image_count = len(find_image_label_pairs(DATASET_DIR))
    print(f"Dataset OK: {image_count} labeled image(s) in {DATASET_DIR}")

    if image_count < MIN_RECOMMENDED_IMAGES and not args.force:
        print(
            f"\nOnly {image_count} images — below the recommended minimum of "
            f"{MIN_RECOMMENDED_IMAGES} for a useful fine-tune. Keep uploading classroom "
            "photos and clicking 'Export Training Data' after correcting them, then re-run.\n"
            "Pass --force to train anyway (mainly useful to sanity-check the pipeline runs)."
        )
        sys.exit(1)

    train_images, val_images = split_dataset(DATASET_DIR, val_fraction=args.val_fraction)
    data_yaml = write_split_files(DATASET_DIR, train_images, val_images)
    print(f"Split: {len(train_images)} train / {len(val_images) or len(train_images)} val -> {data_yaml}")

    if args.dry_run:
        print("Dry run requested — stopping before training.")
        return

    from ultralytics import YOLO  # imported lazily: heavy dependency, and --dry-run shouldn't need it

    model = YOLO(args.weights)
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        project=str(RUNS_DIR),
        name="classroom_finetune",
    )
    print(f"\nDone. Wire the resulting best.pt into vision/detection/detector.py's `weights` default "
          f"once you've checked it with evaluate.py.")


if __name__ == "__main__":
    main()
