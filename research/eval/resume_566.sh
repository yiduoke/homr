#!/bin/bash
# resume of the 566 pass for the second batch (the first helper was cancelled after mozart-k475), then Petrushka with both models
S=/Users/yiduoke/Documents/homr/run/scores/testset; X=/Users/yiduoke/Documents/homr/run/eval_run1/run_testset.sh; WT566=/Users/yiduoke/Documents/homr/run/octave_wt; WTR=/Users/yiduoke/Documents/homr/run/acc_wt
$X 566 $WT566 schubert-wanderer-3-4 $S/schubert-wanderer-peters.pdf 19 33
$X 566 $WT566 schubert-impromptu-d899-4 $S/schubert-impromptus-d899-breitkopf.pdf 27 36
$X 566 $WT566 schumann-kreisleriana-1 $S/schumann-kreisleriana-schirmer.pdf 2 5
$X 566 $WT566 chopin-etude-op25-10 $S/chopin-etudes-op25-peters.pdf 29 32
$X 566 $WT566 chopin-etude-op25-11 $S/chopin-etudes-op25-peters.pdf 33 39
$X 566 $WT566 chopin-polonaise-op53 $S/chopin-polonaise-op53-breitkopf.pdf 1 10
$X 566 $WT566 liszt-te-5 $S/liszt-transcendental-schott.pdf 29 37
$X 566 $WT566 liszt-te-10 $S/liszt-transcendental-schott.pdf 76 85
$X 566 $WT566 liszt-hr-6 $S/liszt-hungarian-rhapsody6-paderewski.pdf 1 11
$X 566 $WT566 liszt-sonata $S/liszt-sonata-schott.pdf 2 15
$X 566 $WT566 liszt-paganini-6 $S/liszt-paganini-etudes-4-6-breitkopf1851.pdf 11 22
$X 566 $WT566 scriabin-sonata-5 $S/scriabin-sonata5-muzgiz.pdf 1 18
$X 566 $WT566 debussy-reflets $S/debussy-images1-durand.pdf 3 9
$X 566 $WT566 debussy-pour-le-piano-1 $S/debussy-pour-le-piano-fromont.pdf 3 13
$X 566 $WT566 ravel-alborada $S/ravel-miroirs-demets.pdf 32 44
$X run2s7 $WTR stravinsky-petrushka x.pdf 1 37
$X 566 $WT566 stravinsky-petrushka x.pdf 1 37
bash /Users/yiduoke/Documents/homr/run/eval_run1/score_more.sh bach-fugue-873 bach-italian-concerto-2 bach-prelude-873 beethoven-appassionata-1 beethoven-hammerklavier-4 beethoven-waldstein-1 haydn-hob16-49-1 mozart-k475 schubert-wanderer-3-4 schubert-impromptu-d899-4 schumann-kreisleriana-1 chopin-etude-op25-10 chopin-etude-op25-11 chopin-polonaise-op53 liszt-te-5 liszt-te-10 liszt-hr-6 liszt-sonata liszt-paganini-6 scriabin-sonata-5 debussy-reflets debussy-pour-le-piano-1 ravel-alborada stravinsky-petrushka
echo ALL_DONE
