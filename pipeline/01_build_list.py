#!/usr/bin/env python3
"""01_build_list.py — FishBase checklist -> species_list_raw.csv

Input:  data/raw/fishbase_*.tsv  (manual browser export or playwright dump)
        expected: one TSV exported per habitat (marine / freshwater), header row kept.
Output: data/species_list_raw.csv  (species, family, order, habitat, status)

Notes:
- FishBase checklist rows flagged as 'possible' occurrence are EXCLUDED (frozen decision 2026-09-18).
- Introduced species are KEPT but tagged in `status` column.
- N is frozen here; every downstream number must trace back to this file.
"""
import csv
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "species_list_raw.csv"

# Column-name candidates per FishBase HTML export; adjust to actual header after first export.
COLS = {
    "species": ["Species", "Scientific Name", "Species Name"],
    "family": ["Family"],
    "order": ["Order"],
    "status": ["Status", "Occurrence", "IUCN Red List Status"],
}


def load_tsv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return list(reader)


def pick(row: dict, names: list[str]) -> str:
    for n in names:
        if n in row and row[n].strip():
            return row[n].strip()
    return ""


def main() -> None:
    files = sorted(RAW.glob("fishbase_*.tsv"))
    if not files:
        sys.exit("No fishbase_*.tsv found in data/raw/ - export from browser first.")
    seen: dict[str, dict] = {}
    for f in files:
        habitat = "freshwater" if "fresh" in f.stem else ("marine" if "marine" in f.stem else "unknown")
        for row in load_tsv(f):
            status_raw = pick(row, COLS["status"]).lower()
            if "possible" in status_raw or "questionable" in status_raw:
                continue  # frozen: exclude possible records
            sp = pick(row, COLS["species"])
            if not sp:
                continue
            key = sp.lower()
            rec = seen.setdefault(key, {
                "species": sp,
                "family": pick(row, COLS["family"]),
                "order": pick(row, COLS["order"]),
                "habitat": habitat,
                "status": "introduced" if "introduced" in status_raw else ("native" if status_raw else ""),
            })
            if rec["habitat"] == "unknown" and habitat != "unknown":
                rec["habitat"] = habitat
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["species", "family", "order", "habitat", "status"])
        w.writeheader()
        w.writerows(seen.values())
    n = len(seen)
    fw = sum(1 for r in seen.values() if r["habitat"] == "freshwater")
    print(f"FROZEN N = {n}  (freshwater {fw}, marine/other {n - fw})")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
