#!/usr/bin/env python3
"""03_load_midorii.py — MIDORI2 vGB273 (curated GenBank) -> sqlite

Verified file layout (2026-09-18):
  data/raw/MIDORI2_GB273_RAW/RAW/total/MIDORI2_TOTAL_NUC_GB273_{CO1,lrRNA,srRNA}_RAW.fasta.gz
Header format:  >LC098275.1.<1.>604 root_1;...;family_Gobionidae_2743714;genus_Pseudorasbora_38758;species_Pseudorasbora parva_51549
  - first token = accession (+ coords), species name in the `species_..._<taxid>` segment
  - we keep only fish-lineage rows (class whitelist) to keep sqlite small
  - country is not present in MIDORI2 -> NULL (local-origin analysis uses BOLD + GenBank efetch)
"""
import gzip
import re
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "db" / "coverage.db"
RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
FILES = {
    "COI": RAW / "MIDORI2_GB273_RAW/RAW/total/MIDORI2_TOTAL_NUC_GB273_CO1_RAW.fasta.gz",
    "12S": RAW / "MIDORI2_GB273_RAW/RAW/total/MIDORI2_TOTAL_NUC_GB273_srRNA_RAW.fasta.gz",
    "16S": RAW / "MIDORI2_GB273_RAW/RAW/total/MIDORI2_TOTAL_NUC_GB273_lrRNA_RAW.fasta.gz",
}
FISH_LINEAGE = re.compile(
    r"class_(Actinopteri|Actinopterygii|Teleostei|Elasmobranchii|Holocephali|Cladistia|Chondrostei|Dipnoi)_"
    r"|superclass_(Actinopterygii|Chondrichthyes|Sarcopterygii)_"
    r"|subclass_Dipnoi_"
)
SPECIES_SEG = re.compile(r"species_(.+?)_(\d+)(?:;|$)")
ACC = re.compile(r"^>([A-Za-z0-9_.]+)")
BATCH = 200_000


def ensure_db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS sequences(
               seq_key TEXT PRIMARY KEY, src_db TEXT, marker TEXT,
               species TEXT, length INTEGER, country TEXT)"""
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_seq_sp ON sequences(species, marker)")
    return con


def parse_file(path: Path, marker: str, con: sqlite3.Connection) -> int:
    n = 0
    batch = []
    name, seq = None, []

    def flush():
        nonlocal n
        if name is None or not seq:
            return
        header, s = name, "".join(seq).replace("-", "").upper()
        acc = ACC.match(header).group(1) if ACC.match(header) else header[1:30]
        sp = ""
        tail = header.split(" ", 1)
        if len(tail) > 1:
            for seg in reversed(tail[1].split(";")):
                if seg.startswith("species_"):
                    sp = SPECIES_SEG.match(seg).group(1) if SPECIES_SEG.match(seg) else ""
                    break
        if sp:
            batch.append((f"midorii:{acc}:{marker}", "MIDORI2_GB273", marker, sp, len(s), None))
            n += 1
            if len(batch) >= BATCH:
                con.executemany("INSERT OR IGNORE INTO sequences VALUES(?,?,?,?,?,?)", batch)
                con.commit()
                batch.clear()

    with gzip.open(path, "rt", errors="ignore") as f:
        keep = False
        for line in f:
            line = line.strip()
            if line.startswith(">"):
                flush()
                name, seq = line, []
                keep = FISH_LINEAGE.search(name) is not None
                continue
            if name is not None and keep:
                seq.append(line)
        flush()
    if batch:
        con.executemany("INSERT OR IGNORE INTO sequences VALUES(?,?,?,?,?,?)", batch)
        con.commit()
    return n


def main() -> None:
    con = ensure_db()
    for marker, path in FILES.items():
        if not path.exists():
            print(f"[skip] {path} missing")
            continue
        n = parse_file(path, marker, con)
        print(f"{marker}: {n} fish rows loaded from {path.name}")
    print("done")


if __name__ == "__main__":
    main()
