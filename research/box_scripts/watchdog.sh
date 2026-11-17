#!/bin/bash
# A crashed pool worker makes a converter wait forever (fixed upstream only on
# feature/beams). If a converter is running but nothing under datasets/ or its log
# changed for 20 minutes, interrupt it so its index is flushed and the next one starts.
L=/workspace/logs/driver.log
while [ "$(grep -c "^END" /workspace/logs/status.log)" -lt 5 ]; do
  sleep 120
  P=$(pgrep -f "python training/omr_datasets/convert_" | head -1)
  [ -z "$P" ] && continue
  recent=$(find /workspace/homr/datasets /workspace/logs -newermt "-20 min" -type f 2>/dev/null | head -1)
  if [ -z "$recent" ]; then
    echo "$(date -u +%FT%TZ) WATCHDOG: converter stalled 20 min, interrupting" >> $L
    pkill -INT -f "python training/omr_datasets/convert_"; sleep 60
    pkill -KILL -f "python training/omr_datasets/convert_"
  fi
done
