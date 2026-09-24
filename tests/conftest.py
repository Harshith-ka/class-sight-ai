import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

# Mirrors backend/app/main.py's sys.path setup so tests can import both
# `vision.*` and `app.*` (backend) without a separate package install.
sys.path.insert(0, str(_ROOT / "backend"))
# ml/training/dataset.py is a plain script-adjacent module (train.py imports
# it as `from dataset import ...` since it's run directly), so it needs its
# own directory on sys.path too.
sys.path.insert(0, str(_ROOT / "ml" / "training"))
