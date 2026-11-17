#!/bin/bash
# usage: chain_slot.sh <pid to wait for> then commands...  (runs the given job lines one after the other)
W=$1; shift
while kill -0 $W 2>/dev/null; do sleep 20; done
for job in "$@"; do bash -c "$job"; done
