#!/bin/bash
# pull_d30.sh TAG... : page XML and homr.log of the box runs to the laptop (eval_run1/testset/<tag>/<piece>/)
R=/Users/yiduoke/Documents/homr/run
for tag in "$@"; do for piece in liszt-sonata liszt-te-5 liszt-te-10 liszt-te-4-schott; do
  mkdir -p $R/eval_run1/testset/$tag/$piece
  ssh vast-homr5 "cd $R/eval_run1/testset/$tag/$piece && tar -c page-xml homr.log" 2>/dev/null | tar -x -C $R/eval_run1/testset/$tag/$piece
done; done
