#!/bin/bash
tmux kill-session -t lily 2>/dev/null
pkill -f "training/omr_datasets/convert_lilypond.py"; pkill -x lilypond; pkill -f musicxml2ly; sleep 2
echo "running converters: $(pgrep -fc "training/omr_datasets/convert_lilypond.py")"
