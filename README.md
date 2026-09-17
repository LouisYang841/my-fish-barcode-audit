# Malaysian fish DNA barcode reference coverage audit

Reproducible multi-marker audit of COI / 12S / 16S reference coverage for the fishes
of Malaysia (marine + freshwater) across three public libraries:

1. **MIDORI2 vGB273** (curated GenBank subset; Zenodo DOI 10.5281/zenodo.22685700)
2. **BOLD public data** (BOLD Portal API, three-stage query: preprocessor -> query -> documents)
3. **Both combined**

Outputs: coverage tables, family x marker heatmap, IUCN-threatened vs LC comparison
(Fisher's exact test), local-origin share of sequences, and a ranked gap list.

## Reproduce

```bash
# 1. species list: export FishBase country checklist (marine + freshwater) to
#    data/raw/fishbase_marine.tsv / fishbase_fresh.tsv
python pipeline/01_build_list.py          # freezes N
python pipeline/02_gbif_match.py          # synonyms -> accepted names (resumable)

# 2. reference libraries
python pipeline/03_load_midorii.py        # parse MIDORI2 FASTA (COI/srRNA/lrRNA)
python pipeline/04_fetch_bold.py          # BOLD v5 API, per-class queries (resumable)

# 3. metrics + figures
python pipeline/05_coverage.py
python pipeline/06_figs.py
```

## Frozen decisions

- Species list: FishBase country checklist, `possible` occurrence records excluded,
  introduced species kept and tagged. N is frozen in `data/species_list_raw.csv`.
- Coverage is counted against GBIF-backbone accepted names only.
- Length thresholds: COI >= 500 bp; 12S >= 300 bp; 16S >= 300 bp.
- Robust coverage = >= 3 sequences per species.
- IUCN: "Threatened" = CR/EN/VU only; NT reported separately as "NT or higher".
- BOLD scope = public data only (documented limitation).

## Data sources

- MIDORI2 vGB273: Zenodo DOI 10.5281/zenodo.22685700
- BOLD Portal API docs: https://boldsystems.org/data/api
- GBIF backbone: https://api.gbif.org/v1/species/match
