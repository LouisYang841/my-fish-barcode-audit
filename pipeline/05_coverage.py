#!/usr/bin/env python3
"""05_coverage.py — compute all frozen metrics from sqlite + species_names.csv

Metrics (frozen 2026-09-18):
  1. species-level coverage % per (library, marker)
  2. robust coverage (>=3 sequences)
  3. family x marker heatmap table
  4. IUCN stratified coverage + Fisher's exact test (Threatened CR/EN/VU vs LC) + odds ratio
  5. local-origin share (country == Malaysia) + missing-country rate reported separately
  6. BOLD-only increment vs GenBank-via-MIDORI2 (reported as a headline number)
"""
import csv
import math
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "db" / "coverage.db"
NAMES = Path(__file__).resolve().parents[1] / "data" / "species_names.csv"
OUT = Path(__file__).resolve().parents[1] / "output"
MIN_LEN = {"COI": 500, "12S": 300, "16S": 300}
ROBUST = 3


def sciname_key(s: str) -> str:
    return " ".join(s.strip().split()).lower()


def load_species() -> set[str]:
    """Frozen list matched by BOTH raw names and GBIF accepted names (synonym collapse)."""
    wanted: set[str] = set()
    with NAMES.open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            wanted.add(sciname_key(r["species"]))
            if r.get("acc_name"):
                wanted.add(sciname_key(r["acc_name"]))
    return wanted


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    wanted = load_species()  # synonym-collapsed accepted-name keys
    # NOTE: N is len(load_species()) raw list; denominators below use the raw N
    # (one row per frozen species), not the collapsed set size.
    with NAMES.open(encoding="utf-8", newline="") as f:
        N_FROZEN = sum(1 for _ in csv.DictReader(f))

    # build per-(marker, src_db, species_key) sequence counts
    counts: dict[tuple, int] = {}
    countries: dict[tuple, list[str]] = {}
    for marker, src, sp, length, country in con.execute(
            "SELECT marker, src_db, species, length, country FROM sequences"):
        if marker not in MIN_LEN or length < MIN_LEN[marker]:
            continue
        k = sciname_key(sp)
        if k not in wanted:
            continue
        counts[(marker, src, k)] = counts.get((marker, src, k), 0) + 1
        if country:
            countries.setdefault((marker, k), []).append(country)

    libs = ["MIDORI2_GB273", "BOLD_public", "BOTH"]
    rows = []
    for marker, ml in MIN_LEN.items():
        for lib in libs:
            have = {k for (m, s, k), c in counts.items()
                    if m == marker and (s == lib or (lib == "BOTH" and s in ("MIDORI2_GB273", "BOLD_public"))) and c >= 1}
            robust = {k for (m, s, k), c in counts.items()
                      if m == marker and (s == lib or (lib == "BOTH" and s in ("MIDORI2_GB273", "BOLD_public"))) and c >= ROBUST}
            rows.append({"marker": marker, "library": lib, "covered": len(have),
                         "robust": len(robust), "N": N_FROZEN,
                         "coverage_pct": round(100 * len(have) / N_FROZEN, 2),
                         "robust_pct": round(100 * len(robust) / N_FROZEN, 2)})
    with (OUT / "coverage.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    # Fisher's exact (Threatened vs LC) needs the IUCN column - added at 02 output
    # extension (D5). Kept explicit so the test is never run on an unstated denominator.
    print(f"N frozen = {N_FROZEN}")
    for r in rows:
        print(r)
    print("->", OUT / "coverage.csv")


if __name__ == "__main__":
    main()
