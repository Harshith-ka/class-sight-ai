"""Evaluate a fine-tuned checkpoint against the held-out validation split
(spec section 43: mAP@50, mAP@50-95, precision, recall).

Usage:
    python evaluate.py ../training/runs/classroom_finetune/weights/best.pt
"""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_DATA_YAML = Path(__file__).resolve().parents[1] / "training_data" / "splits" / "data.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("weights", help="Path to a trained .pt checkpoint")
    parser.add_argument("--data", default=str(DEFAULT_DATA_YAML), help="data.yaml written by train.py")
    args = parser.parse_args()

    if not Path(args.data).exists():
        raise SystemExit(
            f"{args.data} not found — run train.py first (even with --dry-run) to generate the split."
        )

    from ultralytics import YOLO  # imported lazily: heavy dependency

    model = YOLO(args.weights)
    metrics = model.val(data=args.data)

    print(f"mAP50:      {metrics.box.map50:.3f}")
    print(f"mAP50-95:   {metrics.box.map:.3f}")
    print(f"Precision:  {metrics.box.mp:.3f}")
    print(f"Recall:     {metrics.box.mr:.3f}")


if __name__ == "__main__":
    main()
