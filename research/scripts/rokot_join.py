"""Join rokot's per-system ABC into one tune per piece, voice by voice.

The earlier pass converted each system to MIDI and laid them end to end, which
restarts every voice at each system boundary. rokot's own card calls the missing
step "measure-wise joining": one header, and each voice's music lines
concatenated across systems so the voices stay parallel the whole way down.

    python rokot_join.py <slug> [<slug> ...]
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path("/Users/yiduoke/Documents/homr")
WORK = ROOT / "run/work"

HEADER_FIELDS = ("X:", "M:", "L:", "K:", "Q:")
VOICE_DEF = re.compile(r"^V:\s*(\S+)(.*)$")
VOICE_LINE = re.compile(r"^\[V:\s*([^\]]+)\]\s*(.*)$")


def parse_system(text: str) -> tuple[dict, dict, list]:
    """Split one system's ABC into header fields, voice definitions and music."""
    header: dict[str, str] = {}
    voice_defs: dict[str, str] = {}
    music: dict[str, list[str]] = {}
    order: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("%"):
            continue
        if any(line.startswith(f) for f in HEADER_FIELDS):
            header.setdefault(line[:2], line[2:].strip())
            continue
        m = VOICE_DEF.match(line)
        if m and not line.startswith("[V:"):
            name = m.group(1)
            voice_defs.setdefault(name, m.group(2).strip())
            if name not in order:
                order.append(name)
            continue
        m = VOICE_LINE.match(line)
        if m:
            name = m.group(1).strip()
            music.setdefault(name, []).append(m.group(2).strip())
            if name not in order:
                order.append(name)
    return header, voice_defs, {k: " ".join(v) for k, v in music.items()}


def join(slug: str) -> Path | None:
    abcs = sorted((WORK / slug / "rokot").glob("sys-*.abc"))
    if not abcs:
        return None

    header: dict[str, str] = {}
    voice_defs: dict[str, str] = {}
    order: list[str] = []
    bodies: dict[str, list[str]] = {}

    for abc in abcs:
        text = abc.read_text().strip()
        if not text:
            continue
        h, defs, music = parse_system(text)
        for k, v in h.items():
            header.setdefault(k, v)          # first system's header wins
        for name, spec in defs.items():
            voice_defs.setdefault(name, spec)
            if name not in order:
                order.append(name)
        for name, line in music.items():
            if name not in order:
                order.append(name)
            bodies.setdefault(name, []).append(line)

    if not bodies:
        return None

    out = ["%%rokot-abc 0.1", f"X:{header.get('X:', '1')}"]
    for field in ("M:", "L:", "Q:"):
        if field in header:
            out.append(f"{field}{header[field]}")
    out.append(f"K:{header.get('K:', 'C')}")
    for name in order:
        if name in bodies:
            out.append(f"V:{name} {voice_defs.get(name, '')}".rstrip())
    for name in order:
        if name in bodies:
            out.append(f"[V:{name}] " + " ".join(bodies[name]))

    dst = WORK / slug / "rokot_joined.abc"
    dst.write_text("\n".join(out) + "\n")
    return dst


def main() -> None:
    for slug in sys.argv[1:]:
        joined = join(slug)
        if joined is None:
            print(f"  {slug}: no ABC to join")
            continue
        mid = WORK / slug / "rokot_joined.mid"
        proc = subprocess.run(
            ["abc2midi", str(joined), "-o", str(mid)],
            capture_output=True, text=True, timeout=300,
        )
        warns = len([l for l in proc.stdout.splitlines() if "Warning" in l])
        voices = sum(1 for l in joined.read_text().splitlines() if l.startswith("[V:"))
        print(f"  {slug}: {voices} voices, {warns} abc2midi warnings -> {mid.name}")


main()
