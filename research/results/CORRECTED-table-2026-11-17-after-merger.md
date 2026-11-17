# Corrected test-set table after the merger fixes, 2026-11-17

Visible notes only (`print-object="no"` and invisible noteheads are not counted). Scriabin is scored against its reference without the stray 47-note second part (original kept). **After-merger** = `merge_pages.py` keeps the simultaneous same-name parts of a page apart and gives the part with fewer bars on a page rests for the missing bars at the end of that page (the lost bars sit mid-page and cannot be located), so both hands have the same bars per page. This affects only liszt-sonata, liszt-te-5 and liszt-te-10 (tag `T_am`); the Schott staves are still not joined as grand staffs, that is handled separately. Run B has only its final files locally: not re-merged, its Schott rows keep the old doubled bars. **Petrushka is provisional**: it is scored staff-ignored with per-staff bar alignment in the staff-sensitive column (58.3), the pooled column uses one joint alignment (79.2) because the reference has three staves and ours two; the pooled figure is not verified. Rendered columns use the earlier outputs (not re-merged).

Staff-sensitive pitch F1 % (pitch inventory, timing ignored), with pitch+onset in brackets. Pooled-staff scores and bar counts: `POOLED-table-2026-11-17-after-merger.md`.

| piece | rendered (released) | scan released | scan run B | scan control s7 | scan control s11 | scan harder-data s7 | scan harder-data s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.9 (95.6) | 99.6 (94.5) | 99.6 (97.1) | 99.7 (96.5) | 99.2 (95.6) | 99.6 (95.1) | 99.6 (95.1) |
| bach-italian-concerto-2 | 100.0 (100.0) | 98.9 (94.2) | 99.0 (98.2) | 98.9 (98.7) | 99.0 (97.8) | 99.1 (93.5) | 98.9 (95.0) |
| bach-prelude-873 | 98.7 (94.9) | 99.4 (97.2) | 99.3 (97.3) | 99.3 (97.2) | 98.9 (96.8) | 99.2 (96.3) | 99.4 (96.6) |
| beethoven-appassionata-1 | 98.3 (89.7) | 98.8 (91.0) | 97.6 (88.5) | 98.8 (90.2) | 98.9 (90.8) | 99.0 (90.6) | 98.6 (89.6) |
| beethoven-hammerklavier-4 | 97.7 (90.5) | 89.5 (83.0) | 89.3 (83.3) | 89.6 (83.3) | 89.4 (82.0) | 89.7 (83.2) | 89.5 (83.4) |
| beethoven-waldstein-1 | 99.0 (94.1) | 94.2 (90.9) | 94.1 (91.0) | 94.3 (88.7) | 94.2 (88.4) | 94.3 (90.3) | 94.0 (89.2) |
| chopin-etude-op10-4 | 97.9 (97.9) | 94.8 (93.1) | 94.6 (94.0) | 94.8 (92.8) | 95.1 (93.5) | 94.6 (91.4) | 94.7 (91.6) |
| chopin-etude-op25-10 | 99.1 (76.8) | 96.0 (72.3) | 94.8 (74.4) | 96.3 (68.6) | 97.1 (71.2) | 96.1 (76.1) | 95.4 (74.0) |
| chopin-etude-op25-11 | 94.4 (59.3) | 88.5 (53.4) | 86.4 (50.9) | 88.9 (55.4) | 89.1 (54.3) | 87.5 (47.5) | 88.8 (53.0) |
| chopin-polonaise-op53 | 95.3 (83.7) | 89.0 (71.4) | 88.3 (78.8) | 89.4 (73.6) | 90.0 (75.9) | 89.3 (69.9) | 89.6 (72.9) |
| chopin-scherzo3 | 97.1 (96.0) | 91.8 (89.6) | 89.3 (87.3) | 91.9 (89.6) | 90.3 (88.5) | 91.4 (89.6) | 91.6 (89.7) |
| debussy-pour-le-piano-1 | 95.0 (81.7) | 91.8 (77.4) | 82.9 (69.6) | 85.5 (74.3) | 84.9 (74.1) | 90.4 (78.0) | 91.9 (78.6) |
| debussy-reflets | 85.7 (46.6) | 85.2 (47.7) | 85.8 (50.2) | 85.9 (47.3) | 85.6 (48.0) | 85.9 (50.1) | 84.8 (50.0) |
| haydn-hob16-49-1 | 99.6 (98.3) | 95.1 (86.8) | 92.5 (86.8) | 92.6 (86.3) | 95.4 (87.4) | 94.8 (87.2) | 94.6 (87.1) |
| liszt-hr-6 | 86.2 (72.9) | 91.8 (81.8) | 89.0 (78.9) | 89.5 (79.2) | 90.6 (79.2) | 92.1 (81.7) | 91.8 (81.8) |
| liszt-paganini-6 | 93.7 (72.8) | 90.7 (63.8) | 88.2 (60.4) | 89.9 (62.0) | 90.3 (63.2) | 89.1 (63.6) | 91.0 (64.2) |
| liszt-sonata * | 96.8 (91.2) | 81.0 (66.0) | 49.8 (38.5) | 78.6 (62.7) | 81.5 (66.5) | 78.8 (63.0) | 81.5 (66.3) |
| liszt-te-10 * | 95.0 (53.6) | 79.1 (31.7) | 52.2 (18.0) | 79.2 (32.6) | 77.5 (31.7) | 79.6 (32.5) | 80.2 (33.3) |
| liszt-te-5 * | 91.9 (81.1) | 77.0 (62.3) | 50.2 (37.5) | 78.5 (61.9) | 77.4 (61.3) | 76.7 (61.0) | 80.6 (62.5) |
| mozart-k475 | 99.4 (96.7) | 92.0 (65.2) | 90.3 (73.5) | 91.3 (68.6) | 91.1 (68.0) | 92.6 (66.4) | 91.2 (65.5) |
| prokofiev-toccata | 92.0 (81.0) | 92.8 (82.3) | 90.8 (81.0) | 92.2 (81.2) | 93.2 (82.5) | 92.4 (82.6) | 93.3 (84.2) |
| ravel-alborada | 90.7 (67.1) | 81.7 (59.7) | 81.0 (57.2) | 81.6 (60.5) | 81.1 (60.1) | 82.2 (60.4) | 81.1 (57.6) |
| schubert-impromptu-d899-4 | 99.2 (99.2) | 96.7 (95.8) | 96.3 (94.8) | 96.7 (95.7) | 96.5 (95.4) | 96.5 (95.4) | 96.5 (95.4) |
| schubert-wanderer-3-4 | 98.5 (96.1) | 94.9 (93.5) | 94.7 (92.3) | 94.8 (93.2) | 94.9 (93.7) | 94.9 (93.7) | 94.9 (93.6) |
| schumann-kreisleriana-1 | 97.5 (80.5) | 95.8 (71.4) | 94.9 (65.3) | 95.5 (70.5) | 96.7 (72.0) | 96.3 (73.0) | 96.5 (72.5) |
| schumann-toccata | 98.3 (90.1) | 91.2 (82.5) | 91.4 (82.3) | 90.4 (80.5) | 91.8 (82.4) | 91.2 (82.1) | 91.6 (82.6) |
| scriabin-sonata-5 | 95.7 (75.4) | 89.1 (73.2) | 88.9 (74.0) | 90.1 (74.1) | 89.5 (72.9) | 90.6 (74.7) | 90.8 (74.3) |
| stravinsky-petrushka (provisional) | 73.3 (56.7) | 58.3 (43.1) | 56.3 (41.7) | 58.1 (43.4) | 58.3 (43.5) | 58.3 (44.0) | 58.2 (43.5) |
| **mean** | 95.2 (82.8) | 90.2 (75.5) | 86.0 (73.0) | 89.7 (75.3) | 89.9 (75.6) | 90.1 (75.5) | 90.4 (75.8) |
| **mean without Petrushka** | 96.0 (83.8) | 91.3 (76.7) | 87.1 (74.1) | 90.9 (76.5) | 91.1 (76.8) | 91.2 (76.6) | 91.6 (77.0) |
