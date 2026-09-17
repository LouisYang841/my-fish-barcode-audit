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

## References

Key prior work this audit builds on (see also in-pipeline comments):

- Hebert, P. D. N., Ratnasingham, S., & de Waard, J. R. (2003). Biological identifications through DNA barcodes. *Proceedings of the Royal Society B*, 270, 313–321. https://doi.org/10.1098/rspb.2002.2218
- Ratnasingham, S., & Hebert, P. D. N. (2007). BOLD: The Barcode of Life Data System. *Molecular Ecology Notes*, 7(3), 355–364. https://doi.org/10.1111/j.1471-8286.2007.01678.x
- Weigand, H., et al. (2019). DNA barcode reference libraries for the monitoring of aquatic biota in Europe: Gap-analysis and recommendations for future work. *Science of the Total Environment*, 678, 452–478. https://doi.org/10.1016/j.scitotenv.2019.04.247
- Leray, M., Knowlton, N., & Machida, R. J. (2022). MIDORI2: A collection of quality controlled, preformatted, and regularly updated reference databases for taxonomic assignment of eukaryotic mitochondrial sequences. *Environmental DNA*, 4(4), 894–907. https://doi.org/10.1002/edn3.303
- Li, F., et al. (2022). Gap analysis for DNA-based biomonitoring of aquatic ecosystems in China. *Ecological Indicators*, 137, 108732. https://doi.org/10.1016/j.ecolind.2022.108732
- Munian, K., et al. (2024). The viability and potential of environmental DNA (eDNA) detection of freshwater fish based on current genetic resources in Malaysia. *Sains Malaysiana*, 53(1), 11–21. https://doi.org/10.17576/jsm-2024-5301-02
- DNA barcode reference database and gap analysis for biomonitoring Hong Kong's marine animals (2024). *Regional Studies in Marine Science*. https://www.sciencedirect.com/science/article/pii/S2352485524005796
- Luypaert, T., et al. (2026). Barcoding gaps and sequencing prioritisation in a global biodiversity stronghold. *Research Square* (preprint, under review). https://doi.org/10.21203/rs.3.rs-9096952/v1

## Data sources

- MIDORI2 vGB273: Zenodo DOI 10.5281/zenodo.22685700
- BOLD Portal API docs: https://boldsystems.org/data/api
- GBIF backbone: https://api.gbif.org/v1/species/match
