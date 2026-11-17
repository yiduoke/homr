"""Run-3 relabel (copy of relabel_run2.py, which is unchanged): the run-2 label rule (lift = printed
sign) for the staffs added in the candidate lists: hard PDMX, ASAP, Scriabin.
usage: NEEDED=<file with run-1 token paths, one per line> relabel_run3.py <set> [limit]
 set: pdmx_hard asap kern_scriabin
Writes /workspace/run3/tokens/<path under /workspace> (same mirrored layout as /workspace/run2/tokens),
status in /workspace/run3/status/<set>.json.
Differences to run 2:
 - the staffs come from NEEDED (the selected token paths) instead of the run-1 lists;
 - ASAP and Scriabin: their MuseScore exports were deleted, so the MuseScore MusicXML is re-exported
   (/workspace/run3/export_ms.py, same MuseScore, same per-piece style, into /workspace/run3/ms_export/<set>/)
   and used like the pdmx_hard rendered_scores. The old "fuzzy" mode of regen.py is not used.
 - Scriabin is NOT relabeled from the kern with Verovio: its images are MuseScore renders of a music21
   MusicXML conversion (r6_extra/prep_kern.py, render.py), so the printed signs are MuseScore's.
Original docstring of relabel_run2.py:
 Reads the unique token paths of /workspace/run1/{run1_train,run1_val,holdout_*}.txt of that set,
 MuseScore sets: new MusicXML parser (<accidental>), staff mapping as regen_meter/relabel_octave.
MuseScore sets: new MusicXML parser (<accidental>), staff mapping as regen_meter/relabel_octave.
lilypond: the rule (homr.accidentals) applied to the sounding alterations of the XML.
grandstaff: Verovio 6.4.1 MEI @accid per note as printed_signs.
"""
import os as _os
_os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import collections, json, multiprocessing as mp, os, re, sys
from pathlib import Path

sys.path.insert(0, "/workspace/regen_meter")
sys.path.insert(0, "/workspace/audit_meter")
sys.path.insert(0, "/workspace/octave_relabel")
import regen as R  # noqa: E402
import relabel_oct as O  # noqa: E402

OUT = "/workspace/run3"
LISTS = ["run1_train", "run1_val", "holdout_real", "holdout_inserted"]
SETDEF = {  # name -> (root, relative dir of the token files in datasets_meter, old dir)
    "Lieder-main": ("/workspace/homr566", "Lieder-main"),
    "pdmx": ("/workspace/homr566", "pdmx"),
    "pdmx_hard": ("/workspace/homr566", "pdmx/hard"),
    "grandstaff": ("/workspace/homr566", "grandstaff"),
    "asap": ("/workspace/homr566", "asap"),
    "kern_scriabin": ("/workspace/homr566", "kern_scriabin"),
    "musescore_octave": ("/workspace/homr", "musescore_octave"),
    "lilypond": ("/workspace/homr", "lilypond"),
}
RULE = False


def needed_tokens(name):
    if os.environ.get("NEEDED"):
        root, sub = SETDEF[name]
        pre = f"{root}/datasets_meter/{sub}/"
        out = set()
        for ln in open(os.environ["NEEDED"]):
            t = ln.strip().split(",")[-1]
            if t.startswith(pre) and not (name == "pdmx" and t.startswith(pre + "hard/")):
                out.add(t)
        return sorted(out)
    root, sub = SETDEF[name]
    pre = f"{root}/datasets_meter/{sub}/"
    out = set()
    for n in LISTS:
        for ln in open(f"/workspace/run1/{n}.txt"):
            ln = ln.strip()
            if not ln:
                continue
            t = ln.split(",")[1]
            if not t.startswith(pre):
                continue
            if name == "pdmx" and t.startswith(pre + "hard/"):
                continue
            out.add(t)
    return sorted(out)


def new_path(t):
    return f"{OUT}/tokens/{t[len('/workspace/'):]}"


def norm2(text):
    """Text without time signatures, beams and lifts (what staff mapping compares)."""
    out = []
    for line in text.split("\n"):
        parts = []
        for p in line.split("&"):
            p = p.strip()
            if p.startswith("timeSignature"):
                continue
            f = p.split(" ")
            if len(f) == 6:
                if f[0].startswith(("note", "rest")):
                    keep = [x for x in f[4].split("_") if x not in O.BEAMS and x not in ("", "_")]
                    f[4] = "_".join(keep) or "_"
                f[2] = "L"
                p = " ".join(f)
            parts.append(p)
        if parts:
            out.append("&".join(sorted(parts)))
    return "\n".join(out)


def align(old, new):
    """
    New text with the symbols of every chord in the order of the old text. The token writer
    sorts a chord by its text, lift included, so notes of the same pitch can swap places when
    only their lift changes. None if the symbols differ in anything but the lift.
    """
    olds, news = old.strip("\n").split("\n"), new.strip("\n").split("\n")
    if len(olds) != len(news):
        return None
    out = []
    for lo, ln in zip(olds, news):
        po = [p.strip() for p in lo.split("&")]
        pn = [p.strip() for p in ln.split("&")]
        if len(po) != len(pn):
            return None
        pool = collections.defaultdict(list)
        for p in pn:
            pool[strip_lift(p)].append(p)
        line = []
        for p in po:
            k = strip_lift(p)
            if not pool[k]:
                return None
            line.append(pool[k].pop(0))
        out.append("&".join(line))
    return "\n".join(out) + ("\n" if old.endswith("\n") else "")


def strip_lift(text):
    out = []
    for line in text.split("\n"):
        parts = []
        for p in line.split("&"):
            f = p.strip().split(" ")
            if len(f) == 6:
                f[2] = "L"
            parts.append(" ".join(f))
        out.append("&".join(parts))
    return "\n".join(out).strip()


def _extract(c, k):
    from homr.accidentals import printed_lifts_from_sounding
    from training.transformer.training_vocabulary import token_lines_to_str

    if len(c.voice) < k:
        raise IndexError
    popped = list(c.voice[:k])
    snap = R._snap(c)
    before = len(c.voice)
    try:
        syms = c.extract_measures(k)
        if RULE:
            syms = printed_lifts_from_sounding(syms)
        return token_lines_to_str(syms), popped
    except Exception:
        R._restore(c, snap, popped[: before - len(c.voice)])
        raise


def install_patches(rule):
    global RULE
    RULE = rule
    R.norm = norm2
    O.norm = norm2
    R._extract = _extract
    if rule:
        from homr.accidentals import UnsupportedAccidentalError, sounding_lift
        import training.omr_datasets.music_xml_parser as X

        def lift_by_rule(note, strict):
            pitch = X._children(note, "pitch")[0]
            a = X._child(pitch, "alter")
            alter = float(X._text(a, "0")) if a is not None else 0.0
            if alter != int(alter) or abs(alter) > 2:
                raise UnsupportedAccidentalError(f"alter {alter}")
            return sounding_lift(int(alter))

        X._lift_from_accidental = lift_by_rule


# ------------------------------------------------------------------ MuseScore / LilyPond sets
def run_xml_set(name, limit):
    root, sub = SETDEF[name]
    needed = needed_tokens(name)
    octave = name in ("musescore_octave", "lilypond")
    old_flat_rel = f"datasets/{sub}/flat"
    flat = f"{root}/{old_flat_rel}"
    mscls = O._MS
    by_stem = collections.defaultdict(lambda: ({}, {}, {}))  # ms, vrv, paths
    for fn in os.listdir(flat):
        if not fn.endswith(".tokens"):
            continue
        key = fn[: -len(".tokens")]
        m = R._VRV.match(key)
        if m and not octave:
            by_stem[m[1]][1][(int(m[2]), int(m[3]))] = key
        else:
            m = mscls.match(key)
            if not m:
                continue
            by_stem[m[1]][0][(int(m[2]), int(m[3]))] = key
        by_stem[m[1]][2][key] = f"{flat}/{fn}"
    status = {}
    need_by_stem = collections.defaultdict(set)
    tok_key = {}
    for t in needed:
        key = os.path.basename(t)[: -len(".tokens")]
        m = (R._VRV.match(key) if not octave else None) or mscls.match(key)
        if not m:
            status[t] = ["badname", ""]
            continue
        need_by_stem[m[1]].add(key)
        tok_key[t] = (m[1], key)
    jobs = []
    for stem in sorted(need_by_stem):
        ms, vrv, paths = by_stem[stem]
        if octave:
            src = O.find_source(stem)
            if src is None:
                for k in need_by_stem[stem]:
                    status[f"{os.path.dirname(needed[0])}/{k}.tokens"] = ["no_source", ""]
                continue
            jobs.append((stem, src, ms, paths, need_by_stem[stem]))
        else:
            if name in ("asap", "kern_scriabin"):
                src = f"/workspace/run3/ms_export/{name}/{stem}.musicxml"
            else:
                src = f"{root}/datasets/{sub}/rendered_scores/{stem}.musicxml"
            jobs.append((stem, src, ms, vrv, paths, need_by_stem[stem]))
    if limit:
        jobs = jobs[:: max(1, len(jobs) // limit)][:limit]
    print(name, "needed", len(needed), "stems", len(jobs), flush=True)
    results = {}
    if octave:
        wjobs = [(old_flat_rel, j[0], j[1], j[2], j[3], j[4], name == "lilypond") for j in jobs]
        fn = O.process_stem
    else:
        wjobs = jobs
        fn = R.process_stem
    with mp.Pool(int(os.environ.get("NP", "48")), maxtasksperchild=50) as pool:
        for i, (job, r) in enumerate(zip(jobs, pool.imap(fn, wjobs, chunksize=1))):
            results[job[0]] = r
            if i % 500 == 0:
                print("stems", i, len(jobs), flush=True)
    for t, (stem, key) in tok_key.items():
        if stem not in results:
            status.setdefault(t, ["no_source", ""])
            continue
        st, text = results[stem].get(key, ("no_match", "missing"))
        if st != "ok":
            status[t] = [st, text[:100]]
            continue
        text = align(Path(t).read_text(), text)
        if text is None:
            status[t] = ["differs_other_field", ""]
            continue
        write(t, text)
        status[t] = ["ok", ""]
    return status


def write(t, text):
    p = new_path(t)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


# ------------------------------------------------------------------ grandstaff
_RXTOK = re.compile(r"^[\[\(\{<>&/\\^~yYxXiIjZN]*\d*\.*[^a-grA-GR#]*[a-gA-G]+(--|-|n|##|#)?")


def mark_kern(lines):
    out = []
    for ln_no, line in enumerate(lines, start=1):
        l = line.rstrip("\n")
        if not l or l[0] in "*!=":
            out.append(l)
            continue
        fields = l.split("\t")
        nf = []
        for fi, f in enumerate(fields, start=1):
            toks = f.split(" ")
            nt = []
            for si, tok in enumerate(toks, start=1):
                if tok != "." and _RXTOK.match(tok):
                    tok = f"{tok}@{ln_no},{fi},{si if len(toks) > 1 else 0}"
                nt.append(tok)
            nf.append(" ".join(nt))
        out.append("\t".join(nf))
    return [x + "\n" for x in out]


def mei_accids(text):
    import verovio

    tk = verovio.toolkit()
    if not tk.loadData(text):
        raise ValueError("verovio load failed")
    mei = tk.getMEI()
    notes = {}
    for ev in re.finditer(r"<note ([^>]*?)/?>", mei):
        a = dict(re.findall(r'([\w.:]+)="([^"]*)"', ev.group(1)))
        m = re.match(r"note-L(\d+)F(\d+)(?:S(\d+))?", a.get("xml:id", ""))
        if m:
            notes[(int(m[1]), int(m[2]), int(m[3] or 0))] = a.get("accid")
    return notes


def kern_one(t):
    import homr.accidentals as A
    import training.omr_datasets.humdrum_kern_parser as H
    from training.transformer.training_vocabulary import token_lines_to_str

    krn = t.replace("/datasets_meter/", "/datasets/")[: -len(".tokens")] + ".krn"
    try:
        lines = open(krn).readlines()
        mei = mei_accids("".join(lines))
        locs = []
        orig_lift = H.HumdrumKernConverter._accidental_to_lift
        orig_post = H.printed_lifts_from_sounding

        def lift_with_loc(self, accidental, token):
            v = orig_lift(self, accidental, token)
            m = re.search(r"@(\d+),(\d+),(\d+)$", token)
            return v + (f"@{m[1]},{m[2]},{m[3]}" if m else "@none")

        def post(symbols, printed_signs=None):
            res = []
            for s in symbols:
                if A._is_note(s):
                    base, _, loc = s.lift.partition("@")
                    locs.append(loc)
                    s = s.change_lift(base)
                res.append(s)
            return orig_post(res, None)

        H.HumdrumKernConverter._accidental_to_lift = lift_with_loc
        H.printed_lifts_from_sounding = post
        try:
            H.convert_kern_to_tokens(mark_kern(lines))
        finally:
            H.HumdrumKernConverter._accidental_to_lift = orig_lift
            H.printed_lifts_from_sounding = orig_post
        signs = []
        for loc in locs:
            if loc == "none":
                return t, ("no_mei_match", "no location")
            k = tuple(int(x) for x in loc.split(","))
            if k not in mei:
                return t, ("no_mei_match", str(k))
            signs.append(A.sign_from_mei(mei[k]))
        new = token_lines_to_str(H.convert_kern_to_tokens(lines, printed_signs=signs))
        rule = token_lines_to_str(H.convert_kern_to_tokens(lines))
        n_diff_rule = sum(
            1
            for a, b in zip(new.split("\n"), rule.split("\n"))
            if a != b
        )
        return t, ("ok", new, n_diff_rule)
    except A.UnsupportedAccidentalError as e:
        return t, ("unsupported_accidental", str(e))
    except Exception as e:  # noqa: BLE001
        return t, ("error", repr(e)[:150])


def run_kern(limit):
    needed = needed_tokens("grandstaff")
    if limit:
        needed = needed[:: max(1, len(needed) // limit)][:limit]
    status = {}
    rule_diff = 0
    n = 0
    with mp.Pool(int(os.environ.get("NP", "48")), maxtasksperchild=200) as pool:
        for i, (t, r) in enumerate(pool.imap(kern_one, needed, chunksize=32)):
            if r[0] != "ok":
                status[t] = [r[0], r[1][:100]]
                continue
            text = align(Path(t).read_text(), r[1])
            if text is None:
                status[t] = ["differs_other_field", ""]
                continue
            write(t, text)
            status[t] = ["ok", ""]
            rule_diff += r[2] > 0
            n += 1
            if i % 5000 == 0:
                print("kern", i, len(needed), flush=True)
    status["__rule_vs_mei_staffs_differing"] = [rule_diff, n]
    return status


def main():
    name = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    install_patches(rule=name == "lilypond")
    status = run_kern(limit) if name == "grandstaff" else run_xml_set(name, limit)
    os.makedirs(f"{OUT}/status", exist_ok=True)
    tag = name + (f"_limit{limit}" if limit else "")
    json.dump(status, open(f"{OUT}/status/{tag}.json", "w"))
    cnt = collections.Counter(v[0] for k, v in status.items() if not k.startswith("__"))
    print(name, dict(cnt), status.get("__rule_vs_mei_staffs_differing"))
    det = collections.Counter((v[0], v[1][:60]) for k, v in status.items() if not k.startswith("__") and v[0] != "ok")
    for k, v in det.most_common(10):
        print("  ", k, v)


if __name__ == "__main__":
    main()
