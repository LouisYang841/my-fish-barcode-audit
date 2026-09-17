# HANDOFF — cloud agent onboarding

> 交接给云端环境的 agent。项目背景、冻结口径、复现步骤见 README.md。
> 本文件不含任何密钥——`.env`（IUCN token + NCBI api_key）需在本地安全渠道建立。

## Current status (2026-09-18)

- Species list frozen: **N = 2087** (`data/species_list_raw.csv`, snapshot 2026-09-18; Teleostei 1,957 + Elasmobranchii 130)
- GBIF synonym mapping done: `data/species_names.csv` (2,087/2,087)
- MIDORI2 vGB273 parsed into sqlite on the dev machine (`db/coverage.db`; **not committed** — rebuild here):
  fish-lineage rows: COI 631,912 / 12S 236,274 / 16S 311,981
- **GenBank-side coverage (headline numbers)**:
  COI 77.2% (robust ≥3 seq: 68.7%) · 12S 61.8% (35.7%) · 16S 64.8% (40.6%)
- BOLD side: **not fetched yet** — `pipeline/04_fetch_bold.py` is ready and spike-verified (2026-09-18)
- IUCN stratification + Fisher's exact: pending (API returning 525 as of 2026-09-18; retry)

## Next steps (deadline: abstract 2026-09-30)

1. Download data: `wget https://zenodo.org/records/22685701/files/MIDORI2_GB273_RAW.zip -O data/raw/MIDORI2_GB273_RAW.zip`
   (md5 must be `6145c5f0844780b93b38deec04ea64b3`; unpack only `RAW/total/*_{CO1,lrRNA,srRNA}_RAW.fasta.gz`)
2. `python pipeline/03_load_midorii.py` → rebuild `db/coverage.db` (~1 min)
3. `python pipeline/04_fetch_bold.py` → BOLD v5 three-stage API, per-class queries (`tax:class:Teleostei`, `tax:class:Chondrichthyes`); report 21% missing-country rate
4. `python pipeline/05_coverage.py` → three-library merged table + "BOLD-only increment" headline
5. IUCN overlay + Fisher's exact (Threatened = CR/EN/VU vs LC) → gap list → figures (06) → abstract ≤300 words

## Environment note

- Pipeline needs Python ≥ 3.10 (uses `X | None` unions and builtin generics).
- Create `.env` locally (never commit): `IUCN_TOKEN=...`, `NCBI_API_KEY=...`
- BOLD v5 API docs: https://boldsystems.org/data/api ; MIDORI2: Zenodo DOI 10.5281/zenodo.22685700
- Known gotchas are documented in pipeline docstrings (MIDORI2 `srRNA` = 12S rRNA gene; FishBase single-quoted HTML; BOLD old API dead).
