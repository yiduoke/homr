"""Render the windows of the meter arm into staff images and current-format token files.
usage: render_windows.py vrv <plan.jsonl> <outdir> [k n]     Verovio (fonts, scale, time-signature size by SVG edit)
       render_windows.py ms  <plan.jsonl> <outdir> [k n]     MuseScore 4.6.5 (font style via -S, time-signature scale in the mscx)
Labels: music_xml_file_to_tokens + MeasureCutter of the homr_acc code (copy in code/), the same functions that made the
run-3 hard-PDMX / ASAP labels (Verovio: the window's own MusicXML; MuseScore: the MusicXML which MuseScore exports from the
same mscx that is drawn). Courtesy clefs/keys/time signatures of MuseScore are switched off so that every drawn symbol is labelled.
Writes <outdir>/staffs_<renderer>_<k>.jsonl (one line per staff image).
Run with nice -n 19.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, "/workspace/run4/meters/code")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

from training.omr_datasets import convert_lieder as CL  # noqa: E402
from training.omr_datasets import verovio_staffs as VS  # noqa: E402
from training.omr_datasets.music_xml_parser import music_xml_file_to_tokens  # noqa: E402

CL.git_root = Path("/")  # index lines are written with absolute paths
APPRUN = "/workspace/run4/meters/ms_extract/squashfs-root/AppRun"
STYLE_DIR = "/workspace/run4/meters/ms_styles"


# ----------------------------------------------------------------------------- Verovio
def scale_meter_sigs(svg: str, k: float) -> str:
    """Scale every digit/C of the time signatures about its own centre (rows of the num/den by baseline y)."""
    if abs(k - 1.0) < 1e-6:
        return svg
    out = []
    pos = 0
    for m in re.finditer(r'<g id="[^"]*" class="meterSig">', svg):
        start = m.start()
        if start < pos:
            continue
        # find matching </g>
        depth = 0
        i = start
        end = None
        for t in re.finditer(r"<g\b|</g>", svg[start:]):
            if t.group(0).startswith("<g"):
                depth += 1
            else:
                depth -= 1
                if depth == 0:
                    end = start + t.end()
                    break
        if end is None:
            continue
        block = svg[start:end]
        rect = re.search(r'<rect x="([\d.-]+)" y="([\d.-]+)" height="([\d.-]+)" width="([\d.-]+)"', block)
        if rect is None:
            continue
        cx = float(rect.group(1)) + float(rect.group(4)) / 2

        def fix(u):
            x, y, s = float(u.group(1)), float(u.group(2)), float(u.group(3))
            nx = cx + (x - cx) * k
            return f'transform="translate({nx:.0f}, {y:.0f}) scale({s * k:.4f}, {s * k:.4f})"'

        new = re.sub(r'transform="translate\(([\d.-]+), ([\d.-]+)\) scale\(([\d.]+), [\d.]+\)"', fix, block)
        # horizontal origin of a glyph is its left edge: moving the origin to cx + (x-cx)k keeps the row centred only if the
        # glyph's own half width shrinks too; correct by half of the lost width (glyph width ~ 0.5 staff space * scale, measured below)
        out.append((start, end, new))
        pos = end
    res = svg
    for start, end, new in reversed(out):
        res = res[:start] + new + res[end:]
    return res


def _depth_end(svg, start):
    depth = 0
    for t in re.finditer(r"<g\b|</g>", svg[start:]):
        if t.group(0).startswith("<g"):
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start + t.end()
    return None


def remove_cautionary(svg: str) -> str:
    """Verovio draws the key/time signature (and clef) of a change at the start of the next system again at the end of the
    system, after the last note; those are not in the labels, so they are cut out. Only direct children of a staff
    (not in a layer) lying to the right of every note of that staff are touched."""
    root = ET.fromstring(svg)  # noqa: S314
    S = "{http://www.w3.org/2000/svg}"
    ids = []

    def cls(e):
        return (e.get("class") or "").split(" ")[0]

    def ux(g):
        for u in g.iter(S + "use"):
            m = re.search(r"translate\(([\d.-]+)", u.get("transform", ""))
            if m:
                return float(m.group(1))
        return None

    for staff in root.iter(S + "g"):
        if cls(staff) != "staff":
            continue
        note_x = [ux(g) for g in staff.iter(S + "g") if cls(g) in ("note", "rest", "chord", "mRest") and ux(g) is not None]
        if not note_x:
            continue
        right = max(note_x)
        for child in staff:
            if child.tag == S + "g" and cls(child) in ("keySig", "meterSig", "clef"):
                x = ux(child)
                if x is not None and x > right:
                    ids.append(child.get("id"))
    for i in ids:
        m = re.search(r'<g id="' + re.escape(i) + r'"[^>]*>', svg)
        if m:
            end = _depth_end(svg, m.start())
            if end:
                svg = svg[: m.start()] + svg[end:]
    return svg


class VrvStyle:
    font = "Leipzig"
    scale = 40
    tsscale = 1.0


def render_styled(musicxml_file: str, name: str) -> VS.VerovioScore:
    import verovio  # noqa: PLC0415

    root = ET.parse(musicxml_file).getroot()
    clef_changes = VS.clef_changes_within_measures(root)
    VS.fill_voices(root)
    toolkit = verovio.toolkit()
    toolkit.setOptions({"pageWidth": 2100, "pageHeight": 2970, "scale": VrvStyle.scale, "font": VrvStyle.font, "header": "none",
                        "footer": "none", "svgBoundingBoxes": True})
    if not toolkit.loadData(ET.tostring(root, encoding="unicode")):
        raise ValueError("Verovio failed to load " + musicxml_file)
    pages, systems = [], []
    for page in range(1, toolkit.getPageCount() + 1):
        svg = toolkit.renderToSVG(page)
        first_measure = sum(s.bars for s in systems)
        systems.extend(VS.parse_page(svg, page, first_measure, clef_changes))
        pages.append(scale_meter_sigs(remove_cautionary(svg), VrvStyle.tsscale))
    return VS.VerovioScore(pages, systems)


def run_vrv(plan, outdir, k, n):
    VS.render = render_styled
    flat = Path(outdir) / "flat"
    flat.mkdir(parents=True, exist_ok=True)
    out = open(Path(outdir) / f"staffs_vrv_{k}.jsonl", "a")
    specs = [json.loads(ln) for ln in open(plan)]
    specs = [s for s in specs if s["renderer"] == "vrv"][k::n]
    done = fail = 0
    att_file = Path(outdir) / f"attempts_vrv_{k}.txt"
    finished = set()
    jf = Path(outdir) / f"staffs_vrv_{k}.jsonl"
    for ln in open(jf):
        r = json.loads(ln)
        finished.add(r.get("spec") or r.get("wid"))
    attempted = set(att_file.read_text().split()) if att_file.exists() else set()
    att = open(att_file, "a")
    for spec in specs:
        wid = spec["wid"]
        if wid in finished or wid in attempted:
            continue  # done before, or it crashed the process (Verovio segfault) on an earlier run
        att.write(wid + "\n")
        att.flush()
        xml = f"/workspace/run4/meters/xml/{spec['round']}/{wid}.musicxml"
        VrvStyle.font, VrvStyle.scale, VrvStyle.tsscale = spec["font"], spec["vrv_scale"], spec["tsscale"]
        try:
            voices = music_xml_file_to_tokens(xml)
            staves_per_part = [CL.get_svg_voice_count(v) for v in voices]
            if VS.has_multi_measure_rests(xml):
                raise ValueError("mmrest")
            staffs = VS.split_into_staffs(xml, voices, staves_per_part, set(range(len(voices))), False, str(flat))
        except Exception as e:  # noqa: BLE001
            fail += 1
            out.write(json.dumps({"wid": wid, "error": repr(e)[:200]}) + "\n")
            continue
        if not staffs:
            fail += 1
            out.write(json.dumps({"wid": wid, "error": "no staffs"}) + "\n")
            continue
        for _part, image, tokens, symbols in staffs:
            CL._write_tokens(image, tokens, symbols)
            rec = dict(spec=wid, image=image, tokens=tokens, renderer="vrv", font=spec["font"], scale=spec["vrv_scale"],
                       tsclass=spec["tsclass"], tsscale=spec["tsscale"], kind=spec["kind"], pool=spec["pool"])
            out.write(json.dumps(rec) + "\n")
        out.flush()
        done += 1
    print("vrv windows", done, "failed", fail, flush=True)


# ----------------------------------------------------------------------------- MuseScore
def style_file(font):
    os.makedirs(STYLE_DIR, exist_ok=True)
    p = f"{STYLE_DIR}/{font}.mss"
    if not os.path.exists(p):
        Path(p).write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<museScore version="4.00">\n  <Style>\n'
            f"    <musicalSymbolFont>{font}</musicalSymbolFont>\n    <musicalTextFont>{font} Text</musicalTextFont>\n"
            "    <genCourtesyTimesig>0</genCourtesyTimesig>\n    <genCourtesyKeysig>0</genCourtesyKeysig>\n"
            "    <genCourtesyClef>0</genCourtesyClef>\n  </Style>\n</museScore>\n"
        )
    return p


def musescore(style, jobs):
    jf = f"/workspace/run4/meters/ms_work/job_{os.getpid()}.json"
    Path(jf).write_text(json.dumps(jobs))
    env = dict(os.environ, APPIMAGE_EXTRACT_AND_RUN="1", QT_QPA_PLATFORM="offscreen")
    cmd = ["xvfb-run", "-a", APPRUN, "--force"] + (["-S", style] if style else []) + ["-j", jf]
    subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)  # noqa: S603


def run_ms(plan, outdir, k, n):
    work = Path(f"/workspace/run4/meters/ms_work/{Path(outdir).name}_{k}")
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    flat = Path(outdir) / "flat"
    flat.mkdir(parents=True, exist_ok=True)
    out = open(Path(outdir) / f"staffs_ms_{k}.jsonl", "a")
    specs = [json.loads(ln) for ln in open(plan)]
    specs = [s for s in specs if s["renderer"] == "ms"][k::n]
    by_font = {}
    for s in specs:
        by_font.setdefault(s["font"], []).append(s)
    CL._verovio_staffs = lambda *a, **kw: (set(), [])
    for font, group in by_font.items():
        for b0 in range(0, len(group), 40):
            batch = group[b0 : b0 + 40]
            jobs1 = []
            for s in batch:
                src = f"/workspace/run4/meters/xml/{s['round']}/{s['wid']}.musicxml"
                jobs1.append({"in": src, "out": f"{work}/{s['wid']}.mscx"})
            musescore(style_file(font), jobs1)
            jobs2 = []
            ok = []
            for s in batch:
                m = work / f"{s['wid']}.mscx"
                if not m.exists():
                    out.write(json.dumps({"wid": s["wid"], "error": "mscx"}) + "\n")
                    continue
                if abs(s["tsscale"] - 1.0) > 1e-6:
                    t = m.read_text(encoding="utf-8")
                    t = re.sub(r"(<sigD>\d+</sigD>)", rf'\1<scale w="{s["tsscale"]}" h="{s["tsscale"]}"/>', t)
                    m.write_text(t, encoding="utf-8")
                jobs2.append({"in": str(m), "out": f"{work}/{s['wid']}x.musicxml"})
                jobs2.append({"in": str(m), "out": f"{work}/{s['wid']}x.svg"})
                ok.append(s)
            musescore(None, jobs2)
            for s in ok:
                wid = s["wid"]
                xml = work / f"{wid}x.musicxml"
                if not xml.exists() or not list(work.glob(f"{wid}x-*.svg")):
                    out.write(json.dumps({"wid": wid, "error": "export"}) + "\n")
                    continue
                try:
                    lines = CL.convert_xml_and_svg_file(xml, False, str(flat), fail_if_image_is_missing=False)
                except Exception as e:  # noqa: BLE001
                    lines = []
                    out.write(json.dumps({"wid": wid, "error": "convert " + repr(e)[:150]}) + "\n")
                    continue
                if not lines:
                    out.write(json.dumps({"wid": wid, "error": "no staffs"}) + "\n")
                    continue
                for ln in lines:
                    image, tokens = ln.strip().split(",")
                    rec = dict(spec=wid, image="/" + image, tokens="/" + tokens, renderer="ms", font=font, scale=None,
                               tsclass=s["tsclass"], tsscale=s["tsscale"], kind=s["kind"], pool=s["pool"])
                    out.write(json.dumps(rec) + "\n")
                out.flush()
                shutil.copy(xml, Path(outdir) / "xml_ms" / xml.name) if (Path(outdir) / "xml_ms").exists() else None
            for f in work.glob("*.svg"):
                f.unlink()
    print("ms done", flush=True)


if __name__ == "__main__":
    mode, plan, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    k, n = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (0, 1)
    os.makedirs("/workspace/run4/meters/ms_work", exist_ok=True)
    (run_vrv if mode == "vrv" else run_ms)(plan, outdir, k, n)
