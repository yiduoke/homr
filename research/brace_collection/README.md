# Real examples of the thin, nearly straight brace: collection, screening, labels (step 2 of the professor's plan)

Written 2026-11-17, 7:30 pm Pacific. Everything is in `run/brace_collection/` on the laptop (rendered pages and crops are not committed: 395 MB of
pages, 38 MB of extracted crops, 37 MB of labelled crops; they are rebuilt by the scripts below). PDFs are in `~/Downloads/imslp_brace_batch/`
(`downloads.md`: sha256, size, pages of 49 files, 175 MB; 3 same-series Schott files, 2 early Beethoven transfer files, 44 screened). No model was trained, no GPU box used (vast-homr4 and vast-homr5 untouched), nothing pushed.

## Result in short

1. **The three test scans come from two files of the same Schott series**, edited by August Schmid-Lindner (1917-18, B. Schott's Soehne, Mainz).
   The Transcendental Etudes 5 and 10 are pp. 29-37 and 76-85 of the 121-page volume (IMSLP #964191, plate 30341); the Sonata is IMSLP #364674 (plate 30373).
   The volume itself holds the other ten pieces (about 86 more pages) in the same brace style: **394 of 394 grand pairs on 78 labelled pages, the shipped model misses 392**.
   Two more files of the series (Piano Concertos 1 and 2 for two pianos, 1918; Concert-Etudes S.144, 1918) have the same engraving: misses 15 of 15, 68 of 214 and 68 of 282 grand pairs.
   That is the same-edition training pool: **194 pages (164 labelled), 905 grand pairs of other compositions than the three test pieces.**
2. **Independent thin-brace editions are rare.** 46 PDFs from about 25 publishers (1800-1987) were rendered and screened (6-12 pages each, all pages for the early Beethoven prints), by eye and by the shipped model on
   the pages the pipeline's own staff detection finds. 37 editions have a curved brace (thin or medium, with a connecting barline): 1,332 grand pairs, **2 missed**, 1 false grand, 2 false joins.
   The only edition besides Schott and the held-out Reichardt songs that the shipped model fails on is **Beethoven Op. 27/2, Cappi, Vienna 1802** (IMSLP #15808): a straight vertical
   line with short hooks at both ends (a square bracket, no curve) and no separate connecting line: 40 of 46 grand pairs missed, 10 false joins (binding shadow on the left edge). It is a weak
   scan and a different shape (hooked bracket, not a thin brace with a point), so it is a *transfer test of the straight-line idea*, not a second thin-brace edition. A second early edition
   (Eder 1800, Op. 13) fails 7 of 9 but only 2 of 21 pages could be labelled. Seven other early prints (1800-1822) are too blurred for the staff detector (see table).
3. **Split.** Train candidates: the Schott files below. Reserved, never train: the three test scans, the Mazeppa pages of the volume (Etude 4 is a test composition of the earlier
   work: the Peters Etude 4 was removed from the training data too), Cappi 1802 and Eder 1800 (transfer test), Reichardt 1819 (held out before), and every curved-brace edition (negative
   controls for regression: they must stay at 100 %).

## 1. Which edition the test scans are (checked on IMSLP and on the PDFs)

| test file in `run/scores/testset/` | IMSLP file | publisher, plate, year | editor | pages | used for |
|---|---|---|---|---|---|
| `liszt-transcendental-schott.pdf` (121 pp., FUJITSU fi-5530C2dj scan, Sibley Mirroring Project; Zwoelf Etueden in fortschreitender Schwierigkeit + Zwei Konzert-Etueden, title page, Inhalt, Vorwort) | #964191 | B. Schott's Soehne, Mainz, 1917, plate 30341 | August Schmid-Lindner | 121 | TE 5 = pdf pp. 29-37 (printed 31-39), TE 10 = pdf pp. 76-85 (printed 78-87) |
| `liszt-sonata-schott.pdf` (32 pp., scan 'Pages from 39087012348829Sonate.pdf', Sibley) | #364674 | B. Schott's Soehne, Mainz, 1917, plate 30373 | August Schmid-Lindner | 32 | Sonata pdf pp. 2-15 |

Contents of the volume by printed page (offset -2 to pdf pages): I Praeludium 8, II 10, III Landschaft 15, IV Mazeppa 18, **V Irrlichter 31, X 78**, VI Vision 40, VII Eroica 50, VIII Wilde Jagd 56,
IX Ricordanza 67, XI Abendklaenge 88, XII Schneegestoeber 96, Waldesrauschen 106, Gnomenreigen 115. Brace style (rendered and looked at, `figures/`): thin, nearly straight, short point, no connecting
line; barlines run inside the system only. The IMSLP page `Category:Schmid-Lindner, August/Editor` lists only these works; other Schott Liszt files of the series on IMSLP (checked on all 43 Liszt works with a
Schott edition, `Category:Scores published by Schott`): Concert-Etudes S.144 (Schott No. 06779, 1918), Piano Concertos 1 and 2 (1918, same Sibley series, barcode 39087012348811), the Paganini Etude 3 single edition
(No. 06550, 1950; not used), the Schubert-Liszt Wanderer Fantasy excerpt (1 page). The Schott edition 1913 of the Schubert Impromptus (Thuemer, plate 0687) has a curved brace (it is another engraving), the Schott 1906 d'Albert
Hungarian Rhapsodies (94 pp., not downloaded) are a different series.

## 2. Table (shipped model = the released relation model; labels from structure as in `staff_rel_realbrace/`)

Pages = pages rendered (all pages for the Schott and early Beethoven files, an even sample of 6-12 for the others); kept = pages with a label (even number of staffs per system k, chain of pairs, barlines
cross the gap of every paired set and of no separate pair, or, for pages without a barline in some gap, all paired gaps < 0.8 x the gap between systems; k = 2 piano, k = 4 two pianos
G / same system / G / separate). Missed = true grand staff not called grand by the shipped model (argmax); false join = separate pair called same system or grand. Detail: `table_raw.txt`, `split.tsv`.

| edition | publisher, year | IMSLP | pages / kept | systems | grand pairs | shipped misses | brace style (by eye) | split |
|---|---|---|---|---|---|---|---|---|
| Liszt Transcendental Etudes + Konzert-Etueden, ed. Schmid-Lindner, **other pieces** (pdf pp. 4-15, 38-75, 86-121) | Schott, Mainz, 1917 (plate 30341) | 964191 | 86 / 78 | 394 | 394 | **392 (99.5 %)**, 0 false join | thin, nearly straight, short point, no connecting line | **train candidate** |
| same volume, Etude 4 Mazeppa (pdf pp. 16-28) | Schott 1917 | 964191 | 13 / 8 | 43 | 43 | 43 (100 %) | same | **reserved** (test composition) |
| Liszt Concert-Etudes S.144, ed. Schmid-Lindner | Schott 1918 (No. 06779) | 04424 | 10 / 3 | 15 | 15 | 15 (100 %) | same (3-staff and ossia pages not labelled) | **train candidate** |
| Liszt Piano Concerto 1, two-piano score | Schott 1918 | 977987 | 44 / 36 | 107 | 214 (braces I and II) | 68 (32 %) | thin straight brace per piano with I / II | **train candidate** |
| Liszt Piano Concerto 2, two-piano score | Schott 1918 | 977999 | 54 / 47 | 141 | 282 | 68 (24 %) | same | **train candidate** |
| Beethoven Op. 27/2 | Cappi, Vienna, 1802 | 15808 | 16 / 10 | 46 | 46 | **40 (87 %)**, 10 false joins | straight line with two short hooks (square bracket), no connecting line; grey scan, binding shadow | **transfer test only** |
| Beethoven Op. 13 | Eder, Vienna, 1800 | 50958 | 21 / 2 | 9 | 9 | 7 (78 %), 3 false joins | style not checked by eye (grey, very poor scan) | **transfer test only** (too few pages) |
| 37 curved-brace editions (list in `table_raw.txt`: Haslinger 1835, Cranz 1814, Kistner 1833, Breitkopf 1839-1857, Simrock 1832-1898, Schuberth 1862, Senff 1872, Jurgenson 1878-1909, Zimmermann 1906, Belaieff 1898, Schlesinger 1910, Schott 1913, UE 1917, Peters 1887-1925, Costallat 1918, Breitkopf 1924, Salabert 1949, Henle 1987, Naegeli 1803 ...) | 25 publishers, 1803-1987 | see `downloads.md` | 292 / 250 | 1,332 | 1,332 | 2 (0.15 %), 1 false grand, 2 false joins (Haslinger 1835 1, Breitkopf Op. 12 1857 1) | thin to medium **curved** brace, connecting barline | **negative controls** (test / regression only) |
| Reichardt songs (earlier work, 23 pp.) | Berlin, 1819 | earlier batch | - | - | 56 | 53 (95 %) | thin straight, heavy double line | held out (earlier) |
| 7 early or poor files: Artaria Op. 106 1819, Schlesinger Op. 109 1821, Hoffmeister Op. 22 1800, Cappi Op. 27/1 1801 (1 of 15 pages labelled), Simrock Op. 31/2 1802 (3 pairs), Bureau Op. 54 1806, Diabelli Erlkoenig 1820s | 1800-1822 | see `downloads.md` | 77 / 2 | - | 4 | n/a | scans too blurred or dark for the staff detector (no staffs or odd staff counts) | unusable |

Counts above are over the pages that could be labelled; a grand pair that sits on an unlabelled page is not in the table. The 40 labelled crops of the Schott pool, of the concertos and of Cappi 1802 (and 15
crops of the Concert-Etudes) were looked at one by one (`figures/labelcheck_*.png`, green G = grand, blue S = same system, red - = separate, 'shipped' = the shipped decision): no wrong label among 135 crops (40 + 40 + 40 + 15).
The shipped model's 'S' on all grand Schott crops is the known failure (D25); on the concertos it reads the 'I' / 'II' labelled braces right and misses the unlabelled ones.

## 3. What this does and does not give

* **Same-edition experiment**: 164 labelled pages / 905 grand pairs of Schott 1917-18 other than the three test pieces (and 43 more pairs on the reserved Mazeppa pages). The Schott scans are all of one scanning
  series (Sibley, same scanner, same page geometry), so a model trained on them will be tested on a neighbour of its training scans (same brace, same scan, other music): it shows that the brace can be learned from
  real examples, **not** that it generalises to other editions. Hold out whole *pieces* (and keep the three test pieces and Mazeppa out), e.g. train on Etudes 1-3, 6-9 and the concertos, validate on 11, 12 and the Konzert-Etueden.
* **Transfer test**: there is **no second thin straight brace edition with a point**. The best available are Cappi 1802 (straight bracket with hooks; 40 / 46 missed; weak scan) and Reichardt 1819 (thin, straight, heavy
  double line; 53 / 56). Together with the 37 curved editions they test (a) whether a model trained on Schott fixes Cappi / Reichardt (transfer to other straight shapes) and (b) whether it keeps the curved editions at 100 % (no
  regression); both are in `split.tsv`. If the professor wants a real second thin-brace edition, it has to come from outside IMSLP's public scans (e.g. library scans of other Schott or Peters volumes of 1900-1930).
* Honest limits: the screening looked at 6-12 pages per edition (not whole volumes), the style column is my reading of rendered crops, grey early scans are barely usable, two files are not public domain (Henle 1987, Salabert 1949,
  only used as negative controls, not copied anywhere else), and 'systems' for the two-piano files counts a system once although it has two pairs of grand staves.

## Files

* `downloads.md` sha256, size, pages of every file; `split.tsv` role of every labelled group with the labelled page numbers; `table_raw.txt` the analysis output.
* `render_pages.sh` (pdftoppm 150 dpi; 600 dpi scans with a huge page box are scaled to 1415 px width), `extract.sh` / `extract_rev.sh` (detection + 96 x 96 crops with the code of `staff_rel_realbrace/scripts/extract_pairs.py`, worktree `run/rel_wt`,
  released segnet), `analyze.py` (labels from structure, shipped-model decisions, per-edition counts, writes `labels/<group>.npz` with crops, labels and shipped decisions), `labelcheck.py` (eye check sheets), `style_sheet.py`, `gen_downloads.py`.
* `figures/`: `labelcheck_schott_pool.png`, `labelcheck_concertos.png`, `labelcheck_concert_etudes.png`, `labelcheck_cappi1802.png`; page-margin sheets of the Schott files and of the screened editions (`pages_*.png`).
* Commands: `./render_pages.sh <name> <pdf> <pages>; ./extract.sh <name>; python analyze.py <name>[:k] ...` (k = staffs per system, default 2; `schott-concerto1:4`), run with `/Users/yiduoke/Documents/homr/.venv/bin/python`.
