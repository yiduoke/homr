#!/bin/bash
# Pilot automation (D29). Runs on the LAPTOP (nohup, under caffeinate), drives the boxes through ssh and tmux.
# For each of the four pilot models, as soon as "<NAME> DONE" is in /workspace/logs/pilot/status.log on vast-homr4:
#   1. export to ONNX on vast-homr4 (tmux session pexp_<NAME>, nice 10, CPU only, 2 threads; pilot_export.sh; run3 recipe, byte-identical to run3's export on the test)
#   2. copy the ONNX to vast-homr5 through the laptop (cloud2_models.sh; sizes verified on box 4, laptop and box 5)
#   3. wait until vast-homr5 is idle (no python job of anybody else, >= 14 GB available), then held-out read (tmux pilot_val_<NAME>, 5 lists, GPU)
#   4. the 28-scan GPU evaluation (tmux pilot_eval_<NAME>; res_eval.py --tag <NAME>_gpu --model <NAME> --scale 1; /root/logs/gpu_chain.status lines)
#   5. pull the results to the laptop (cloud2_pull_min.sh, pilot_val)
# Before the first model: held-out reads of the baselines (released, run3_ctrl_s7, run3_ctrl_s11) with the same script, once.
# Every step is retried 3 times and logged to run/eval_run1/pilot_auto.log (Pacific time). State markers in run/eval_run1/pilot_auto_state/ make the script
# restartable (finished steps are skipped). The boxes keep working if the laptop sleeps; only the copy through the laptop and the polling wait.
# usage: nohup caffeinate -i bash run/eval_run1/pilot_auto.sh > run/eval_run1/pilot_auto.out 2>&1 &
# Dry run (no training involved): DRY=1 bash pilot_auto.sh   (model dry_s7 = the run3_ctrl_s7 weights; one piece, tag pilot_dry_s7_gpu; skips the idle wait; cleans up)
# NEVER put the name of the training script into a remote command line: the chain on box 4 waits with pgrep -f on it.
R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1
L=${PILOT_AUTO_LOG:-$E/pilot_auto.log}; ST=$E/pilot_auto_state; mkdir -p $ST
SSHO="-q -o BatchMode=yes -o ConnectTimeout=20 -o ServerAliveInterval=15 -o ServerAliveCountMax=4"
b4() { ssh $SSHO vast-homr4 "$@"; }
b5() { ssh $SSHO vast-homr5 "$@"; }
log() { echo "$(TZ=America/Los_Angeles date '+%F %T %Z') $*" >> $L; }
FAILS=""
retry() { # retry DESC cmd args...   three tries, growing pause, every failure logged
  local desc=$1 i rc; shift
  for i in 1 2 3; do "$@" && return 0; rc=$?; log "RETRY $i/3 (rc=$rc): $desc"; sleep $((20 * i)); done
  log "FAILED after 3 tries: $desc"; return 1
}
fail_model() { FAILS="$FAILS $1:$2"; log "MODEL $1: step '$2' FAILED, continuing with the next model (re-run the script later: finished steps are skipped)"; touch $ST/FAILED.$1.$2; }

# ---------- wait for a status line on box 4
wait_done() { # wait_done NAME -> 0 done, 2 training ended without weights/never will
  local name=$1 out nfail=0 last=$(date +%s) now
  while true; do
    out=$(b4 "grep -E '$name (DONE|MISSING)|CHAIN DONE' /workspace/logs/pilot/status.log; true" 2>/dev/null); rc=$?
    now=$(date +%s)
    if [ $((now - last)) -gt 150 ]; then log "note: $((now - last)) s since the last poll (laptop asleep or network down)"; fi
    last=$now
    if [ $rc -ne 0 ]; then nfail=$((nfail + 1)); [ $((nfail % 10)) -eq 1 ] && log "ssh to vast-homr4 failed ($nfail in a row), still waiting for $name"; sleep 30; continue; fi
    nfail=0
    echo "$out" | grep -q "$name DONE" && return 0
    echo "$out" | grep -q "$name MISSING" && { log "$name: status log says MISSING mix list"; return 2; }
    echo "$out" | grep -q "CHAIN DONE" && { log "$name: CHAIN DONE seen but no '$name DONE'"; return 2; }
    sleep 30
  done
}

# ---------- 1. export
export_one() { # export_one NAME
  local name=$1 i
  [ -e $ST/$name.export.ok ] && return 0
  if b4 "grep -q EXPORT_EXIT=0 /workspace/logs/pilot_auto/export_$name.log && test -s /workspace/onnx/$name/encoder_$name.onnx" 2>/dev/null; then touch $ST/$name.export.ok; log "$name: export already on box 4"; return 0; fi
  for i in 1 2 3; do
    if b4 "tmux has-session -t =pexp_$name" 2>/dev/null; then log "$name: export session already running, waiting"; else
      log "$name: export on vast-homr4 (tmux pexp_$name, attempt $i)"
      b4 "tmux new-session -d -s pexp_$name 'bash /workspace/pilot_auto/pilot_export.sh $name'" || { log "could not start export session"; sleep 30; continue; }
    fi
    local t0=$(date +%s)
    while b4 "tmux has-session -t =pexp_$name" 2>/dev/null || [ $? -eq 255 ]; do
      [ $(( $(date +%s) - t0 )) -gt 1500 ] && { log "$name: export longer than 25 min, still waiting"; t0=$(date +%s); }
      sleep 10
    done
    if b4 "grep -q EXPORT_EXIT=0 /workspace/logs/pilot_auto/export_$name.log" 2>/dev/null; then touch $ST/$name.export.ok; log "$name: export ok ($(b4 "tail -n 12 /workspace/logs/pilot_auto/export_$name.log | grep -c onnx") onnx lines in the log)"; return 0; fi
    log "$name: export attempt $i FAILED: $(b4 "grep -E 'FAILED|Error|error' /workspace/logs/pilot_auto/export_$name.log | tail -n 3" 2>/dev/null | tr '\n' '|')"
    sleep 30
  done
  return 1
}

# ---------- 2. copy to box 5 (and keep a laptop copy)
sizes_b4() { b4 "cd /workspace/onnx/$1 && stat -c '%s %n' * | sort -k2"; }
sizes_b5() { b5 "cd $R/models/$1 && stat -c '%s %n' * | sort -k2"; }
sizes_lap() { (cd $R/models/$1 && stat -f '%z %N' * | sort -k2); }
copy_once() { # copy_once NAME
  local name=$1 a c d
  LAPTOP_COPY=1 bash $R/cloud2_models.sh $name /workspace/onnx/$name >> $L 2>&1
  a=$(sizes_b4 $name); c=$(sizes_b5 $name); d=$(sizes_lap $name)
  [ -n "$a" ] && [ "$a" = "$c" ] && [ "$a" = "$d" ] && return 0
  log "$name: copy size check differs: box4 [$(echo $a | tr '\n' ' ')] box5 [$(echo $c | tr '\n' ' ')] laptop [$(echo $d | tr '\n' ' ')]"; return 1
}
copy_model() {
  local name=$1 free
  [ -e $ST/$name.copy.ok ] && return 0
  retry "$name copy to vast-homr5" copy_once $name || return 1
  touch $ST/$name.copy.ok; log "$name: ONNX copied to vast-homr5 and kept in $R/models/$name (sizes equal on box 4, box 5, laptop)"
  free=$(b4 "df --output=avail -BM /workspace | tail -1 | tr -dc 0-9" 2>/dev/null)
  if [ -n "$free" ] && [ "$free" -lt 2500 ]; then
    b4 "rm -rf /workspace/onnx/$name" && log "$name: box 4 has only $free MB free: removed /workspace/onnx/$name (copies verified; the .pth stays and can be re-exported)"
  fi
  return 0
}

# ---------- box 5 idle check
box5_busy() { # prints a reason and returns 0 if busy
  local out
  out=$(b5 "ps -eo args | grep -E 'bin/python|pdftoppm|lilypond|ffmpeg|rsvg|verovio' | grep -v grep | cut -c1-110 | head -n 3; echo AVAIL \$(free -g | awk '/Mem:/{print \$7}')" 2>/dev/null) || { echo "ssh to vast-homr5 failed"; return 0; }
  local avail=$(echo "$out" | sed -n 's/^AVAIL //p')
  local procs=$(echo "$out" | grep -v '^AVAIL')
  if [ -n "$procs" ]; then echo "python job(s) of someone else: $(echo "$procs" | head -n 1)"; return 0; fi
  if [ -n "$avail" ] && [ "$avail" -lt 14 ]; then echo "only $avail GB memory available"; return 0; fi
  return 1
}
wait_box5_idle() { # three idle readings 20 s apart; logs the reason every 10 minutes
  [ "$SKIP_IDLE" = 1 ] && return 0
  local ok=0 n=0 why
  while [ $ok -lt 3 ]; do
    if why=$(box5_busy); then ok=0; n=$((n + 1)); [ $((n % 20)) -eq 1 ] && log "waiting for vast-homr5 to be idle: $why"; sleep 30; else ok=$((ok + 1)); sleep 20; fi
  done
}
b5_marker() { b5 "echo '$(TZ=America/Los_Angeles date '+%F %T %Z') $1' > /root/logs/pilot_auto.busy; true"; }
b5_unmark() { b5 "rm -f /root/logs/pilot_auto.busy; true"; }

# ---------- a tmux job on box 5 that has to finish; $2 = session, $3 = command, $4 = file that holds the end marker, $5 = marker text
run_b5_job() { # run_b5_job SESSION CMD LOGFILE ENDPATTERN
  local sess=$1 cmd=$2 logf=$3 pat=$4 t0
  if ! b5 "tmux has-session -t =$sess" 2>/dev/null; then
    b5 "tmux new-session -d -s $sess '$cmd'" || return 1
  else log "tmux $sess already running on vast-homr5, waiting"; fi
  t0=$(date +%s)
  while b5 "tmux has-session -t =$sess" 2>/dev/null || [ $? -eq 255 ]; do
    if [ $(( $(date +%s) - t0 )) -gt 3600 ]; then log "$sess still running after $(( ($(date +%s) - t0) / 60 )) min"; t0=$(date +%s); fi
    sleep 20
  done
  b5 "grep -q '$pat' $logf" 2>/dev/null
}

# ---------- 3. held-out read
valread_once() { # valread_once NAME
  wait_box5_idle; b5_marker "pilot_val_$1 (pilot automation)"
  run_b5_job pilot_val_$1 "bash $R/eval_run1/pilot_val_box.sh $1" /root/logs/pilot_val_$1.log 'VAL_EXIT=0'; local rc=$?
  b5_unmark; return $rc
}
valread() { # valread NAME
  local name=$1
  [ -e $ST/$name.val.ok ] && return 0
  retry "$name held-out read on vast-homr5" valread_once $name || return 1
  mkdir -p $E/pilot_val
  b5 "tar -c -C $R eval_run1/pilot_val/$name" | tar -x -C $R 2>/dev/null
  [ -s $E/pilot_val/$name/b2_twin.json ] || { log "$name: held-out results not pulled"; return 1; }
  touch $ST/$name.val.ok
  log "$name: held-out read done: $(/Users/yiduoke/Documents/homr/.venv/bin/python $E/pilot_auto_scripts/pilot_val_summary.py $E/pilot_val/$name)"
  return 0
}

# ---------- 4. 28-scan evaluation
eval_once() { # eval_once NAME TAG [extra res_eval args]
  local name=$1 tag=$2; shift 2
  wait_box5_idle; b5_marker "pilot_eval_$name ($tag, pilot automation)"
  run_b5_job pilot_eval_$name "bash $R/eval_run1/pilot_eval_box.sh $name $tag $*" /root/logs/gpu_chain.status "end $tag exit=0"; local rc=$?
  b5_unmark; return $rc
}
evaluate() { # evaluate NAME TAG [extra]
  local name=$1 tag=$2; shift 2
  [ -e $ST/$name.eval.ok ] && return 0
  retry "$name 28-scan evaluation ($tag) on vast-homr5" eval_once $name $tag "$@" || return 1
  bash $R/cloud2_pull_min.sh $tag >> $L 2>&1
  local n=$(ls $R/out/testset/*/*-$tag.musicxml 2>/dev/null | wc -l)
  [ $n -ge ${EXPECT_PIECES:-28} ] || { log "$name: only $n musicxml pulled for $tag"; return 1; }
  touch $ST/$name.eval.ok
  log "$name: evaluation $tag pulled ($n pieces). $(grep -E '^Mean over' $R/out/testset/RES-$tag.md | tr '\n' ' ') $(grep -E '^Pieces at 97' $R/out/testset/RES-$tag.md | tr '\n' ' ')"
  return 0
}

# ---------- one model
process_model() { # process_model NAME ARM SEED [dry]
  local name=$1 tag=${1}_gpu
  log "=== $name: waiting for DONE in /workspace/logs/pilot/status.log"
  if [ "$DRY" != 1 ]; then wait_done $name || { fail_model $name training; return; }; fi
  log "$name: training finished"
  if [ "$DRY" != 1 ]; then
    b4 "ls /workspace/homr_acc/training/architecture/transformer/pytorch_model_${name}_*.pth" >/dev/null 2>&1 || { log "$name: DONE but no weights file on box 4"; fail_model $name noweights; return; }
  fi
  export_one $name || { fail_model $name export; return; }
  copy_model $name || { fail_model $name copy; return; }
  baselines
  valread $name || fail_model $name valread
  if [ "$DRY" = 1 ]; then evaluate $name $tag --pieces bach-fugue-873 || fail_model $name eval; else evaluate $name $tag || fail_model $name eval; fi
  log "=== $name: finished (failed steps so far:${FAILS:- none})"
}

# ---------- baselines of the held-out read (same script, same GPU path); once
baselines() {
  local b
  for b in released run3_ctrl_s7 run3_ctrl_s11; do
    [ -e $ST/base.$b.val.ok ] && continue
    [ "$DRY" = 1 ] && [ $b != run3_ctrl_s7 ] && continue
    if retry "baseline held-out read $b" valread_once $b; then
      mkdir -p $E/pilot_val; b5 "tar -c -C $R eval_run1/pilot_val/$b" | tar -x -C $R 2>/dev/null
      if [ -s $E/pilot_val/$b/b2_twin.json ]; then touch $ST/base.$b.val.ok; log "baseline $b: held-out read done"; else log "baseline $b: result not pulled"; fi
    else log "baseline $b FAILED"; fi
  done
}

log "################ pilot_auto.sh start (pid $$, DRY=${DRY:-0}) ################"
if [ "$DRY" = 1 ]; then
  export SKIP_IDLE=1 EXPECT_PIECES=1
  process_model dry_s7
  log "DRY RUN finished (failed:${FAILS:- none}); not cleaned: remove dry_s7 files by hand"
  exit 0
fi
# the box-5 files of the automation (scripts, validation crops and lists, 24 MB) were pushed by the preparation step; check they are there
b5 "test -s $R/scan_pairs_virtuoso/batch2/lists/batch2_val_v2_twin.txt && test -x $R/eval_run1/pilot_eval_box.sh" || { log "FATAL: box-5 files missing, push them first (see PILOT_AUTO in EXPERIMENTS.md D29)"; exit 1; }
for name in pilot_CTRL_RENDER_s7 pilot_SCAN_s7 pilot_CTRL_RENDER_s11 pilot_SCAN_s11; do
  process_model $name
done
log "################ ALL FOUR MODELS PROCESSED; failed steps:${FAILS:- none} ################"
log "next (not started): python eval_run1/pilot_final_table.py   -> out/testset/PILOT-final-table-<date>.md"
