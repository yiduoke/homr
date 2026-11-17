# Evaluation pieces removed from every training source (2026-11-15)

Matching: PDMX / Lieder / octave sets by composer + title text from PDMX.csv (title, song_name, composer_name, artist_name, subtitle) and OpenScore Lieder folder names; GrandStaff by kern path (composer/collection/work); ASAP and Scriabin by folder name; octave sets by the PDMX / Lieder id behind each file (or their source file name). Rules are in /workspace/clean_index/eval_rules.py; phrases in phrases.txt (copy of training/omr_datasets/pdmx_exclude_test_pieces.txt). Matches were reviewed against a near-miss scan (same composers, no hit) to check for spelling variants.

## A. Phrases already excluded (pdmx_exclude_test_pieces.txt, 21 pieces)
Liszt La Campanella (Paganini Etude 3), Mazeppa, Liebestraum 3, Mephisto Waltz 1, Hungarian Rhapsody 2, Totentanz; Mussorgsky Pictures at an Exhibition (all movements, also French/German titles); Ravel Jeux d eau, Gaspard de la nuit / Scarbo; Chopin Scherzo 1 Op. 20, Ballade 4 Op. 52; Debussy L isle joyeuse; Rachmaninoff Op. 23 No. 2 and Op. 3 No. 2; Scriabin Op. 8 No. 12, Op. 30 (and Sonata 4). Added: Mussorgsky + Pictures movement name without "Pictures" in the title (e.g. "La grande porte de Kiev").

## B. Five reference movements
- Bach WTC I Prelude and Fugue No. 3 C-sharp major, BWV 848. Text rule: BWV 848, or C-sharp major + prelude/fugue + Bach.
- Mozart Sonata K. 331 movement 1 (theme and variations). Text: K./KV 331 unless the title names another movement (Alla Turca / Turkish March / Rondo / 2nd, 3rd are kept). GrandStaff: sonata11-1a..1g.
- Mozart Sonata K. 309 movement 1. GrandStaff: sonata07-1.
- Beethoven Sonata Op. 13 movement 1. Text: Pathetique / Op. 13 unless another movement is named (the Adagio cantabile is kept). GrandStaff: sonata08-1.

## C. Stravinsky Petrushka (any arrangement)
Text rule petrushka / petrouchka / petrouchka variants. No hits in any set.

## D. Pages in the real test set (run/scores/real/inventory.csv)
Pieces in the inventory that are whole-piece evaluation items: Liszt Liebestraum 3, Hungarian Rhapsody 2, Mephisto Waltz 1, Mazeppa, La Campanella, Totentanz; Chopin Scherzo 1; Ravel Scarbo, Jeux d eau; Debussy L isle joyeuse; Rachmaninoff Op. 23 No. 2; Scriabin Etude Op. 8 No. 12, Sonata 4 Op. 30; Mussorgsky Pictures; Brahms Op. 116 (all of A, except Brahms below). The controls were identified by looking at the page PNGs (and OCR of the source PDFs):

| page | piece on the page | how identified | excluded |
|---|---|---|---|
| bach-wtc1-schirmer p030 | Fugue III C-sharp major (end), BWV 848 | 7 sharps, printed p. 17, final bar | BWV 848 prelude+fugue (also reference B) |
| bach-wtc1-schirmer p045 | Prelude VII E-flat, BWV 852 | printed heading "Preludio VII" | BWV 852 prelude (fugue kept) |
| bach-wtc1-schirmer p060 | Fugue IX E major (end), BWV 854 | 4 sharps, final bar; next page (printed 48) begins "Preludio X" | BWV 854 prelude+fugue (medium confidence) |
| bach-wtc1-schirmer p075 | Prelude XIII F-sharp, BWV 858 | heading "Preludio XIII" | BWV 858 prelude |
| bach-wtc1-schirmer p105 | Prelude XX A minor, BWV 865 | heading "Preludio XX" | BWV 865 prelude |
| bach-wtc2-schirmer p025 / p045 / p085 / p125 | Fuga III (C-sharp), VII, XIV, XXI | OCR headings | BWV 872, 876, 883, 890 fugues |
| bach-wtc-novello p020 | Fugue III C-sharp | printed heading "FUGUE III" | BWV 848 (already) |
| bach-wtc-novello p050 | Prelude IX E major | heading "PRELUDE IX" | BWV 854 |
| bach-wtc-novello p065 | Fugue XII F minor | printed p. 57, 4 flats, bar numbers 20-30; inferred from position (medium) | BWV 857 fugue |
| bach-wtc-novello p095 | Fugue XIX A major (end) | printed p. 87, 3 sharps, final bar; inferred (medium) | BWV 864 fugue |
| beethoven-sonatas-schirmer p030 | Op. 2 No. 2, movement 1 | printed "SONATA Op.2 No 2 Allegro vivace" | Op. 2 No. 2 mvt 1 |
| beethoven-sonatas-schirmer p070 | Op. 2 No. 3 (movement unknown) | printed p. 60, no key signature, between Op. 2/2 and Op. 7 (inferred, low-medium) | all movements of Op. 2 No. 3 |
| beethoven-sonatas-schirmer p090 | Op. 7 movement 3, "Minore" | 3/4, 6 flats, "Minore" (inferred, medium) | Op. 7 mvt 3 |
| beethoven-sonatas-schirmer p110 | Op. 10 No. 1 movement 3 | printed p. 100, "Finale. Prestissimo", cut time, 3 flats (inferred, medium) | Op. 10 No. 1 mvt 3 |
| brahms-op116-breitkopf p006, p008 | Op. 116 No. 2 Intermezzo | printed heading "2. Intermezzo" | whole Op. 116 |
| brahms-op116-breitkopf p010, p012 | Op. 116 No. 3 Capriccio (G minor) | key signature, ends with final bar | whole Op. 116 |
| brahms-op116-breitkopf p014 | Op. 116 No. 4 (or 5), E major | key signature, no heading | whole Op. 116 |
| brahms-op116-breitkopf p018 | Op. 116 No. 6 Intermezzo | heading "6. Intermezzo" | whole Op. 116 |
| brahms-op116-breitkopf p022 | Op. 116 No. 6 end or No. 7, 6/8 (unsure) | no heading | whole Op. 116 |

Not whole collections: Bach WTC and Beethoven sonatas are excluded only for the movements above. Bach prelude vs fugue is decided from the title field (a score titled only "Fuga ..." is kept when only the prelude is evaluated); PDMX scores whose title says "prelude and fugue" are excluded when either is evaluated. Brahms is excluded as the whole Op. 116 because the page evidence does not pin down all pieces.

## E. Polish Scores and SMB
- btrkeks/polish-scores (112 pages): the dataset has only image, kern and xml; no composer or title. Pages look like 19th-century Polish editions (e.g. Katski Obertas, Chopin-style pieces). Metadata matching is impossible. I checked content instead: 12-note pitch n-grams of every page against all GrandStaff kern files; the best page shares 8 of 387 grams (Chopin Prelude 15, a repeated-note passage) and the others fewer, so no sign of a copy. PDMX, Lieder, ASAP and the octave sets were NOT content-checked against Polish Scores.
- PRAIG/SMB: gated on Hugging Face, no token on the box; its piece list could not be read. Nothing excluded for SMB. Needs the owner (login) or a list of SMB titles.

## F. Found in which sets (lines dropped)
See report.md. Summary: GrandStaff Beethoven (Op. 13/1, Op. 2/2 mvt 1, Op. 2/3 all movements, Op. 7/3, Op. 10/1 mvt 3) and Mozart (K. 331/1 theme+variations, K. 309/1); PDMX main and hard: many Bach WTC pairs, Mussorgsky Pictures, Rachmaninoff Op. 3 No. 2, Brahms Op. 116, Mozart K. 309; ASAP: Bach BWV 854, 857, 864, 865, 876, 883 and Beethoven sonatas 2-1 and 3-1; octave sets: Bach, Mussorgsky, Liszt Liebestraum 3; Lieder and Scriabin: none.
