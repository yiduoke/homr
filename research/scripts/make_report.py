"""Build the comparison report from run/results.json.

Every cell links to the WAV it produced, so the table is playable rather than
just readable.
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path("/Users/yiduoke/Documents/homr")
RESULTS = ROOT / "run/results.json"
OUT_HTML = ROOT / "run/report.html"
WAV_DIR = ROOT / "run/out"

ENGINE_ORDER = ["homr", "audiveris", "rokot", "legato", "transcoda"]
ENGINE_LABEL = {
    "homr": "homr",
    "audiveris": "Audiveris",
    "rokot": "rokot-omr-2b",
    "legato": "LEGATO",
    "transcoda": "transcoda",
}

data = json.loads(RESULTS.read_text())
engines = [e for e in ENGINE_ORDER if any(e in v["engines"] for v in data.values())]

rows = []
for slug, piece in sorted(data.items(), key=lambda kv: kv[1]["title"].lower()):
    cells = []
    for engine in engines:
        row = piece["engines"].get(engine)
        if row is None:
            cells.append('<td class="skip">not run</td>')
        elif "error" in row:
            err = row["error"].replace("<", "&lt;").strip()[:180]
            cells.append(f'<td class="fail"><b>failed</b><div class="err">{err}</div></td>')
        else:
            wav = WAV_DIR / row["wav"]
            secs = row.get("seconds", 0)
            # rokot works system-by-system and never forms measures, so the unit
            # of structure it reports differs from the other engines'.
            if "measures" in row:
                scale = f'{row["measures"]} bars'
            elif "systems" in row:
                empty = row.get("empty_systems", 0)
                scale = f'{row["systems"]} systems' + (f' ({empty} blank)' if empty else "")
            else:
                scale = ""
            timing = f' · {secs:.0f}s to run' if secs else ""
            cells.append(
                f'<td class="ok"><a href="{wav.as_uri()}">▶ play</a>'
                f'<div class="stat">{row["notes"]:,} notes · {scale}</div>'
                f'<div class="stat dim">{row["minutes"]} min audio{timing}</div></td>'
            )
    pages = next(
        (r.get("pages") for r in piece["engines"].values() if isinstance(r, dict) and r.get("pages")),
        "",
    )
    page_note = f'<div class="stat dim">{pages} pages</div>' if pages else ""
    rows.append(
        f'<tr><th>{piece["title"]}{page_note}</th>' + "".join(cells) + "</tr>"
    )

head = "".join(f"<th>{ENGINE_LABEL.get(e, e)}</th>" for e in engines)
total = sum(len(v["engines"]) for v in data.values())
ok = sum(1 for v in data.values() for r in v["engines"].values() if "error" not in r)

OUT_HTML.write_text(f"""<!doctype html>
<meta charset="utf-8">
<title>OMR engine comparison</title>
<style>
  body {{ font: 15px/1.5 -apple-system, system-ui, sans-serif; margin: 2.5rem auto; max-width: 1100px;
         color: #1a1a1a; padding: 0 1.5rem; }}
  h1 {{ font-size: 1.5rem; margin-bottom: .2rem; }}
  .sub {{ color: #666; margin-bottom: 1.8rem; font-size: .9rem; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #e2e2e2; padding: .6rem .7rem; text-align: left; vertical-align: top; }}
  thead th {{ background: #f6f6f6; font-size: .85rem; text-transform: uppercase; letter-spacing: .04em; }}
  tbody th {{ background: #fafafa; font-weight: 600; width: 22%; }}
  td.ok a {{ font-weight: 600; text-decoration: none; color: #0a58ca; }}
  td.ok a:hover {{ text-decoration: underline; }}
  td.fail {{ background: #fff5f5; }}
  td.skip {{ color: #999; font-style: italic; }}
  .stat {{ font-size: .82rem; color: #444; margin-top: .25rem; }}
  .stat.dim {{ color: #888; }}
  .err {{ font: 11px/1.35 ui-monospace, Menlo, monospace; color: #a33; margin-top: .3rem;
          white-space: pre-wrap; word-break: break-word; }}
</style>
<h1>OMR engine comparison</h1>
<div class="sub">{len(data)} scores · {ok}/{total} cells succeeded ·
generated {datetime.now().strftime("%Y-%m-%d %H:%M")}<br>
Every WAV uses the same crude additive synth, so differences are recognition, not playback.</div>
<table>
  <thead><tr><th>Score</th>{head}</tr></thead>
  <tbody>{"".join(rows)}</tbody>
</table>
""")
print(f"wrote {OUT_HTML}  ({ok}/{total} cells ok)")
