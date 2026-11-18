"""Octave-review decisions of batch 2 (eye review of 47 octave-unverified crops: sheets work/sheets/oct, evidence in octave_review.md).
Writes octave_review/tokens_corrected/<name>.tokens for corrected crops, checks each against the released model's read of the scan and the trainer filters,
and writes work/octave_decisions.json (name -> decision admit | corrected | quarantine, note, tokens)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import octave_fix as F
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/tuplet_wt")
from unittest import mock
for _m in ("augraphy","augraphy.base","augraphy.base.augmentationpipeline","augraphy.base.augmentation","augraphy.utilities","augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
B = F.B
ADMIT = {  # label right (print and label agree; the model missed a printed bracket or invented one)
 'N1_p-02_s0': 'no bracket in print or label; the model invented an 8va', 'N1_p-04_s0': 'no bracket in print or label (the bracket in the crop margin belongs to the next system)',
 'N2_p-04_s1': 'no bracket in print or label; stray stop in the read', 'N2_p-04_s2': 'no bracket in print or label; the model invented 8va/stop',
 'N11_p-15_s5': 'print and label both have the 8va over the same notes (model missed it)', 'N12_p-05_s0': 'print and label both have the 8va over the first bars (model missed it)',
 'N16_p-04_s2': 'print and label both open the 8va in bar 3, running on into the next system (model missed it)'}
REMOVE_RAISE = {  # edition difference: the print writes the high notes at pitch, ASAP has 8va and lowered written notes
 n: 'print writes the notes at pitch (ledger lines) without 8va; ASAP has 8va with lowered notes: bracket removed, notes raised an octave (after the change 100% of aligned notes equal the scan read)'
 for n in ('N11_p-08_s5 N11_p-14_s4 N11_p-14_s5 N11_p-15_s0 N11_p-16_s3 N12_p-02_s0 N12_p-02_s2 N6_p-26_s1 N6_p-26_s2 N6_p-27_s0 N6_p-27_s1 N6_p-28_s5 N6_p-28_s6 N6_p-29_s2 '
           'N7_p-04_s3 N8_p-04_s2 N8_p-05_s3 N8_p-06_s1 N8_p-08_s1 N8_p-08_s2 N9_p-02_s5 N9_p-03_s0').split()}
def bar_lines(text):
    lines = F.parse(text); idx = F.upper_note_lines(lines); bars = []; b = 0; per = []
    for i, p in enumerate(lines):
        if p[0][0] == 'barline' or p[0][0].startswith('repeat'): b += 1
        per.append(b)
    return idx, [per[i] for i in idx]
ADD = {  # name: (first upper-note-line k0 or ('bar', n), last k1 or 'end', stop, delta, note)
 'N1_p-03_s1': (('bar', 1), 'bar1', True, 0, 'print: 8va over the whole second bar (hook at the barline); ASAP has none, written pitch equals the print: bracket added'),
 'N19_p-25_s3': (0, 'end', False, 0, 'print: 8va dotted line over the whole system, running on; ASAP has none: bracket added (open at both ends)'),
 'N19_p-25_s4': (0, 'end', False, 0, 'same, whole system under the 8va, running on'),
 'N19_p-26_s0': (0, 'end', False, 0, 'same, whole system under the 8va, running on'),
 'N19_p-26_s1': (0, 'end', True, 0, 'same; the print closes the 8va with a hook at the end of the bar'),
 'N4_p-17_s0': (('bar', 2), 'end', False, -1, 'print: 8va from the start of bar 3, running on into the next system; ASAP has none and holds sounding pitch: bracket added, 24 notes lowered an octave'),
 'N12_p-06_s4': ('run+1', None, False, -1, 'print: 8va starts in the last bar and runs on; ASAP has none and holds sounding pitch: bracket added over the 8 notes the scan read places an octave lower, lowered'),
}
QUAR = {
 'N7_p-03_s0': 'print has 12/8 (eighth notes) where the label has 4/4 with triplets: time signature and note values differ from the print (no bracket issue)',
 'N8_p-05_s4': 'label bracket starts earlier than the printed one (partial overlap of notes; edition/ASAP differ): not corrected',
 'N6_p-29_s3': 'label brackets partly agree and partly disagree with the print (4 notes edition difference, 3 agree): not corrected',
 'N9_p-07_s5': 'final bar: scan read agrees with the label except 3 notes, print has the final chord at pitch while ASAP has 8va: unclear, not corrected',
}
for n in 'N20_p-17_s1 N20_p-19_s2 N20_p-20_s3 N20_p-20_s4 N20_p-20_s5 N20_p-21_s2 N20_p-21_s3'.split():
    QUAR[n] = 'print has an 8va over part of the system that the ASAP label lacks (Var. IV-VI of Schubert D.935/3); partial span, not corrected'
PARTIAL = {  # kept-tier crops where label and read agree that a bracket exists, but the label bracket covers notes the print writes at pitch (checked by eye): quarantined, not corrected
 'N8_p-05_s0': 'label 8va covers about 5 chords of bar 1 where the print brackets 2 (9 notes an octave off the print)',
 'N11_p-16_s4': 'label 8va starts in the second half of bar 2 where the print writes those notes at pitch and brackets only the first chord of bar 3',
 'NR1_p-36_s5': 'label 8va runs 3 notes into bar 3 which the print writes at pitch (bracket ends with bar 2)',
}
dec = {}
os.makedirs(F.OUT, exist_ok=True)
def trainer_ok(path):
    try:
        t = read_tokens(path); check_token_lines(t)
    except Exception as e: return 'vocab ' + repr(e)[:40]
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES: return 'more than 5 ledger lines after the correction'
    return 'ok'
names = open(B + 'work/octave_names.txt').read().split()
for n in names:
    r = F.recs[n]; text = open(r['tokens']).read()
    if n in ADMIT: dec[n] = dict(decision='admit', note=ADMIT[n]); continue
    if n in QUAR: dec[n] = dict(decision='quarantine', note=QUAR[n]); continue
    if n in REMOVE_RAISE:
        new = F.remove_raise(text); note = REMOVE_RAISE[n]
    elif n in ADD:
        k0, k1, stop, delta, note = ADD[n]; idx, bars = bar_lines(text)
        if k0 == 'run+1':
            hits, allal, idx2 = F.target_run(n, +1); ks = [idx.index(h) for h in hits]; k0, k1 = min(ks), max(ks)
        else:
            if isinstance(k0, tuple): k0 = next(k for k, b in enumerate(bars) if b >= k0[1])
            if k1 == 'end': k1 = len(idx) - 1
            elif k1 == 'bar1': k1 = max(k for k, b in enumerate(bars) if b == 1)
        new = F.add_bracket(text, k0, k1, stop, delta)
    else:
        dec[n] = dict(decision='quarantine', note='not decided'); continue
    out = F.OUT + n + '.tokens'; open(out, 'w').write(new)
    c, share = F.verify(new, n); tr = trainer_ok(out)
    if tr != 'ok': dec[n] = dict(decision='quarantine', note=tr + ' (' + note[:60] + ')'); continue
    # added-bracket cases keep the read's own bracket evidence: the share of equal aligned notes must be at least 0.9
    if share < 0.9: dec[n] = dict(decision='quarantine', note='after the correction only %.0f%% of aligned notes equal the scan read' % (100 * share)); continue
    dec[n] = dict(decision='corrected', note=note, tokens=out, aligned_equal_after=round(share, 3))
for n, why in PARTIAL.items(): dec[n] = dict(decision='quarantine', note=why, partial=True)
json.dump(dec, open(B + 'work/octave_decisions.json', 'w'), indent=1)
import collections
print(collections.Counter(d['decision'] for d in dec.values()))
for n, d in dec.items():
    if d['decision'] == 'quarantine': print(n, d['note'][:110])
