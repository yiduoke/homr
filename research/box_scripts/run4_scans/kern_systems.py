"""Split a KernScores .krn at its original line breaks into staff systems and convert each system to
the CURRENT token format (full time signature, printed-accidental lift, beams): the code path of the
GrandStaff / run-2 labels (homr_acc training.omr_datasets.humdrum_kern_parser.convert_kern_to_tokens,
printed signs from Verovio MEI @accid as in relabel_run2.kern_one).

usage (PYTHONPATH=/workspace/homr_acc, CPU):
    python kern_systems.py <repo> [piece ...]      -> /workspace/run4/scans/kern/<repo>/<piece>.json

Per system the json holds: tokens text, status, reasons, n_bars (barline tokens), n_notes, first/last note,
the excerpt lines, and flags.

Layout of a .krn: the line-break marker `!!LO:LB:g=original` comes BEFORE the barline that ends the
previous system, so system i = lines after marker i (without its leading barline) + the leading barline of
marker i+1 (as the closing barline). Page breaks (`!!LO:PB:g=original`) also start a system.
A system starts with clef and key signature; the time signature is printed only on the first system of the
movement (or where the .krn changes meter), so only there the meter goes into the excerpt.
"""
import json
import os
import re
import sys
import traceback

ROOT = "/workspace/extra_scores/kern"
OUT = "/workspace/run4/scans/kern"
HIDDEN = re.compile(r"yy")  # hidden (invisible) note or rest
BAR_TOK = re.compile(r"^(=+)(\d*[a-z]?)(.*)$")


class Skip(Exception):
    pass


def norm_barline(tok):
    m = BAR_TOK.match(tok)
    if not m:
        raise Skip("barline " + tok)
    b = m.group(1) + m.group(3)
    return b


def parse_stream(lines):
    """-> items: ('L', tokens, staff_ids) | ('LB',) ; kern spines only, hidden tokens removed, `!` comments dropped."""
    types = []  # (type, staff id or None)
    items = []
    nstaff = 0
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        if line.startswith("!!"):
            if re.match(r"!!LO:(LB|PB):g=original", line):
                items.append(("LB",))
            continue
        toks = line.split("\t")
        if all(t.startswith("**") for t in toks):
            types = []
            nstaff = 0
            for t in toks:
                if t == "**kern":
                    types.append(("kern", nstaff))
                    nstaff += 1
                else:
                    types.append((t, None))
            items.append(("L", ["**kern"] * nstaff, list(range(nstaff))))
            continue
        if line.startswith("!"):
            continue
        if len(toks) != len(types):
            raise Skip(f"column count {len(toks)} != {len(types)}")
        if any(t in ("*x", "*+") for t in toks):
            raise Skip("spine op x/+")
        has_ops = any(t in ("*^", "*v", "*-") for t in toks)
        out_toks, out_ids = [], []
        new_types = []
        i = 0
        while i < len(toks):
            t = toks[i]
            ty, sid = types[i]
            if t == "*^":
                new_types += [(ty, sid), (ty, sid)]
                if ty == "kern":
                    out_toks.append(t)
                    out_ids.append(sid)
                i += 1
            elif t == "*v":
                j = i
                while j < len(toks) and toks[j] == "*v" and types[j][0] == ty:
                    j += 1
                new_types.append((ty, sid))
                if ty == "kern":
                    out_toks += ["*v"] * (j - i)
                    out_ids += [sid] * (j - i)
                i = j
            elif t == "*-":
                i += 1  # terminated spine
            else:
                new_types.append((ty, sid))
                if ty == "kern":
                    out_toks.append(t)
                    out_ids.append(sid)
                i += 1
        types = new_types if has_ops else types
        if not out_toks:
            continue
        if line.startswith("*") or toks[0].startswith("*"):
            if all(t == "*-" for t in toks):
                continue
        # data and barlines: remove hidden tokens
        if not toks[0].startswith(("*", "=")):
            cleaned = []
            for t in out_toks:
                if t == ".":
                    cleaned.append(t)
                    continue
                # a rest can carry a pitch which only places it vertically (4rGG): the image shows a plain rest
                subs = [re.sub(r"r[A-Ga-g]+", "r", s) for s in t.split(" ") if not HIDDEN.search(s)]
                cleaned.append(" ".join(subs) if subs else ".")
            out_toks = cleaned
        if out_toks[0].startswith("="):
            out_toks = [norm_barline(t.split(" ")[0]) if t.startswith("=") else t for t in out_toks]
        items.append(("L", out_toks, out_ids))
    return items


def is_interp(it):
    return it[0] == "L" and it[1][0].startswith("*") and not it[1][0].startswith("**")


def is_bar(it):
    return it[0] == "L" and it[1][0].startswith("=")


def is_data(it):
    return it[0] == "L" and not it[1][0].startswith(("*", "="))


def split_systems(items):
    segs = [[]]
    for it in items:
        if it[0] == "LB":
            segs.append([])
        else:
            segs[-1].append(it)
    return segs


class State:
    def __init__(self):
        self.clef, self.key, self.meter, self.met = {}, {}, {}, {}
        self.cols = []  # staff ids of the current columns
        self.staffchange = False

    def feed(self, it):
        if it[0] != "L":
            return
        toks, ids = it[1], it[2]
        if toks[0].startswith("**"):
            self.cols = list(ids)
            return
        if toks[0].startswith("*") or toks[0].startswith("="):
            pass
        if any(t in ("*^", "*v") for t in toks):
            new = []
            i = 0
            while i < len(toks):
                if toks[i] == "*^":
                    new += [ids[i], ids[i]]
                    i += 1
                elif toks[i] == "*v":
                    j = i
                    while j < len(toks) and toks[j] == "*v":
                        j += 1
                    new.append(ids[i])
                    i = j
                else:
                    new.append(ids[i])
                    i += 1
            self.cols = new
            return
        if toks[0].startswith("*"):
            for t, s in zip(toks, ids):
                if t.startswith("*clef"):
                    self.clef[s] = t
                elif re.match(r"\*k\[", t):
                    self.key[s] = t
                elif re.match(r"\*M\d", t):
                    self.meter[s] = t
                    self.met.pop(s, None)
                elif t.startswith("*met("):
                    self.met[s] = t
                elif re.match(r"\*staff\d", t) and not t.startswith(("*staff1/2",)):
                    self.staffchange = True


def excerpt_for(state_cols, state, body, end_bar, with_meter, n_staff):
    """Humdrum text lines for one system."""
    lines = []
    lines.append("\t".join(["**kern"] * n_staff))
    ncols = {}
    for s in state_cols:
        ncols[s] = ncols.get(s, 0) + 1
    if any(c > 2 for c in ncols.values()):
        raise Skip("more than two voices at system start")
    if any(c == 2 for c in ncols.values()):
        lines.append("\t".join("*^" if ncols.get(s, 1) == 2 else "*" for s in range(n_staff)))

    def head(d, name):
        if not all(s in d for s in state_cols):
            return None
        return "\t".join(d[s] for s in state_cols)

    h = head(state.clef, "clef")
    if h is None:
        raise Skip("no clef")
    lines.append(h)
    h = head(state.key, "key")
    lines.append(h if h else "\t".join("*k[]" for _ in state_cols))
    if with_meter:
        h = head(state.meter, "meter")
        if h:
            lines.append(h)
            h = head(state.met, "met")
            if h:
                lines.append(h)
    for it in body:
        lines.append("\t".join(it[1]))
    if end_bar is not None:
        lines.append("\t".join(end_bar[1]))
    lines.append("\t".join(["*-"] * len(end_bar[1] if end_bar is not None else body[-1][1])))
    return lines


# ---------------------------------------------------------------------------------------------- tokens
def mark_kern(lines):
    sys.path.insert(0, "/workspace/regen_meter")
    out = []
    rx = re.compile(r"^[\[\(\{<>&/\\^~yYxXiIjZN]*\d*\.*[^a-grA-GR#]*[a-gA-G]+(--|-|n|##|#)?")
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
                if tok != "." and rx.match(tok):
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


def to_tokens(lines):
    """-> (token text by MEI printed signs, token text by rule, n lines differing)."""
    import homr.accidentals as A
    import training.omr_datasets.humdrum_kern_parser as H
    from training.transformer.training_vocabulary import token_lines_to_str

    nl = [x + "\n" for x in lines]
    rule = token_lines_to_str(H.convert_kern_to_tokens(nl))
    mei = mei_accids("".join(nl))
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
            raise Skip("no mei location")
        k = tuple(int(x) for x in loc.split(","))
        if k not in mei:
            raise Skip("no mei match " + str(k))
        signs.append(A.sign_from_mei(mei[k]))
    symbols = H.convert_kern_to_tokens(nl, printed_signs=signs)
    text = token_lines_to_str(symbols)
    ndiff = sum(1 for a, b in zip(text.split("\n"), rule.split("\n")) if a != b)
    return symbols, text, rule, ndiff


def token_facts(symbols):
    notes = [s for s in symbols if s.rhythm.startswith("note")]
    bars = sum(1 for s in symbols if "barline" in s.rhythm or s.rhythm.startswith("repeat"))
    return dict(
        n_notes=len(notes),
        n_bars=bars,
        first_note=f"{notes[0].pitch}" if notes else None,
        last_note=f"{notes[-1].pitch}" if notes else None,
        pitches=[n.pitch for n in notes],
    )


def process_piece(repo, piece):
    path = f"{ROOT}/{repo}/kern/{piece}.krn"
    raw = open(path, encoding="utf-8", errors="replace").readlines()
    res = dict(repo=repo, piece=piece, systems=[], error=None)
    n_markers = sum(1 for l in raw if re.match(r"!!LO:(LB|PB):g=original", l))
    res["n_markers"] = n_markers
    try:
        items = parse_stream(raw)
    except Skip as e:
        res["error"] = "parse: " + str(e)
        return res
    segs = split_systems(items)
    n_staff = None
    for it in items:
        if it[0] == "L" and it[1][0].startswith("**"):
            n_staff = len(it[1])
            break
    if n_staff != 2:
        res["error"] = f"{n_staff} kern staves"
        return res
    st = State()
    # state after each segment's leading part
    from training.transformer.training_vocabulary import check_token_lines  # noqa: F401

    split_info = []
    for i, seg in enumerate(segs):
        # leading barline: first barline before any data line
        lead = None
        pre = []
        k = 0
        while k < len(seg) and not is_data(seg[k]):
            if is_bar(seg[k]):
                lead = seg[k]
                k += 1
                break
            pre.append(seg[k])
            k += 1
        body = seg[k:]
        for it in pre:
            st.feed(it)
        # snapshot of the state at system start
        snap = dict(clef=dict(st.clef), key=dict(st.key), meter=dict(st.meter), met=dict(st.met), cols=list(st.cols))
        split_info.append(dict(lead=lead, body=body, snap=snap, pre=pre, staffchange_before=st.staffchange))
        for it in body:
            st.feed(it)
    # segments with no data at all (e.g. a marker right before the end) are dropped
    nsys = len(segs)
    for i, info in enumerate(split_info):
        body = info["body"]
        if not any(is_data(it) for it in body):
            continue
        end_bar = split_info[i + 1]["lead"] if i + 1 < nsys else None
        if end_bar is None and body and is_bar(body[-1]):
            end_bar, body = body[-1], body[:-1]
        sysrec = dict(index=i, status="ok", reasons=[])
        try:
            class S:  # snapshot as State-like
                pass

            s = S()
            s.clef, s.key, s.meter, s.met = (info["snap"][x] for x in ("clef", "key", "meter", "met"))
            cols = info["snap"]["cols"]
            # does the body use octave shifts, cross-staff changes, other issues
            body_txt = "\n".join("\t".join(it[1]) for it in body)
            if re.search(r"\*X?8va|\*X?8ba|\*X?15ma|\*X?15mb|\*X?8vb", body_txt) or any(
                t.startswith(("*8va", "*X8va", "*8ba", "*X8ba", "*15ma", "*X15ma", "*8vb", "*X8vb"))
                for it in info["pre"]
                for t in it[1]
            ):
                sysrec["reasons"].append("octave_shift")
            if re.search(r"\*staff\d", body_txt):
                sysrec["reasons"].append("staff_change")
            if end_bar is not None and "repeat" not in "":
                pass
            if end_bar is not None and end_bar[1][0] in ("=:|!|:", "=:!!:"):
                end_bar = ("L", [("=:|!") for _ in end_bar[1]], end_bar[2])
            start_repeat = info["lead"] is not None and info["lead"][1][0] in ("=:|!|:", "=:!!:", "=!|:")
            if start_repeat:
                sysrec["reasons"].append("repeat_start_at_system_start")
            first_data = next((j for j, it in enumerate(body) if is_data(it)), len(body))
            if any(is_bar(it) and it[1][0] not in ("=", "=-") for it in body[:first_data]):
                sysrec["reasons"].append("repeat_start_at_system_start")  # a barline with repeat/double bar before the first note
            first_in_piece = (i == 0) or not any(is_data(it) for sg in segs[:i] for it in sg)
            lines = excerpt_for(cols, s, body, end_bar, first_in_piece, n_staff)
            sysrec["with_meter"] = bool(first_in_piece)
            sysrec["lines"] = lines
            symbols, text, rule, ndiff = to_tokens(lines)
            sysrec.update(token_facts(symbols))
            sysrec["tokens"] = text
            sysrec["lift_rule_vs_mei_lines"] = ndiff
        except Skip as e:
            sysrec["reasons"].append("skip: " + str(e))
        except Exception as e:  # noqa: BLE001
            sysrec["reasons"].append(type(e).__name__ + ": " + str(e)[:120])
        if sysrec["reasons"]:
            sysrec["status"] = "fail"
        res["systems"].append(sysrec)
    res["n_segments_with_data"] = len(res["systems"])
    return res


def main():
    repo = sys.argv[1]
    pieces = sys.argv[2:] or sorted(f[:-4] for f in os.listdir(f"{ROOT}/{repo}/kern") if f.endswith(".krn"))
    os.makedirs(f"{OUT}/{repo}", exist_ok=True)
    for p in pieces:
        try:
            r = process_piece(repo, p)
        except Exception as e:  # noqa: BLE001
            r = dict(repo=repo, piece=p, systems=[], error="crash " + repr(e)[:200], tb=traceback.format_exc()[-600:])
        json.dump(r, open(f"{OUT}/{repo}/{p}.json", "w"))
        ok = sum(1 for s in r["systems"] if s["status"] == "ok")
        print(repo, p, "systems", len(r["systems"]), "ok", ok, "error", r.get("error"), flush=True)


if __name__ == "__main__":
    main()
