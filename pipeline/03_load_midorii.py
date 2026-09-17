#!/usr/bin/env python3
"""03_load_midorii.py — MIDORI2 (curated GenBank) -> sqlite

MIDORI2 vGB273 (Zenodo 10.5281/zenodo.22685700) — RAW zip unpacks per-gene FASTA.
We keep: COI, srRNA (12S rRNA gene), lrRNA (16S rRNA gene).
Headers look like: >COI|species binomial|...   (adjust parser to actual header on first run)

Input:  data/raw/MIDORI2_GB273_RAW/   (unpacked)
Output: sqlite db/coverage.db  table bold_genbank(seq_key UNIQUE, src_db, marker, species, length, country)
"""
import re
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "db" / "coverage.db"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "MIDORI2_GB273_RAW"
MARKER_FILES = {
    "COI": ["*COI*", "*cox1*"],
    "12S": ["*srRNA*", "*12S*"],
    "16S": ["*lrRNA*", "*16S*"],
}
MIN_LEN = {"COI": 500, "12S": 300, "16S": 300}  # frozen thresholds


def ensure_db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS sequences(
               seq_key TEXT PRIMARY KEY, src_db TEXT, marker TEXT,
               species TEXT, length INTEGER, country TEXT)"""
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_seq_marker ON sequences(marker, src_db)")
    return con


def parse_fasta(path: Path, marker: str, con: sqlite3.Connection) -> int:
    n = 0
    name, seq = None, []
    def flush():
        nonlocal n
        if name and seq:
            s = "".join(seq).replace("-", "").upper()
            if len(s) >= MIN_LEN[marker]:
                m = re.match(r"^>?([A-Za-z0-9_.\-]+)\|([^|]+)\|", name)
                sp = m.group(2).strip() if m else name[1:].split("|")[0].strip()
                con.execute(
                    "INSERT OR IGNORE INTO sequences VALUES(?,?,?,?,?,?)",
                    (f"midorii:{name[1:].split('|')[0]}", "MIDORI2_GB273", marker, sp, len(s), None),
                )
                n += 1
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if line.startswith(">"):
            flush(); name, seq = line, []
        elif line:
            seq.append(line)
    flush()
    return n


def main() -> None:
    con = ensure_db()
    for marker, patterns in MARKER_FILES.items():
        files = [p for pat in patterns for p in RAW.rglob(pat)]
        for p in files:
            k = parse_fasta(p, marker, con)
            print(f"{p.name}: {k} rows (>= {MIN_LEN[marker]} bp)")
    con.commit()
    print("done")


if __name__ == "__main__":
    main()
