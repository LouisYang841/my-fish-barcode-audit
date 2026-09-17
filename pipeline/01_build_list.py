#!/usr/bin/env python3
"""01_build_list.py — fetch FishBase RegionSpeciesList (Malaysia, c_code=458) and freeze N.

Source: https://fishbase.se/identification/RegionSpeciesList.php?c_code=458
Snapshot date is stamped into the output; FishBase updates bimonthly.

Usage:
  python 01_build_list.py            # fetch missing pages, parse, freeze N
Pages cached in data/raw/fishbase_pages/ (re-run resumes, no re-fetch).
"""
import csv
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

BASE = "https://fishbase.se/identification/RegionSpeciesList.php?c_code=458"
RAWP = Path(__file__).resolve().parents[1] / "data" / "raw" / "fishbase_pages"
OUT = Path(__file__).resolve().parents[1] / "data" / "species_list_raw.csv"
UA = {"User-Agent": "Mozilla/5.0 (academic research script; fish coverage audit)"}
SNAP = date.today().isoformat()


def fetch_page(page: int) -> str:
    p = RAWP / f"page_{page:02d}.html"
    if p.exists() and p.stat().st_size > 5000:
        return p.read_text(encoding="utf-8", errors="ignore")
    url = BASE + (f"&resultPage={page}" if page > 1 else "")
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", errors="ignore")
    p.write_text(html, encoding="utf-8")
    time.sleep(0.9)  # be polite: FishBase is a small non-profit server
    return html


def parse(html: str) -> list[tuple[str, str, str, str, str]]:
    """Return (species, speccode, class, order, family) per card.

    Card structure (verified 2026-09-18):
      <a href='../summary/SpeciesSummary.php?id=4307'><i>Acanthurus bariene</i></a>
      <strong>Class:</strong> Teleostei <br/>
      <strong>Order:</strong><a ...>Acanthuriformes</a><br/>
      <strong>Family:</strong><a ...> Acanthuridae </a>
    Note: species link uses lowercase `id=`; FamilySummary uses uppercase `ID=`.
    """
    out = []
    for m in re.finditer(
        r"SpeciesSummary\.php\?id=(\d+)['\"][^>]*>\s*(?:<i>)?\s*([A-Z][a-z]+(?:\s+[a-z\-]+){1,2})\s*(?:</i>)?\s*</a>(.*?)(?=SpeciesSummary\.php|</table>|$)",
        html,
        re.S,
    ):
        speccode, name, tail = m.group(1), m.group(2).strip(), m.group(3)[:3000]
        c = re.search(r"Class:</strong>\s*([A-Za-z]+)", tail)
        o = re.search(r"Order:</strong>\s*(?:<a[^>]*>)?\s*([A-Za-z/]+)", tail)
        f = re.search(r"Family:</strong>\s*(?:<a[^>]*>)?\s*([A-Za-z]+)", tail)
        out.append((name, speccode, c.group(1) if c else "", o.group(1) if o else "", f.group(1) if f else ""))
    return out


def main() -> None:
    RAWP.mkdir(parents=True, exist_ok=True)
    # pass 1: discover total n from page 1
    first = fetch_page(1)
    n = re.search(r"n\s*=\s*([\d,]+)", first)
    total = int(n.group(1).replace(",", "")) if n else 0
    per_page = len(parse(first)) or 50
    pages = (total + per_page - 1) // per_page if total else 1
    print(f"total n={total}, per_page={per_page} -> {pages} pages")

    seen: dict[str, dict] = {}
    for pg in range(1, pages + 1):
        html = fetch_page(pg)
        rows = parse(html)
        if not rows:
            print(f"page {pg}: EMPTY, stop")
            break
        for name, speccode, cls, order, fam in rows:
            k = name.lower()
            if k not in seen:
                seen[k] = {"species": name, "speccode": speccode, "class": cls, "order": order, "family": fam}
        print(f"page {pg}: +{len(rows)} (unique {len(seen)})")

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["species", "speccode", "class", "order", "family"])
        w.writeheader()
        w.writerows(seen.values())
    print(f"FROZEN N = {len(seen)}  (snapshot {SNAP}) -> {OUT}")


if __name__ == "__main__":
    sys.exit(main())
