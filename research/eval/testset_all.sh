#!/bin/bash
# usage: testset_all.sh TAG WORKTREE
S=/Users/yiduoke/Documents/homr/run/scores/testset; X=/Users/yiduoke/Documents/homr/run/eval_run1/run_testset.sh
$X $1 $2 chopin-etude-op10-4 $S/chopin-etudes-op10-breitkopf.pdf 12 15
$X $1 $2 prokofiev-toccata $S/prokofiev-sarcasms-visions-dover.pdf 1 11
$X $1 $2 chopin-scherzo3 $S/chopin-scherzo3-op39-breitkopf.pdf 1 12
$X $1 $2 schumann-toccata $S/schumann-toccata-op7-peters.pdf 2 13
$X $1 $2 balakirev-islamey $S/balakirev-islamey-rahter.pdf 2 19
