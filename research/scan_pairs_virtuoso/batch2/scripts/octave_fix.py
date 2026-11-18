"""Corrected label tokens for the octave-review crops (written pitch = printed pitch; the 8va/8vb tokens carry the shift).
  remove_raise(name): the print writes the high notes at pitch (edition difference), the ASAP label has 8va/8vb with lowered written notes ->
      drop the shift tokens and move the notes under them back by the shift (8va: +1 octave, 8vb: -1).
  add_bracket(name, k0, k1, stop, delta): the print has a bracket the label lacks -> insert octaveShift_8va before the line of the k0-th and the stop after the
      k1-th upper-staff note line (counted over the crop, chord = one line); `delta` octaves added to the written pitch of the notes in between (-1 if the label holds sounding pitch).
  Every corrected file is compared with the released model's read of the scan: share of aligned notes with octave difference 0 (aligned per bar and staff on the pitch letters).
usage: octave_fix.py verify|write"""
import os, sys, re, json, glob, difflib, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
B = '/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/'
OUT = B + 'octave_review/tokens_corrected/'
recs = {}
for f in glob.glob(B + 'work/export/*.json'):
    for r in json.load(open(f))['records']:
        if r.get('name'): recs[r['name']] = r
reads = {}
for f in glob.glob(B + 'work/reads/*.jsonl'):
    for l in open(f):
        d = json.loads(l); reads[d['id']] = d

def shift_pitch(p, d):
    return p[0] + str(int(p[1:]) + d) if p and p[0] in 'ABCDEFG' and p[1:].lstrip('-').isdigit() else p

def parse(text):
    return [[p.split(' ') for p in l.split('&')] for l in text.rstrip('\n').split('\n')]
def unparse(lines): return '\n'.join('&'.join(' '.join(f) for f in parts) for parts in lines) + '\n'
def staff_of(f): return f[-1][:5] if f and f[-1][:5] in ('upper', 'lower') else None

def remove_raise(text):
    out = []; state = {}
    for parts in parse(text):
        new = []
        for f in parts:
            st = staff_of(f)
            if f[0] in ('octaveShift_8va', 'octaveShift_8vb'): state[st] = +1 if f[0].endswith('8va') else -1; continue
            if f[0] == 'octaveShiftStop': state[st] = 0; continue
            if f[0].startswith('note') and state.get(st): f = list(f); f[1] = shift_pitch(f[1], state[st])
            new.append(f)
        if new: out.append(new)
    return unparse(out)

def upper_note_lines(lines):
    idx = []
    for i, parts in enumerate(lines):
        if any(f[0].startswith('note') and staff_of(f) == 'upper' for f in parts): idx.append(i)
    return idx

def add_bracket(text, k0, k1, stop, delta):
    lines = parse(text); idx = upper_note_lines(lines); i0, i1 = idx[k0], idx[k1]
    out = []
    for i, parts in enumerate(lines):
        if i == i0: out.append([['octaveShift_8va', '_', '_', '_', '_', 'upper']])
        if i0 <= i <= i1 and delta:
            parts = [(list(f[:1]) + [shift_pitch(f[1], delta)] + list(f[2:])) if f[0].startswith('note') and staff_of(f) == 'upper' else f for f in parts]
        out.append(parts)
        if i == i1 and stop: out.append([['octaveShiftStop', '_', '_', '_', '_', 'upper']])
    return unparse(out)

def notes(text):
    out = []; bar = 0
    for parts in parse(text):
        if parts[0][0] in ('barline',) or parts[0][0].startswith('repeat'): bar += 1; continue
        for f in parts:
            if f[0].startswith('note') and f[1] and f[1][0] in 'ABCDEFG' and staff_of(f): out.append((bar, staff_of(f), f[1][0], int(f[1][1:])))
    return out

def deltas(label_text, read_text):
    lab, mod = notes(label_text), notes(read_text); c = collections.Counter()
    for staff in ('upper', 'lower'):
        for b in sorted(set(x[0] for x in lab) | set(x[0] for x in mod)):
            A = [x for x in lab if x[0] == b and x[1] == staff]; Bm = [x for x in mod if x[0] == b and x[1] == staff]
            sm = difflib.SequenceMatcher(None, [x[2] for x in A], [x[2] for x in Bm], autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    for k in range(i2 - i1): c[A[i1 + k][3] - Bm[j1 + k][3]] += 1
    return c

def target_run(name, sign):
    """first/last upper-note-line index whose aligned notes have label - read == sign (for add_bracket over delta-evidence)"""
    r = recs[name]; text = open(r['tokens']).read(); rd = reads[r['id']]['tokens']
    lines = parse(text); idx = upper_note_lines(lines)
    lab = [(i, f) for i in idx for f in lines[i] if f[0].startswith('note') and staff_of(f) == 'upper']
    # align per bar on pitch letters (main staff 'upper' only)
    labn = []; bar = 0
    for i, parts in enumerate(lines):
        if parts[0][0] == 'barline' or parts[0][0].startswith('repeat'): bar += 1; continue
        for f in parts:
            if f[0].startswith('note') and staff_of(f) == 'upper': labn.append((bar, i, f[1][0], int(f[1][1:])))
    modn = [x for x in notes(rd) if x[1] == 'upper']
    hits = []; allal = []
    for b in sorted(set(x[0] for x in labn)):
        A = [x for x in labn if x[0] == b]; Bm = [x for x in modn if x[0] == b]
        sm = difflib.SequenceMatcher(None, [x[2] for x in A], [x[2] for x in Bm], autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    d = A[i1 + k][3] - Bm[j1 + k][3]; allal.append((A[i1 + k][1], d))
                    if d == sign: hits.append(A[i1 + k][1])
    return hits, allal, idx

def verify(label_text, name):
    c = deltas(label_text, reads[recs[name]['id']]['tokens']); n = sum(c.values())
    return c, (c[0] / n if n else 0)
