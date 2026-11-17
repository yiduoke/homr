"""Turn LEGATO's per-page ABC into one WAV per piece."""
import json, re, subprocess, sys, wave
from pathlib import Path
import numpy as np
from music21 import converter

ROOT = Path("/Users/yiduoke/Documents/homr")
SR, BPM = 22050, 100.0
H = [(1,1.0),(2,.45),(3,.22),(4,.12),(5,.06)]

def page_abc(p: Path) -> str:
    d = json.loads(p.read_text())
    abc = d["abc_transcription"]
    return (abc[0] if isinstance(abc, list) else abc)

def join_pages(slug: str) -> Path | None:
    pages = sorted(
        (ROOT/f"run/work/{slug}/pages").glob("page-*_run_models_legato_abc.json"),
        key=lambda p: int(re.search(r"page-(\d+)", p.name).group(1)))
    if not pages: return None
    header, order, defs = [], [], {}
    bodies: dict[str, list[str]] = {}
    for i, p in enumerate(pages):
        # Voice names are stable across pages; a page simply may not use them all.
        # Any voice missing from a page gets that page's worth of measure rests so
        # the voices stay aligned instead of sliding earlier.
        page_body: dict[str, list[str]] = {}
        cur = None
        for raw in page_abc(p).splitlines():
            line = raw.rstrip()
            if "<|text|>" in line:
                line = re.sub(r"\s*\w+=<\|text\|>", "", line)
                if "<|text|>" in line:
                    continue
            m = re.match(r"^V:\s*(\S+)\s+\S", line)
            if m:
                name = m.group(1)
                defs.setdefault(name, line)
                if name not in order: order.append(name)
                continue
            m = re.match(r"^V:\s*(\S+)\s*$", line)
            if m:
                cur = m.group(1)
                if cur not in order: order.append(cur)
                continue
            if re.match(r"^(X|T|C|L|M|K|I|Q|%%)", line):
                if i == 0: header.append(line)
                continue
            if cur and line.strip():
                page_body.setdefault(cur, []).append(line.strip())

        bars = max((sum(l.count("|") for l in v) for v in page_body.values()), default=0)
        for name in order:
            if name in page_body:
                bodies.setdefault(name, []).extend(page_body[name])
            elif bars:
                bodies.setdefault(name, []).append(f"Z{bars}")   # multi-measure rest

    out = list(header)
    for n in order:
        out.append(defs.get(n, f"V:{n}"))
    for n in order:
        if n in bodies:
            out.append(f"V:{n}\n" + "\n".join(bodies[n]))
    dst = ROOT/f"run/work/{slug}/legato_joined.abc"
    dst.write_text("\n".join(out)+"\n")
    return dst

def main(slug: str):
    abc = join_pages(slug)
    if abc is None: print("no legato output"); return
    mid = abc.with_suffix(".mid")
    subprocess.run(["abc2midi", str(abc), "-o", str(mid)], capture_output=True, text=True)
    s = converter.parse(str(mid), forceSource=True)
    ev = [(float(n.offset), float(n.quarterLength), p.midi)
          for pt in s.parts for n in pt.flatten().notes for p in n.pitches]
    spq = 60/BPM
    tot = max(o+d for o,d,_ in ev)*spq + 2
    buf = np.zeros(int(tot*SR)+SR)
    for o,d,m in ev:
        dur = max(d*spq, .05); n = int((dur+.35)*SR); t = np.arange(n)/SR
        f = 440*2**((m-69)/12)
        if f > SR/2.5: continue
        w = np.zeros(n)
        for k,a in H:
            if f*k < SR/2.5: w += a*np.sin(2*np.pi*f*k*t)
        st = int(o*spq*SR); buf[st:st+n] += w*np.exp(-t*3)*np.minimum(t/.006,1)*.16
    buf = buf/np.max(np.abs(buf))*.89
    dst = ROOT/f"run/out/{slug}__legato.wav"
    with wave.open(str(dst),"wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((buf*32767).astype(np.int16).tobytes())
    print(json.dumps({"wav": dst.name, "notes": len(ev), "minutes": round(tot/60,2)}))

main(sys.argv[1])
