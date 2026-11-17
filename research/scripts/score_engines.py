"""Score every engine against the Mutopia ground truth.

The metric is a normalised edit distance over the pitch sequence, using OMR-NED's
denominator so the numbers sit on the same scale as the published ones:

    NED = edit_distance(ref, pred) / (len(ref) + len(pred))

Pitch only, deliberately. Engines disagree on tempo, on how many measures a piece
has, and on how durations are spelled, so any time-aligned metric would mostly be
measuring those disagreements. "Did it read the right notes, in the right order"
is the question this answers, and it's the one listening keeps raising.

Chords are canonicalised by sorting pitches within an onset, so a chord spelled
bottom-up and top-down compare equal.
"""

import json
from pathlib import Path

import Levenshtein
from music21 import converter

ROOT = Path("/Users/yiduoke/Documents/homr")
TRUTH = ROOT / "run/truth"
WORK = ROOT / "run/work"


def pitch_sequence(path: str) -> list[int]:
    score = converter.parse(path, forceSource=True)
    events: list[tuple[float, int]] = []
    for part in score.parts:
        for n in part.flatten().notes:
            off = float(n.offset)
            for p in n.pitches:
                events.append((off, p.midi))
    events.sort()
    return [midi for _off, midi in events]


def ned(ref: list[int], pred: list[int]) -> float:
    if not ref and not pred:
        return 0.0
    # Levenshtein works on sequences; map pitches into a private-use char range.
    a = "".join(chr(0xE000 + (p % 128)) for p in ref)
    b = "".join(chr(0xE000 + (p % 128)) for p in pred)
    return Levenshtein.distance(a, b) / max(len(ref) + len(pred), 1)


def engine_files(slug: str) -> dict[str, str]:
    out: dict[str, str] = {}
    homr = WORK / slug / "homr.musicxml"
    if homr.exists():
        out["homr"] = str(homr)
    aud = next(iter((WORK / slug / "audiveris").glob("*.mxl")), None)
    if aud:
        out["audiveris"] = str(aud)
    rok = WORK / slug / "rokot_joined.mid"
    if rok.exists():
        out["rokot"] = str(rok)
    leg = WORK / slug / "legato_joined.mid"
    if leg.exists():
        out["legato"] = str(leg)
    krns = sorted((WORK / slug / "pages").glob("*_pred.krn"))
    if krns:
        out["transcoda"] = "|".join(str(k) for k in krns)
    return out


def load_engine(spec: str) -> list[int]:
    if "|" in spec:                       # transcoda: one kern file per page
        seq: list[int] = []
        for part_path in spec.split("|"):
            try:
                seq.extend(pitch_sequence(part_path))
            except Exception:  # noqa: BLE001
                continue
        return seq
    return pitch_sequence(spec)


def main() -> None:
    rows: dict[str, dict[str, object]] = {}
    for mid in sorted(TRUTH.glob("*.mid")):
        slug = mid.stem
        try:
            ref = pitch_sequence(str(mid))
        except Exception as exc:  # noqa: BLE001
            print(f"  {slug}: ground truth unreadable ({exc})")
            continue
        rows[slug] = {"ref_notes": len(ref)}
        for engine, spec in engine_files(slug).items():
            try:
                pred = load_engine(spec)
                rows[slug][engine] = {"ned": round(ned(ref, pred), 4), "notes": len(pred)}
            except Exception as exc:  # noqa: BLE001
                rows[slug][engine] = {"error": str(exc)[:80]}
        print(f"  {slug}: ref={len(ref)} " +
              " ".join(f"{e}={v['ned']}" for e, v in rows[slug].items()
                       if isinstance(v, dict) and "ned" in v), flush=True)
    (ROOT / "run/scores.json").write_text(json.dumps(rows, indent=2))

    engines = ["homr", "audiveris", "rokot", "legato", "transcoda"]
    print("\n  mean NED (lower is better, only pieces an engine completed):")
    for engine in engines:
        vals = [v[engine]["ned"] for v in rows.values()
                if isinstance(v.get(engine), dict) and "ned" in v[engine]]
        if vals:
            print(f"    {engine:12} {sum(vals)/len(vals):.4f}   over {len(vals)} pieces")


main()
