# Clean training indexes (2026-11-15)

Written next to each original as `index_clean.txt`; originals untouched. Octave round lists (`round*_train/val`, `holdout*`) also got `*_clean.txt` (same eval filter).

## Counts per set (image lines)

| set | lines before | duplicates dropped | eval matches dropped (scores) | lines after | clean file |
|---|---:|---:|---:|---:|---|
| grandstaff | 45635 | 0 (0 scores) | 1755 (15 scores) | 43880 | `/workspace/homr566/datasets/grandstaff/index_clean.txt` |
| pdmx | 199706 | 58137 (4676 scores) | 791 (27 scores) | 140778 | `/workspace/homr566/datasets/pdmx/index_clean.txt` |
| pdmx_hard | 92984 | 0 (0 scores) | 558 (19 scores) | 92426 | `/workspace/homr566/datasets/pdmx/hard/index_clean.txt` |
| lieder | 43149 | 0 (0 scores) | 0 (0 scores) | 43149 | `/workspace/homr566/datasets/Lieder-main/index_clean.txt` |
| asap | 5832 | 0 (0 scores) | 286 (9 scores) | 5546 | `/workspace/homr566/datasets/asap/index_clean.txt` |
| kern_scriabin | 1847 | 0 (0 scores) | 0 (0 scores) | 1847 | `/workspace/homr566/datasets/kern_scriabin/index_clean.txt` |
| lilypond | 47587 | 0 (0 scores) | 129 (4 scores) | 47458 | `/workspace/homr/datasets/lilypond/index_clean.txt` |
| lilypond_round2 | 17211 | 0 (0 scores) | 52 (1 scores) | 17159 | `/workspace/homr/datasets/lilypond_round2/index_clean.txt` |
| musescore_octave | 36036 | 0 (0 scores) | 92 (3 scores) | 35944 | `/workspace/homr/datasets/musescore_octave/index_clean.txt` |

Total clean lines: 428187

## P2: PDMX main vs hard

Source score id = file name prefix before `-<n>-<m>.png` (a trailing `-vrv` Verovio re-render is stripped, so both renders of a score match). Main: 199706 lines / 17905 scores; hard: 92984 lines / 6587 scores. 4676 scores are in both (all complexity 2), 58137 lines in each. Rule: keep in hard, drop from main. Of the 58137 main lines dropped as duplicates, 110 would also have been dropped as evaluation pieces (counted once, as duplicates). Hard is unchanged except for evaluation matches.

## P1: beam tokens (random 500 token files per set, drawn from the clean index, seed 7)

A beamable note is `note_<n>` with n >= 8. Beam state is the `beamStart|beamContinue|beamStop` part of the 5th field (slur/beam field; may be combined, e.g. `beamStart_slurStop`).

| set | files read | files with a beamable note | of those, files with a beam token | beamable notes | with beam token | share |
|---|---:|---:|---:|---:|---:|---:|
| grandstaff | 500 | 480 | 463 (96%) | 22568 | 16793 | 74.4% |
| pdmx | 500 | 404 | 373 (92%) | 8827 | 7169 | 81.2% |
| pdmx_hard | 500 | 467 | 449 (96%) | 19602 | 12556 | 64.1% |
| lieder | 500 | 426 | 307 (72%) | 9960 | 5547 | 55.7% |
| asap | 500 | 485 | 476 (98%) | 20728 | 16170 | 78.0% |
| kern_scriabin | 500 | 433 | 389 (90%) | 17012 | 9675 | 56.9% |
| lilypond | 500 | 447 | 0 (0%) | 15205 | 0 | 0.0% |
| lilypond_round2 | 417 | 381 | 0 (0%) | 15004 | 0 | 0.0% |
| musescore_octave | 500 | 396 | 0 (0%) | 9421 | 0 | 0.0% |

**The three octave sets (lilypond, lilypond_round2, musescore_octave) carry no beam tokens at all** (0 of 15k/15k/9k beamable notes): their token files predate the beam change and would need regenerating (or excluding) before run 1. Lieder shows a lower share because vocal lines are beamed only over melismas. In `lilypond_round2/index.txt`, 2806 of 17211 listed token files no longer exist on disk (later rounds overwrote `datasets/lilypond/flat`); those lines are kept in the clean file, not checked by me (83 of the 500 sampled files were missing and are not in the table).

## Evaluation matches dropped, per set

### grandstaff (1755 lines, 15 scores)

- Beethoven Op. 10 No. 1 mvt 3 (evaluation page): 204 lines, 1 scores
- Beethoven Op. 13 mvt 1: 342 lines, 1 scores
- Beethoven Op. 2 No. 2 mvt 1 (evaluation page): 28 lines, 1 scores
- Beethoven Op. 2 No. 3 (evaluation page, movement unknown): 904 lines, 4 scores
- Beethoven Op. 7 mvt 3 (evaluation page): 48 lines, 1 scores
- Mozart K. 309 mvt 1: 91 lines, 1 scores
- Mozart K. 331 mvt 1: 138 lines, 6 scores

Titles dropped:
- `beethoven/piano-sonatas/sonata02-1` 
- `beethoven/piano-sonatas/sonata03-1` 
- `beethoven/piano-sonatas/sonata03-2` 
- `beethoven/piano-sonatas/sonata03-3` 
- `beethoven/piano-sonatas/sonata03-4` 
- `beethoven/piano-sonatas/sonata04-3` 
- `beethoven/piano-sonatas/sonata05-3` 
- `beethoven/piano-sonatas/sonata08-1` 
- `mozart/piano-sonatas/sonata07-1` 
- `mozart/piano-sonatas/sonata11-1a` 
- `mozart/piano-sonatas/sonata11-1b` 
- `mozart/piano-sonatas/sonata11-1d` 
- `mozart/piano-sonatas/sonata11-1e` 
- `mozart/piano-sonatas/sonata11-1f` 
- `mozart/piano-sonatas/sonata11-1g` 

### pdmx (791 lines, 27 scores)

- Bach WTC BWV 848 (fugue+prelude): 61 lines, 2 scores
- Bach WTC BWV 852 (prelude): 80 lines, 2 scores
- Bach WTC BWV 854 (fugue+prelude): 50 lines, 3 scores
- Bach WTC BWV 857 (fugue): 76 lines, 2 scores
- Bach WTC BWV 858 (prelude): 60 lines, 2 scores
- Bach WTC BWV 864 (fugue): 34 lines, 1 scores
- Bach WTC BWV 865 (prelude): 120 lines, 3 scores
- Bach WTC BWV 872 (fugue): 55 lines, 2 scores
- Bach WTC BWV 876 (fugue): 42 lines, 1 scores
- Bach WTC BWV 883 (fugue): 81 lines, 2 scores
- Bach WTC BWV 890 (fugue): 17 lines, 1 scores
- Mussorgsky Pictures at an Exhibition: 79 lines, 5 scores
- Rachmaninoff Op. 23 No. 2 / Op. 3 No. 2: 36 lines, 1 scores

Titles dropped:
- `QmNa6KZb1ryFadjrbPKvbe3whqvEuyAXm1DU7SEo` bwv 854 the well-tempered clavier part i fuga ix | prelude and fugue in e major bwv 854 | j. s. bach
- `QmRD9SPMxYYeG3xhNtpRRru64nuyXcrJuMrEBMMc` la grande porte de kiev piano 8 mains | na | m.moussorgky | na | na
- `QmRNUNg6iT4uqwtfsWWqRNhv1uEwWKXQeqVvfQvq` bwv 872 the well-tempered clavier part ii fuga iii | prelude and fugue in c-sharp major bwv 872 | j.
- `QmRNaUMT3fUkhYCdxiz8BgWKYFkh97kKexUbFNZe` bwv 854: the well-tempered clavier book i - ix (a = 415 hz)- harpsichord sound | prelude and fugue i
- `QmSAsFaEoEXWEKtj64kwJVJHWGfebjnnQWKKMdTA` bwv 854 the well-tempered clavier part i praeludium ix | prelude and fugue in e major bwv 854 | j. s
- `QmSJkZLrUZtM7KhrRp5csnqQBBgnPBRJSTc5E7dZ` bwv 876: the well-tempered clavier book ii - vii (a = 415 hz) | prelude and fugue in e-flat major bw
- `QmSUDHGgsU29t731Aar6xWBZnkp2QLrs6mPQWMk8` sergei rachmaninoff: prelude op.3 no.2 in c-sharp minor | morceaux de fantaisie op.3 | sergei rachma
- `QmUD7YgdghgcdmAf82m5srUjvBjRekK4hiA12g8d` bwv 865 the well-tempered clavier part i praeludium xx | prelude and fugue in a minor bwv 865 | j. s
- `QmV3nmZehNmZdL4UMNwNr4VLePMnjaKq2ew2esUy` bwv 858: the well-tempered clavier book i - xiii (a = 415 hz) | prelude and fugue in f-sharp major b
- `QmWaB6hiNzPjgFMZBqXbBHXv3KM6axjqohRNiLcq` bwv 858: the well-tempered clavier book i - xiii (a = 415 hz) - harpsichord sound | prelude and fugu
- `QmWbBp8qjCE6Q7L3C3iJ17ZiCBq4FcRZKkLt4Xhr` bwv 857: the well-tempered clavier book i - xii (a = 415 hz) - harpsichord sound | prelude and fugue
- `QmXaMthjVguTmQDd1unpDZNuog6v6fxieUMWkHj9` pictures at an exhibition (promenade i) | pictures at an exhibition | na | modest mussorgsky | na
- `QmXoyCdexbybSrcdzoFUCcXoZiNu27KcKbGvbEBK` bwv 857: the well-tempered clavier book i - xii (a = 415 hz) | prelude and fugue in f minor bwv 857 
- `QmYU6q2UKHtWdYgdwiG3qME87dLLGvGP5esnPqzj` bwv 848 the well-tempered clavier part i praeludium iii | prelude and fugue in c-sharp major bwv 848
- `QmYe4apLQhK9nL5JxQ3457dq66MdREpmavv9LxUF` promenade iv | pictures at an exhibition | na | modest mussorgsky | na
- `QmZGH3ExzFtuHZ1L8UrUBfQ2z53WNmC9zG1FnoU3` bwv 865: the well-tempered clavier book i - xx (a = 415 hz) | prelude and fugue in a minor bwv 865 |
- `QmZvewKVjih7ySoPSqqMMkNTKSUEFfPfUj6KXika` bwv 890 the well-tempered clavier part ii fuga xxi | prelude and fugue in b-flat major bwv 890 | j. 
- `QmbrFo56yuFBSFwKJFzjsSh2m2EXAcV3jTmW4z8Z` bwv 883: the well-tempered clavier book ii - xiv (a = 415 hz) - harpsichord sound | prelude and fugu
- `QmcGVxPgXCz2Bi9uSrZWvvi6D134MCzdefmaWi9w` bilder einer ausstellung | na | modeste moussorgsky | na | promenade
- `QmcTqDsnkDzEG379sb7qEuCPUjQRMEiRDYRA128N` bwv 864: the well-tempered clavier book i - xix (a = 415 hz) | prelude and fugue in a major bwv 864 
- `QmckTmD1XYVogJQ8WYVTwYQRhSCDVG95EbyuSRQJ` bwv 872: the well-tempered clavier book ii - iii (a = 415 hz) | prelude and fugue in c-sharp major b
- `Qmd6XpcvfQJYWZFd5TESmSUeYmbTALMMErW9YSv8` bwv 852: the well-tempered clavier book i - vii (a = 415 hz) | prelude and fugue in e-flat major bwv
- `Qmd91e5hitp8eP3MrP85rSU2tajg6HgbYpLEnRhv` promenade | na | modeste mussorgsky | na | 2nd part
- `QmdWo18ehCso3gXAy1BpcJ7fWjisUKViTbPA7X93` bwv 848: the well tempered clavier i-iii - haspsichord sound | prelude and fugue in c-sharp major bw
- `QmeCG9PMYL6yYpkVhYrxrug6iSkHqWjSAEmQcS7M` bwv 883 the well-tempered clavier part ii fuga xiv | prelude and fugue in f-sharp minor bwv 883 | j.
- `QmeeUM3amVoKCRAmKaQ1AQASCxoRTLUGq85YJroH` bwv 865: the well-tempered clavier book i - xx (a = 415 hz) - harpsichord sound | prelude and fugue 
- `QmfHBXqK7sFJqyvX4G49CoAKY9Jd5E4b44eQFQAi` bwv 852 the well-tempered clavier part i praeludium vii | prelude and fugue in e-flat major bwv 852 

### pdmx_hard (558 lines, 19 scores)

- Bach WTC BWV 848 (fugue+prelude): 94 lines, 2 scores
- Bach WTC BWV 852 (prelude): 83 lines, 2 scores
- Bach WTC BWV 854 (fugue+prelude): 21 lines, 1 scores
- Bach WTC BWV 857 (fugue): 58 lines, 2 scores
- Bach WTC BWV 858 (prelude): 60 lines, 3 scores
- Bach WTC BWV 864 (fugue): 62 lines, 2 scores
- Bach WTC BWV 865 (prelude): 90 lines, 2 scores
- Brahms Op. 116 (evaluation pages; whole opus): 31 lines, 2 scores
- Mozart K. 309 mvt 1: 45 lines, 1 scores
- Mussorgsky Pictures at an Exhibition: 14 lines, 2 scores

Titles dropped:
- `QmQL1MKzhKgMynE9fbuuVWRGZSfMqMSb3nkuEoh6` prelude and fugue 13 - openwtc | na | na | na | bwv 858
- `QmQofdy6Lok6mVwuKYrFdoWmWQG7oc5HHmqcwTXv` prelude and fugue 12 - openwtc | na | na | na | bwv 857
- `QmQp4aYX7v68aZyxMwiVqw8fCAsAkweQoRi8rKQB` intermezzo (e major) op. 116 no. 4 | 7 fantasien op.116 | johannes brahms1833-1897 | johannes brahms
- `QmS4tEZneYPVEkRd8GfHijieDCLeVs5ZDLQdLNJU` prelude and fugue 19 - openwtc | na | na | na | bwv 864
- `QmUgYFhqprnmF5QujhEqcA8zPnePUdujuJV8CwvD` intermezzo op. 116 no. 2 (johannes brahms) | 7 fantasien op.116 | johannes brahms | johannes brahms 
- `QmWN4zCQ1SovDVE7mr4edFAy49A7bGE6xbdkvMcX` prelude and fugue 7 - openwtc | na | na | na | bwv 852
- `QmXJVv8tGXnP6s9m4G783uwuj9f9fgSyNHVd18ue` prelude and fugue 19 - openwtc | na | na | na | bwv 864
- `QmXWnuk1nFAaCpLEYoFXZMDExvbRuxVX6DRNzhFD` prelude and fugue 12 - openwtc | na | na | na | bwv 857
- `QmXkTz66CubAkyhY1vg3aQWutQjJixHwnMteCGSX` prelude and fugue 7 - openwtc | na | na | na | bwv 852
- `QmYWERoBPLQvgyuYQBVT5rifH4Txdg7ArctgXxzt` prelude and fugue 20 - openwtc | na | na | na | bwv 865
- `QmYXmg2noErG2MJVfpi5ieyRwRp8qi8DJRiXwV9f` sonate mozart n7 c m | piano sonata no. 7 in c k. 309 | wolfgang amadeus mozart | wolfgang amadeus m
- `QmZYyajNvNoD931nnSBVFGx74ZZr9hpx6pFoKWoW` prelude and fugue 20 - openwtc | na | na | na | bwv 865
- `QmZu65P8bp6WtCzEha5hD94Kmyb8PXUma9u4xEF1` testing the share option | na | modeste moussorgsky | na | promenade
- `QmaTPRtoLRrVLnLS61non25caA1jxGVJxpwikg2U` prelude and fugue 3 - openwtc | na | na | na | bwv 848
- `QmcfsSDhQWTey2zTA6wTExsyNh84oLTcnn1gatJR` prelude and fugue 9 - openwtc | na | na | na | bwv 854
- `Qmdd893Gosw45TVvtVhA465xBBFop3CxcF8MkrFy` bwv 858 - prelude | prelude and fugue in f-sharp major bwv 858 | j.s. bach | johann sebastian bach |
- `QmdiiASBeWrHABHJbGzGHxdrTnZpVQd8mpdfMvdn` al mundo paz. blanco y negro | al mundo paz. blanco y negro | modeste moussorgsky | sromero | promen
- `QmeGESzpQTyo6KnxgPd4MqyVvrRWpeYdSLa4zMnp` prelude and fugue 13 - openwtc | na | na | na | bwv 858
- `QmeNJyxUmbwMeazBoAbi6mY1XEY4i3QQ7UFBaAq8` prelude and fugue 3 - openwtc | na | na | na | bwv 848

### lieder
none

### asap (286 lines, 9 scores)

- Bach WTC BWV 854 (fugue+prelude): 26 lines, 2 scores
- Bach WTC BWV 857 (fugue): 29 lines, 1 scores
- Bach WTC BWV 864 (fugue): 23 lines, 1 scores
- Bach WTC BWV 865 (prelude): 10 lines, 1 scores
- Bach WTC BWV 876 (fugue): 20 lines, 1 scores
- Bach WTC BWV 883 (fugue): 25 lines, 1 scores
- Beethoven Op. 2 No. 2 mvt 1 (evaluation page): 65 lines, 1 scores
- Beethoven Op. 2 No. 3 (evaluation page, movement unknown): 88 lines, 1 scores

Titles dropped:
- `Bach_Fugue_bwv_854` 
- `Bach_Fugue_bwv_857` 
- `Bach_Fugue_bwv_864` 
- `Bach_Fugue_bwv_876` 
- `Bach_Fugue_bwv_883` 
- `Bach_Prelude_bwv_854` 
- `Bach_Prelude_bwv_865` 
- `Beethoven_Piano_Sonatas_2-1` 
- `Beethoven_Piano_Sonatas_3-1` 

### kern_scriabin
none

### lilypond (129 lines, 4 scores)

- Bach WTC BWV 848 (fugue+prelude): 33 lines, 1 scores
- Bach WTC BWV 854 (fugue+prelude): 22 lines, 1 scores
- Bach WTC BWV 864 (fugue): 30 lines, 1 scores
- Mussorgsky Pictures at an Exhibition: 44 lines, 1 scores

Titles dropped:
- `QmRD9SPMxYYeG3xhNtpRRru64nuyXcrJuMrEBMMc` la grande porte de kiev piano 8 mains | na | m.moussorgky | na | na
- `QmRNaUMT3fUkhYCdxiz8BgWKYFkh97kKexUbFNZe` bwv 854: the well-tempered clavier book i - ix (a = 415 hz)- harpsichord sound | prelude and fugue i
- `QmcTqDsnkDzEG379sb7qEuCPUjQRMEiRDYRA128N` bwv 864: the well-tempered clavier book i - xix (a = 415 hz) | prelude and fugue in a major bwv 864 
- `QmdWo18ehCso3gXAy1BpcJ7fWjisUKViTbPA7X93` bwv 848: the well tempered clavier i-iii - haspsichord sound | prelude and fugue in c-sharp major bw

### lilypond_round2 (52 lines, 1 scores)

- Mussorgsky Pictures at an Exhibition: 52 lines, 1 scores

Titles dropped:
- `QmRD9SPMxYYeG3xhNtpRRru64nuyXcrJuMrEBMMc` la grande porte de kiev piano 8 mains | na | m.moussorgky | na | na

### musescore_octave (92 lines, 3 scores)

- Liszt Liebestraum 3: 36 lines, 1 scores
- Mussorgsky Pictures at an Exhibition: 56 lines, 2 scores

Titles dropped:
- `Liebestraum_No._3_in_A_Major` liebestraum no. 3 in a major
- `QmRD9SPMxYYeG3xhNtpRRru64nuyXcrJuMrEBMMc` la grande porte de kiev piano 8 mains | na | m.moussorgky | na | na
- `QmYe4apLQhK9nL5JxQ3457dq66MdREpmavv9LxUF` promenade iv | pictures at an exhibition | na | modest mussorgsky | na

## Octave round lists (same filter)
| list | before | eval dropped | after |
|---|---:|---:|---:|
| lilypond/holdout_inserted.txt | 3009 | 0 | 3009 |
| lilypond/holdout_real.txt | 1387 | 0 | 1387 |
| lilypond/round3_train.txt | 110796 | 532 | 110264 |
| lilypond/round3_val.txt | 4000 | 30 | 3970 |
| lilypond/round4_train.txt | 130460 | 578 | 129882 |
| lilypond/round4_val.txt | 4000 | 30 | 3970 |
| lilypond/round5_train.txt | 131063 | 588 | 130475 |
| lilypond/round5_val.txt | 4000 | 30 | 3970 |
| lilypond_round2/holdout.txt | 1170 | 0 | 1170 |
| lilypond_round2/round2_train.txt | 91796 | 466 | 91330 |
| lilypond_round2/round2_val.txt | 4000 | 25 | 3975 |
