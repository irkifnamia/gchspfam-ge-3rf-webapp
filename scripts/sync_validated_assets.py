"""Package compact validated analytics and Stage 9 charts for deployment."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

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


def sync_analytics(results_root: Path) -> list[dict[str, object]]:
    """Package small research-ready tables; full candidates remain in Neon."""
    analytics_root = results_root / "outputs" / "analytics"
    stage9_data_root = results_root / "outputs" / "stage9" / "data"
    target_root = ROOT / "data" / "analytics"
    target_root.mkdir(parents=True, exist_ok=True)

    sources = {
        "selected_plans_research_ready.parquet": analytics_root / "selected_plans_research_ready.parquet",
        "matched_framework_results.parquet": analytics_root / "matched_framework_results.parquet",
    }
    manifest: list[dict[str, object]] = []
    for filename, source in sources.items():
        target = target_root / filename
        shutil.copy2(source, target)
        frame = pd.read_parquet(target)
        manifest.append(
            {
                "filename": filename,
                "source": str(source.relative_to(results_root)),
                "records": len(frame),
                "columns": len(frame.columns),
                "size_bytes": target.stat().st_size,
                "sha256": sha256(target),
            }
        )

    fixed_source = stage9_data_root / "fixed_plan_oc_evaluations.csv"
    fixed_target = target_root / "fixed_plan_oc_evaluations.parquet"
    fixed = pd.read_csv(fixed_source, float_precision="round_trip")
    fixed.to_parquet(fixed_target, index=False)
    manifest.append(
        {
            "filename": fixed_target.name,
            "source": str(fixed_source.relative_to(results_root)),
            "records": len(fixed),
            "columns": len(fixed.columns),
            "size_bytes": fixed_target.stat().st_size,
            "sha256": sha256(fixed_target),
        }
    )

    (target_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    results_root = discover_results_root()
    if results_root is None:
        raise RuntimeError("The validated results project was not found.")
    analytics_manifest = sync_analytics(results_root)
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
    print(f"Packaged {len(analytics_manifest)} compact analytics tables and {len(manifest)} validated figures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
