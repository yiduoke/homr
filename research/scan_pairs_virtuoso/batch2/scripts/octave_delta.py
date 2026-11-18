"""Octave review helper: for a crop, align the label's notes with the released model's read bar by bar (pitch letter order, per staff, main voice
and others), report shift tokens (bar.note-index) of both and the octave difference label - read of every aligned note, split into notes under a
label bracket / not. usage: octave_delta.py <name> ...  | all (every octave-only disagreement crop)"""
import sys, os, json, glob, re, difflib, collections
B = '/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/'
recs = {}
for f in glob.glob(B + 'work/export/*.json'):
    for r in json.load(open(f))['records']:
        if r.get('name'): recs[r['name']] = r
reads = {}
for f in glob.glob(B + 'work/reads/*.jsonl'):
    for l in open(f):
        d = json.loads(l); reads[d['id']] = d

def seq(tokens):
    out = []; ev = []; bar = 0; state = {}; n = 0
    for l in tokens.strip().split('\n'):
        if l.startswith('barline'): bar += 1; n = 0; continue
        for part in l.split('&'):
            f = part.split(' '); t = f[0]; staff = f[-1][:5] if f[-1].startswith(('upper', 'lower')) else None
            if t in ('octaveShift_8va', 'octaveShift_8vb'): state[staff] = t[12:]; ev.append((bar, n, t[12:], staff))
            elif t == 'octaveShiftStop': state[staff] = None; ev.append((bar, n, 'stop', staff))
            elif t.startswith('note') and f[1] and f[1][0] in 'ABCDEFG' and staff:
                out.append((bar, staff, f[1][0], int(f[1][1:]), state.get(staff))); n += 1
    return out, ev

def analyse(name):
    r = recs[name]; lab, lev = seq(open(r['tokens']).read())
    rd = reads[r['id']]; mod, mev = seq(rd['tokens'])
    res = collections.Counter(); deltas_under = collections.Counter(); deltas_not = collections.Counter()
    for staff in ('upper', 'lower'):
        for b in sorted(set(x[0] for x in lab) | set(x[0] for x in mod)):
            A = [x for x in lab if x[0] == b and x[1] == staff]; Bm = [x for x in mod if x[0] == b and x[1] == staff]
            sm = difflib.SequenceMatcher(None, [x[2] for x in A], [x[2] for x in Bm], autojunk=False)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    for k in range(i2 - i1):
                        a, c = A[i1 + k], Bm[j1 + k]; d = a[3] - c[3]
                        (deltas_under if a[4] else deltas_not)[d] += 1
    fmt = lambda ev: ' '.join(f'{b}.{n}:{e}' + ('' if s == 'upper' else '(L)') for b, n, e, s in ev)
    return dict(name=name, label_ev=fmt(lev), read_ev=fmt(mev), under=dict(deltas_under), not_under=dict(deltas_not), f1=r.get('f1'),
                role=("start_inside " if r.get('oct_start_inside') else "") + ("end_inside" if r.get('oct_end_inside') else ""))

if __name__ == '__main__':
    names = sys.argv[1:]
    if names == ['all']:
        names = [n for n, r in recs.items() if r['reasons'] and all(x.startswith(('octave-bracket disagreement', 'octave shift (pitch')) for x in r['reasons']) and r.get('octave_pre_tier')]
    for n in names:
        a = analyse(n)
        print(f"{n} [{a['role']}] f1={a['f1']:.2f}\n   label: {a['label_ev'] or '-'}\n   read : {a['read_ev'] or '-'}\n   octave delta label-read under label bracket {a['under']}, elsewhere {a['not_under']}")
