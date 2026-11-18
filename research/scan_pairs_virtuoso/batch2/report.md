| pid | piece | group | strong | hard | octave-verified | quarantined | pitch F1 | pitch+onset F1 |
|---|---|---|---|---|---|---|---|---|
| N1 | Liszt Concert Etude S.145/1 Waldesrauschen | train | 37 | 2 | 3 | 3 | 0.957 | 0.464 |
| N2 | Liszt Concert Etude S.145/2 Gnomenreigen | val | 41 | 1 | 2 | 1 | 0.968 | 0.904 |
| N3 | Liszt Venezia e Napoli 1 Gondoliera | train | 26 | 0 | 0 | 7 | 0.968 | 0.727 |
| N4 | Chopin Etude Op.10/5 | val | 20 | 0 | 1 | 3 | 0.979 | 0.612 |
| N5 | Chopin Etude Op.10/7 | train | 18 | 0 | 0 | 0 | 0.988 | 0.986 |
| N6 | Chopin Etude Op.10/8 | train | 21 | 0 | 7 | 3 | 0.991 | 0.981 |
| N7 | Chopin Etude Op.25/8 | train | 14 | 0 | 0 | 3 | 0.977 | 0.715 |
| N8 | Chopin Berceuse Op.57 | train | 21 | 0 | 4 | 5 | 0.973 | 0.792 |
| N9 | Chopin Sonata 2 mvt 1 | train | 32 | 0 | 2 | 8 | 0.961 | 0.750 |
| N10 | Chopin Sonata 2 mvt 3 Marche funebre | train | 15 | 1 | 0 | 2 | 0.977 | 0.897 |
| N11 | Beethoven Op.81a mvt 3 | val | 40 | 0 | 6 | 7 | 0.991 | 0.954 |
| N12 | Beethoven Op.81a mvt 1 | val | 30 | 0 | 4 | 3 | 0.979 | 0.938 |
| N13 | Beethoven Op.7 mvt 1 | train | 61 | 0 | 0 | 5 | 0.996 | 0.946 |
| N14 | Beethoven Op.27/1 mvt 4 | train | 52 | 0 | 0 | 3 | 0.995 | 0.961 |
| N15 | Beethoven Op.31/1 mvt 1 | train | 36 | 0 | 0 | 46 | 0.993 | 0.964 |
| N16 | Rachmaninoff Prelude Op.23/4 | train | 19 | 0 | 1 | 1 | 0.982 | 0.584 |
| N17 | Rachmaninoff Prelude Op.32/5 | train | 17 | 0 | 0 | 2 | 0.982 | 0.238 |
| N18 | Rachmaninoff Prelude Op.32/10 | train | 13 | 0 | 0 | 4 | 0.991 | 0.645 |
| N19 | Ravel Miroirs 3 Une barque sur l'ocean | demets | 42 | 1 | 4 | 37 | 0.937 | 0.412 |
| N20 | Schubert Impromptu D.935/3 | train | 28 | 0 | 0 | 21 | 0.996 | 0.677 |
| N21 | Schumann Arabeske Op.18 | train | 35 | 0 | 0 | 2 | 0.962 | 0.887 |
| NR1 | Chopin Etude Op.10/10 (reserve) | train | 23 | 0 | 0 | 1 | 0.986 | 0.755 |
| NR2 | Schubert Impromptu D.935/1 (reserve) | train | 62 | 0 | 0 | 10 | 0.991 | 0.953 |

| group | strong | hard | octave-verified | quarantined | kept | pitch F1 | pitch+onset F1 |
|---|---|---|---|---|---|---|---|
| train | 530 | 3 | 17 | 126 | 550 | 0.982 | 0.811 |
| val | 131 | 1 | 13 | 14 | 145 | 0.980 | 0.886 |
| demets | 42 | 1 | 4 | 37 | 47 | 0.937 | 0.412 |

all kept crops 742: pitch F1 0.979 (median 1.000), pitch+onset F1 0.801 (median 0.981)

quarantine reasons (a crop can have several; total 177):
- not music of the piece (before start / after end): 52
- duration/tuplet not representable (no token): 31
- rhythm: token sum differs from MusicXML (volta/repeat split, cadenza): 22
- ledger lines > 5 (trainer filter): 21
- octave review: not admitted (label wrong / edition difference / partial): 20
- rhythm: MusicXML bar longer than the meter: 12
- bar mismatch: 10
- alignment ambiguous: 9
- trainer filter (vocabulary/length): 6
- edition/key mismatch: 3
- crop not one grand staff: 2
- wrong by eye: 2

octave roles of kept crops:
train {'kept': 550, 'has_8va_token': 73, 'start_inside_8va': 28, 'continue_through_8va (starts inside, no stop)': 12, 'end_an_8va (starts inside, stop in crop)': 16, 'open_at_end (continues into next system)': 29, 'bracket starts and stops in the crop': 30}
val {'kept': 145, 'has_8va_token': 62, 'start_inside_8va': 30, 'continue_through_8va (starts inside, no stop)': 13, 'end_an_8va (starts inside, stop in crop)': 17, 'open_at_end (continues into next system)': 33, 'bracket starts and stops in the crop': 21}
demets {'kept': 47, 'has_8va_token': 20, 'start_inside_8va': 4, 'continue_through_8va (starts inside, no stop)': 3, 'end_an_8va (starts inside, stop in crop)': 1, 'open_at_end (continues into next system)': 4, 'bracket starts and stops in the crop': 15}
ALL {'kept': 742, 'has_8va_token': 155, 'start_inside_8va': 62, 'continue_through_8va (starts inside, no stop)': 28, 'end_an_8va (starts inside, stop in crop)': 34, 'open_at_end (continues into next system)': 66, 'bracket starts and stops in the crop': 66}

eye check rows: 53
