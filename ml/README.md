# Phase 3 — Custom Model Bridge

This directory is the bridge from Phase 1's pretrained-YOLO-plus-heuristics
pipeline to a real classroom-specific detector (spec §14-15, §40-44).

## How data gets here

There's no separate labeling tool. The app's manual-correction UI *is* the
labeling tool: upload a photo, correct anything the pretrained detector got
wrong (add missed seats, delete false ones, mark occupied/empty, move
misplaced seats, place the instructor), then click **Export Training Data**.
That writes the current image plus a YOLO-format label file here:

```
training_data/
  images/<analysis_id>.jpg
  labels/<analysis_id>.txt   # "0 cx cy w h" per seat, "1 cx cy w h" for instructor if present
  data.yaml                  # auto-generated, describes the class names
```

## Bringing in external datasets

`ml/training/ingest_external.py` converts an external YOLO-format dataset
into our schema (spec §41 "Dataset Class Normalization") — it maps the
source's class names onto ours (`seat`, `instructor`), drops everything
else, and skips images where nothing survived the mapping:

```bash
cd ml/training
python ingest_external.py /path/to/source --map chair=seat teacher=instructor --dry-run
python ingest_external.py /path/to/source --map chair=seat teacher=instructor
```

The source needs an `images/`+`labels/` layout (flat, or split into
`train`/`val`/`test`) and a `data.yaml` with a `names` map — the standard
Roboflow/Kaggle YOLO export layout.

**Vet the images before running this for real, not just the class name.**
A class-name match is not enough — we found this out concretely: Kaggle's
["Objects in the Classroom"](https://www.kaggle.com/datasets/aryakrisnaputra/objects-in-the-classroom)
dataset (MIT license, freely downloadable, 4,000 images, `chair` class)
looked like a perfect fit, but visual inspection of its `chair`-labeled
images showed e-commerce/product photos — a single chair centered on a
white background — not real classroom scenes. 69% of them contain exactly
one labeled object, which is the signature of an isolated product shot, not
a photo of a room. Training on that would teach the model "chair = centered
object on white background," which is the opposite of our actual problem
(small, partially-occluded seats viewed at an angle in a cluttered room).
**Rejected — not ingested.**

Two sources that do look genuinely on-target but need action from you
(neither can be scripted from here without your credentials):

- **[Roboflow "classroom_chairs"](https://universe.roboflow.com/object-detection-icvyw/classroom_chairs)**
  — 272 real images, `chair_empty`/`chair_occupied`/`chairs` classes, CC BY
  4.0. Exporting requires a free Roboflow account + API key (the site gates
  the actual file download behind login, even for public CC-licensed
  datasets). Sign up, grab your key from account settings, and I can script
  the download + `ingest_external.py` conversion.
- **[SCB-Dataset5](https://github.com/Whiffe/SCB-dataset)** — the most
  classroom-specific option (has an actual `teacher` class, which we don't
  get from anywhere else), but it's distributed via Baidu Netdisk, which
  isn't practical to script from here. Would need you to download it
  manually and hand off the files.

## Running training

```bash
cd ml/training
python train.py --dry-run   # validate the dataset + build a train/val split, no training
python train.py             # fine-tune yolov8s.pt (refuses below 30 images without --force)
```

**Realistic expectations**: transfer learning from COCO weights can show a
useful signal with as few as ~30-50 diverse images (different rooms, angles,
lighting). The product spec's 500-1,500 image target is what it'd take to
reliably beat the current heuristic pipeline (tiled inference + desk-based
seat inference) across varied classrooms. Below 30 images, `train.py` won't
run without `--force` — a checkpoint "trained" on a handful of images from
one room will look trained but won't generalize.

## Evaluating a checkpoint

```bash
cd ml/evaluation
python evaluate.py ../training/runs/classroom_finetune/weights/best.pt
```

Reports mAP@50, mAP@50-95, precision, recall (spec §43) against the held-out
validation split `train.py` generated.

## Wiring a trained model back in

Once a checkpoint is validated, point `vision/detection/detector.py`'s
`ObjectDetector.__init__` `weights` default at it. At that point the
class-alias/desk-inference machinery in `vision/seats/seat_detector.py`
becomes largely redundant (a model trained on the `seat`/`instructor`
classes directly should need much less heuristic scaffolding) — that's the
point where it's worth simplifying that module rather than layering the new
model underneath the old workarounds.
