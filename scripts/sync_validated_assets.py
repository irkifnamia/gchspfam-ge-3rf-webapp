"""Copy the validated Stage 9 charts into this deployment repository."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import discover_results_root  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    results_root = discover_results_root()
    if results_root is None:
        raise RuntimeError("The validated results project was not found.")
    source_root = results_root / "outputs" / "stage9" / "charts"
    target_root = ROOT / "assets" / "charts"
    target_root.mkdir(parents=True, exist_ok=True)
    sources = sorted(source_root.glob("*.png"))
    if len(sources) != 39:
        raise ValueError(f"Expected 39 Stage 9 figures, found {len(sources)}")
    manifest = []
    for source in sources:
        target = target_root / source.name
        shutil.copy2(source, target)
        manifest.append({"filename": source.name, "size_bytes": target.stat().st_size, "sha256": sha256(target)})
    (ROOT / "data" / "chart_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Copied and hashed {len(manifest)} validated figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
