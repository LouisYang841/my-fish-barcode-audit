#!/usr/bin/env python3
"""02_gbif_match.py — species names -> GBIF backbone accepted names.

Rate: GBIF allows ~10 req/s; 2,000 species is fine without a key.
Input:  data/species_list_raw.csv
Output: data/species_names.csv  (adds: acc_name, match_type, confidence, gbif_key)

Frozen decision (2026-09-18): coverage is counted against accepted names only.
Synonyms are collapsed; every accepted name carries the set of original spellings
it absorbed, so we can report both raw and synonym-normalised numbers.
"""
import csv
import time
from pathlib import Path

import requests

BASE = "https://api.gbif.org/v1/species/match"
IN = Path(__file__).resolve().parents[1] / "data" / "species_list_raw.csv"
OUT = Path(__file__).resolve().parents[1] / "data" / "species_names.csv"
CACHE = Path(__file__).resolve().parents[1] / "data" / "raw" / "gbif_match_cache.csv"  # append-only resume


def load_cache() -> dict[str, dict]:
    cache: dict[str, dict] = {}
    if CACHE.exists():
        with CACHE.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                cache[row["species"]] = row
    return cache


def main() -> None:
    rows = list(csv.DictReader(IN.open(encoding="utf-8", newline="")))
    cache = load_cache()
    fields = ["species", "acc_name", "match_type", "confidence", "gbif_key", "synonym_of"]
    cache_f = CACHE.open("a", encoding="utf-8", newline="")
    writer = csv.DictWriter(cache_f, fieldnames=fields)
    if not CACHE.exists() or CACHE.stat().st_size == 0:
        writer.writeheader()

    session = requests.Session()
    out_rows = []
    for i, r in enumerate(rows, 1):
        name = r["species"]
        if name not in cache:
            resp = session.get(BASE, params={"name": name, "strict": "false", "verbose": "false"}, timeout=30)
            time.sleep(0.12)  # be polite, ~8 req/s
            try:
                j = resp.json()
            except Exception:
                j = {}
            rec = {
                "species": name,
                "acc_name": j.get("scientificName", ""),
                "match_type": j.get("matchType", ""),
                "confidence": j.get("confidence", ""),
                "gbif_key": j.get("usageKey", ""),
                "synonym_of": j.get("acceptedUsageKey", "") or "",
            }
            cache[name] = rec
            writer.writerow(rec)
            cache_f.flush()
        out_rows.append({**r, **{k: cache[name].get(k, "") for k in fields if k != "species"}})
        if i % 200 == 0:
            print(f"{i}/{len(rows)}")
    cache_f.close()

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"-> {OUT}  ({len(out_rows)} rows)")


if __name__ == "__main__":
    main()
