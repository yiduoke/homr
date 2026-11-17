#!/bin/bash
# usage: testset_more.sh TAG WORKTREE   (second batch of test-set pieces; same steps as testset_all.sh)
# Pages are pre-rendered in eval_run1/pages/<piece>/ (150 dpi; Wanderer at 18 dpi = 150 dpi of its
# 600-dpi scan stored as 72 dpi; two shared pages whited out, see out/testset/README.md), so
# run_testset.sh skips its pdftoppm step.
S=/Users/yiduoke/Documents/homr/run/scores/testset; X=/Users/yiduoke/Documents/homr/run/eval_run1/run_testset.sh
$X $1 $2 beethoven-waldstein-1 $S/beethoven-waldstein-peters.pdf 1 14
$X $1 $2 beethoven-appassionata-1 $S/beethoven-appassionata-ue-schenker.pdf 1 15
$X $1 $2 beethoven-hammerklavier-4 $S/beethoven-hammerklavier-peters.pdf 30 46
$X $1 $2 bach-italian-concerto-2 $S/bach-italian-concerto-ue.pdf 6 9
$X $1 $2 bach-prelude-873 $S/bach-wtc2-bach-gesellschaft.pdf 16 17
$X $1 $2 bach-fugue-873 $S/bach-wtc2-bach-gesellschaft.pdf 18 19
$X $1 $2 haydn-hob16-49-1 $S/haydn-hob16-49-breitkopf1799.pdf 1 7
$X $1 $2 mozart-k475 $S/mozart-k475-schirmer.pdf 1 10
$X $1 $2 schubert-wanderer-3-4 $S/schubert-wanderer-peters.pdf 19 33
$X $1 $2 schubert-impromptu-d899-4 $S/schubert-impromptus-d899-breitkopf.pdf 27 36
$X $1 $2 schumann-kreisleriana-1 $S/schumann-kreisleriana-schirmer.pdf 2 5
$X $1 $2 chopin-etude-op25-10 $S/chopin-etudes-op25-peters.pdf 29 32
$X $1 $2 chopin-etude-op25-11 $S/chopin-etudes-op25-peters.pdf 33 39
$X $1 $2 chopin-polonaise-op53 $S/chopin-polonaise-op53-breitkopf.pdf 1 10
$X $1 $2 liszt-te-5 $S/liszt-transcendental-schott.pdf 29 37
$X $1 $2 liszt-te-10 $S/liszt-transcendental-schott.pdf 76 85
$X $1 $2 liszt-hr-6 $S/liszt-hungarian-rhapsody6-paderewski.pdf 1 11
$X $1 $2 liszt-sonata $S/liszt-sonata-schott.pdf 2 15
$X $1 $2 liszt-paganini-6 $S/liszt-paganini-etudes-4-6-breitkopf1851.pdf 11 22
$X $1 $2 scriabin-sonata-5 $S/scriabin-sonata5-muzgiz.pdf 1 18
$X $1 $2 debussy-reflets $S/debussy-images1-durand.pdf 3 9
$X $1 $2 debussy-pour-le-piano-1 $S/debussy-pour-le-piano-fromont.pdf 3 13
$X $1 $2 ravel-alborada $S/ravel-miroirs-demets.pdf 32 44
