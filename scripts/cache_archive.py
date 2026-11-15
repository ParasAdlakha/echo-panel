"""Pack the per-call cache into one archive for the repository, or restore it.

    python scripts/cache_archive.py pack      results/cache/  -> results/calls.jsonl.gz
    python scripts/cache_archive.py unpack    results/calls.jsonl.gz -> results/cache/

Each line of the archive is one model call: {"key", "model", "messages", "seed", "text", "usage"}.
After `unpack`, every pipeline step reads from the cache and makes no new API calls.
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "results" / "cache"
ARCHIVE = ROOT / "results" / "calls.jsonl.gz"


def pack():
    n = 0
    with gzip.open(ARCHIVE, "wt", encoding="utf-8") as f:
        for p in sorted(CACHE.glob("*/*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            d["key"] = p.stem
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
            n += 1
    print(f"packed {n} calls -> {ARCHIVE} ({ARCHIVE.stat().st_size / 1e6:.1f} MB)")


def unpack():
    n = 0
    with gzip.open(ARCHIVE, "rt", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            key = d.pop("key")
            out = CACHE / key[:2] / f"{key}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(d), encoding="utf-8")
            n += 1
    print(f"restored {n} calls -> {CACHE}")


if __name__ == "__main__":
    {"pack": pack, "unpack": unpack}[sys.argv[1]]()
