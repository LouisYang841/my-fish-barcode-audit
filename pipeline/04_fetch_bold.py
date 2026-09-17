#!/usr/bin/env python3
"""04_fetch_bold.py — BOLD v5 Portal API (verified 2026-09-18) -> sqlite

Three-stage flow (official docs: boldsystems.org/data/api):
  1. GET /api/query/preprocessor?query=tax:family:Cyprinidae   -> validate & normalise triplets
  2. GET /api/query?query=tax:family:Cyprinidae&extent=full     -> {"query_id": "...", ...}
  3. GET /api/documents/<query_id>/download?format=tsv          -> BCDM TSV (<=1M records)

Spike results (Cyprinidae, 2026-09-18):
  - works without auth; query_id valid 24h
  - TSV has: species(22), country/ocean(48), nuc_basecount(68), marker_code(71), insdc_acs(69)
  - country missing rate 21% (sample) - must be reported, not silently dropped
  - marker codes present: COI-5P, 12S, 16S, CYTB, ... -> filter locally

Strategy: per-class queries (Teleostei, Chondrichthyes) instead of ~200 families.
The 1M cap is comfortably above the expected global fish barcode count.
"""
import sqlite3
import time
from pathlib import Path

import requests

BASE = "https://portal.boldsystems.org/api"
DB = Path(__file__).resolve().parents[1] / "db" / "coverage.db"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
KEEP_MARKERS = {"COI-5P", "12S", "16S"}
QUERIES = ["tax:class:Teleostei", "tax:class:Chondrichthyes"]  # extend if needed
MIN_LEN = 300  # per-marker thresholds applied in 05_coverage.py, keep all here

COLS = {  # 0-based index -> name, per verified header
    "species": 21, "country": 47, "basecount": 67, "marker": 70, "insdc": 68,
}


def ensure_db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS sequences(
               seq_key TEXT PRIMARY KEY, src_db TEXT, marker TEXT,
               species TEXT, length INTEGER, country TEXT)"""
    )
    return con


def run_query(session: requests.Session, query: str) -> str | None:
    r = session.get(f"{BASE}/query/preprocessor", params={"query": query}, timeout=60)
    r.raise_for_status()
    terms = r.json().get("successful_terms", [])
    if not terms:
        print(f"[skip] no match for {query}")
        return None
    matched = terms[0]["matched"]
    r = session.get(f"{BASE}/query", params={"query": matched, "extent": "full"}, timeout=120)
    r.raise_for_status()
    return r.json().get("query_id")


def download(session: requests.Session, qid: str, out: Path) -> Path:
    if out.exists() and out.stat().st_size > 0:
        print(f"[resume] {out.name} already downloaded")
        return out
    with session.get(f"{BASE}/documents/{qid}/download", params={"format": "tsv"},
                     stream=True, timeout=600) as r:
        r.raise_for_status()
        with out.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    return out


def load_tsv(path: Path, con: sqlite3.Connection, query: str) -> int:
    n = 0
    with path.open(encoding="utf-8", newline="") as f:
        header = f.readline().rstrip("\n").split("\t")
        idx = {name: header.index(name) for name in
               ["species", "country/ocean", "nuc_basecount", "marker_code", "record_id"] if name in header}
        for line in f:
            c = line.rstrip("\n").split("\t")
            try:
                sp = c[idx["species"]]
                marker = c[idx["marker_code"]]
                if marker not in KEEP_MARKERS or not sp:
                    continue
                length = int(float(c[idx["nuc_basecount"]] or 0))
                country = c[idx["country/ocean"]]
                con.execute("INSERT OR IGNORE INTO sequences VALUES(?,?,?,?,?,?)",
                            (f"bold:{c[idx['record_id']]}", "BOLD_public", marker, sp, length, country))
                n += 1
            except (IndexError, ValueError):
                continue
    con.commit()
    return n


def main() -> None:
    con = ensure_db()
    session = requests.Session()
    RAW.mkdir(parents=True, exist_ok=True)
    for q in QUERIES:
        tag = q.split(":")[-1]
        qid = run_query(session, q)
        if not qid:
            continue
        out = RAW / f"bold_{tag}.tsv"
        print(f"[{q}] query_id={qid}")
        download(session, qid, out)
        n = load_tsv(out, con, q)
        print(f"[{q}] loaded {n} rows into sqlite")
        time.sleep(2)
    print("done")


if __name__ == "__main__":
    main()
