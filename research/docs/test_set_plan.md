# Real-scan test set: piece list (2026-11-16; swaps for virtuosity agreed with the owner)

Each entry: a few pages (3-5) of a real IMSLP scan of a standard edition; reference from ASAP
(expert MusicXML, github.com/fosfrancesco/asap-dataset), KernScores (expert kern, scans already
paired), or a Claude transcription checked by the owner. Every piece here is removed from all
training data. Pieces already in the old test set are marked "have".

| Composer | Piece | Reference | Status |
|---|---|---|---|
| Rameau | Les Cyclopes (or La Poule) | Claude + owner | to download |
| Bach | WTC II Prelude and Fugue BWV 873 (C# minor) or 891 | ASAP | to download |
| Bach | Italian Concerto, 3rd mvt | ASAP | to download |
| Scarlatti | 2 sonatas from KernScores (with scans) | KernScores | have scans (box) |
| Haydn | Sonata Hob. XVI:49 (ASAP 49-1) | ASAP | to download |
| Clementi | Gradus ad Parnassum, a fast étude (or Sonata Op. 25 No. 5) | Claude + owner | to download |
| Mozart | Fantasia K. 475 | ASAP | to download |
| Mozart | K. 331, K. 309 | KernScores | have |
| Beethoven | Waldstein 1st mvt (21-1); Appassionata 1st mvt (23-1); Hammerklavier fugue (29-4) | ASAP | downloaded / downloading |
| Beethoven | Pathetique 1st mvt | KernScores | have |
| Schubert | Wanderer Fantasy; Impromptu D. 899/4 | ASAP | to download |
| Schumann | Toccata Op. 7; Kreisleriana No. 1 | ASAP | to download |
| Mendelssohn | Rondo capriccioso Op. 14 | Claude + owner | to download |
| Chopin | Etude Op. 10/4 (done); Op. 25/10 and 25/11; Scherzo No. 3 (done); Polonaise Op. 53 | ASAP | downloading |
| Chopin | Ballade No. 4 | Claude | have |
| Liszt | Transcendental Etudes No. 5 and 10; Hungarian Rhapsody No. 6; Sonata in B minor; Paganini Etude No. 6 | ASAP | downloading |
| Liszt | Mazeppa (real scan), La Campanella | Claude | have |
| Brahms | Paganini Variations Op. 35 (Op. 118/2 dropped: slow) | Claude + owner | to download |
| Grieg | Wedding Day at Troldhaugen | Claude + owner | to download |
| Tchaikovsky | Dumka Op. 59 (or Concerto No. 1 solo cadenza) | Claude + owner | to download |
| Rachmaninoff | Prelude Op. 23/2 (or an Etude-tableau); ASAP 23/6 and 32/10 dropped: lyrical | Claude + owner | to download |
| Rachmaninoff | Prelude Op. 3/2 | Claude | have |
| Balakirev | Islamey | ASAP | to download |
| Glinka-Balakirev | The Lark | ASAP | to download |
| Scriabin | Sonata No. 5 (ASAP); Etude Op. 8/12 (Claude + owner; 8/11 dropped: slow) | ASAP / Claude | downloading |
| Mussorgsky | Pictures (pages already in the bracket test set) | Claude + owner | have scans |
| Albeniz | Iberia: El Albaicin (or Triana) | Claude + owner | to download |
| Saint-Saens | Etude Op. 52/6 "en forme de valse" (or Op. 111/6 Toccata) | Claude + owner | to download |
| Debussy | Reflets dans l'eau; Pour le piano, Prelude | ASAP | to download |
| Ravel | Alborada del gracioso | ASAP | to download |
| Prokofiev | Toccata Op. 11 | ASAP | to download |
| Stravinsky | Petrushka, Three Movements (whole scan, 37 pages) | Claude transcription (2026-11-16, whole piece, 627 bars x 3 staves; UNCHECKED, owner spot-check by ear needed) | have scan + reference |
| Bartok | Allegro barbaro | Claude + owner | to download |
| Shostakovich | Prelude and Fugue Op. 87 No. 15 in D-flat (owner's pick) | Claude + owner | scan from PML-Asia in scores/testset/private/ (non-PD US/EU/CA; never published) |
| Ligeti | Etude No. 1 "Desordre" | Claude + owner | dropped 2026-11-16 (copyrighted, no copy on hand; 20th century covered by Prokofiev, Stravinsky, Bartok, Shostakovich) |
| Glass | Metamorphosis One (or an Etude) | Claude + owner | dropped 2026-11-16 (copyrighted, no copy on hand; 20th century covered by Prokofiev, Stravinsky, Bartok, Shostakovich) |

Totals: about 25 ASAP references (no transcription), ~5 KernScores/old, ~12 Claude + owner.
Reference/edition check: same automatic pitch-agreement test used for the Ballade (target >95%),
plus a spot check by eye; mismatched editions get a different scan.

Rule: pick each composer's hardest available piece; Haydn, Mozart, Bach and the Schubert Impromptu stay as
moderate era anchors. Every piece here must be added to all training exclusion lists (PDMX, ASAP,
GrandStaff, Lieder, Scriabin) before the next training run.

Petrushka first look (2026-11-16, score_notes, not like-for-like: ours joint alignment with extra staves remapped, 566 per staff):
full-match F1 ours 38.8 / 566 46.2; pitch inventory 58.4 / 71.8; 585 of 627 bars align. The reference has 3 staves per
system and our output 2, so 3-staff systems are a layout case still to handle (the `layout` merge covers only 4-staff
systems). Rerun both models with the frozen pipeline (and the layout code) before quoting these.
