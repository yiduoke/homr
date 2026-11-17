"""Run every OMR engine over every score in run/scores/ and record what happened.

Each (piece, engine) pair produces a WAV plus a row of stats, or an error string
if the engine choked. Nothing aborts the run -- a failure on one cell is data.

    HOMR_ENGINES=homr,audiveris python run/pipeline.py
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/Users/yiduoke/Documents/homr")
SCORES = ROOT / "run/scores"
WORK = ROOT / "run/work"
OUT = ROOT / "run/out"
RESULTS = ROOT / "run/results.json"
AUDIVERIS = Path("/Users/yiduoke/Documents/audiveris")
JAVA_HOME = "/opt/homebrew/opt/openjdk@25/libexec/openjdk.jdk/Contents/Home"

ENGINES = os.environ.get("HOMR_ENGINES", "homr,audiveris").split(",")
DPI = "150"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = 3600):
    merged = {**os.environ, **(env or {})}
    return subprocess.run(
        cmd, cwd=cwd, env=merged, capture_output=True, text=True, timeout=timeout
    )


def uvrun(args: list[str], env: dict | None = None, timeout: int = 3600):
    return run(["uv", "run", "--no-sync", *args], cwd=ROOT, env=env, timeout=timeout)


def source_pages(pages_dir: Path) -> list[Path]:
    """Rendered pages only -- homr writes page-N_teaser.png debug images alongside."""
    return sorted(p for p in pages_dir.glob("page-*.png") if "_teaser" not in p.name)


def render_pages(pdf: Path, pages_dir: Path) -> int:
    pages_dir.mkdir(parents=True, exist_ok=True)
    if not list(pages_dir.glob("page-[0-9]*.png")):
        run(["pdftoppm", "-r", DPI, "-png", str(pdf), str(pages_dir / "page")])
    return len(source_pages(pages_dir))


def engine_homr(pdf: Path, slug: str) -> dict:
    pages_dir = WORK / slug / "pages"
    n = render_pages(pdf, pages_dir)
    for page in source_pages(pages_dir):
        if page.with_suffix(".musicxml").exists():
            continue
        r = uvrun(["homr", "--write-staff-positions", str(page)], timeout=1800)
        if r.returncode != 0 and not page.with_suffix(".musicxml").exists():
            return {"error": f"homr failed on {page.name}: {r.stderr.strip()[-200:]}"}

    env = {
        "HOMR_PAGES": str(pages_dir),
        "HOMR_OUT": str(WORK / slug / "homr"),
        "HOMR_TEMPO_MAP": str(WORK / slug / "tempo.json"),
    }
    uvrun(["python", "run/build_tempo_map.py"], env=env, timeout=1800)
    r = uvrun(["python", "run/merge_pages.py"], env=env, timeout=1800)
    merged = WORK / slug / "homr.musicxml"
    if not merged.exists():
        return {"error": f"merge failed: {r.stderr.strip()[-200:]}"}

    wav = OUT / f"{slug}__homr.wav"
    r = uvrun(
        ["python", "run/render_score.py", str(merged), str(wav), env["HOMR_TEMPO_MAP"]],
        timeout=1800,
    )
    if r.returncode != 0:
        return {"error": f"render failed: {r.stderr.strip()[-200:]}"}
    stats = json.loads(r.stdout.strip().splitlines()[-1])
    return {"wav": wav.name, "pages": n, **stats}


def engine_audiveris(pdf: Path, slug: str) -> dict:
    out_dir = WORK / slug / "audiveris"
    out_dir.mkdir(parents=True, exist_ok=True)
    mxl = next(iter(out_dir.glob("*.mxl")), None)
    if mxl is None:
        # Gradle splits --args on whitespace, so a filename with spaces arrives as
        # several arguments and Audiveris sees garbage. Stage a space-free copy.
        staged = out_dir / f"{slug}.pdf"
        if not staged.exists():
            shutil.copy(pdf, staged)
        r = run(
            [
                "./gradlew", "run", "--console=plain",
                f"--args=-batch -transcribe -export -output {out_dir} {staged}",
            ],
            cwd=AUDIVERIS,
            env={"JAVA_HOME": JAVA_HOME, "PATH": f"{JAVA_HOME}/bin:{os.environ['PATH']}"},
            timeout=5400,
        )
        mxl = next(iter(out_dir.glob("*.mxl")), None)
        if mxl is None:
            return {"error": f"audiveris produced no mxl: {r.stdout.strip()[-200:]}"}

    wav = OUT / f"{slug}__audiveris.wav"
    tempo = WORK / slug / "tempo.json"
    args = ["python", "run/render_score.py", str(mxl), str(wav)]
    if tempo.exists():
        args.append(str(tempo))
    r = uvrun(args, timeout=1800)
    if r.returncode != 0:
        return {"error": f"render failed: {r.stderr.strip()[-200:]}"}
    stats = json.loads(r.stdout.strip().splitlines()[-1])
    return {"wav": wav.name, **stats}


RUNNERS = {"homr": engine_homr, "audiveris": engine_audiveris}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}

    pdfs = sorted(p for p in SCORES.glob("*.pdf"))
    for pdf in pdfs:
        slug = slugify(pdf.stem)
        results.setdefault(slug, {"title": pdf.stem, "engines": {}})
        for engine in ENGINES:
            if engine in results[slug]["engines"] and "error" not in results[slug]["engines"][engine]:
                continue
            print(f"[{slug}] {engine} ...", flush=True)
            started = time.time()
            try:
                row = RUNNERS[engine](pdf, slug)
            except Exception as exc:  # noqa: BLE001 -- a crash is a result too
                row = {"error": f"{type(exc).__name__}: {exc}"[:220]}
            row["seconds"] = round(time.time() - started, 1)
            results[slug]["engines"][engine] = row
            RESULTS.write_text(json.dumps(results, indent=2))
            print(f"[{slug}] {engine} -> {row}", flush=True)

    print(json.dumps(results, indent=2)[:400])


main()
