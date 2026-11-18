"""ASAP MusicXML -> per-measure token lists with the FIXED tuplet converter (run/tuplet_wt, branch tuplet-fix: tuplet_tokens.fixed_tuplets,
typeless bar rests written as bar rests, printed tuplet values kept) and the same MeasureCutter as the pilot.
load(name) -> (voices, report, bad_shift) ; report = TupletReport of every non-exact tuplet note (measure index 0-based),
bad_shift = {measure: reason} for two-octave shifts (15ma/15mb), which the vocabulary cannot hold."""
import sys, os, zipfile
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/tuplet_wt")
from unittest import mock
for _m in ("augraphy","augraphy.base","augraphy.base.augmentationpipeline","augraphy.base.augmentation","augraphy.utilities","augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
import training.omr_datasets.music_xml_parser as mxp
from training.omr_datasets.music_xml_parser import music_xml_string_to_tokens
from training.omr_datasets.convert_lieder import MeasureCutter
from training.omr_datasets.tuplet_tokens import fixed_tuplets
ASAP = "/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/"
_bad = {}
_orig_shift = mxp._process_octave_shift
def _shift(part, el, staff):
    try: _orig_shift(part, el, staff)
    except ValueError as e:
        if "octave shifts by one octave" not in str(e): raise
        _bad[len(part.measures)] = "octave shift of two octaves (15ma/15mb) not in the vocabulary"
mxp._process_octave_shift = _shift

def xml_text(name):
    """score.xml with the hidden-cue fix of the pilot and, for a piece that declares more than 2 staves, the staves which hold only rests removed
    (their rests become <forward> so that the timeline stays), the others renumbered 1, 2. ASAP's Ravel Une barque has an empty third staff and
    its Liszt Gondoliera has 4 staves of which the first two are empty (the music is on 3 and 4): the converter folds higher staves into the
    lower staff, which gave spurious rests and mixed hands in the labels. A staff with notes beyond two would raise."""
    txt = zipfile.ZipFile(ASAP + name + ".mxl").read("score.xml").decode("utf-8").replace("<type>long</type>", "<type>breve</type>").replace("<type>256th</type>", "<type>128th</type>")
    import re as _re
    m = _re.search(r"<staves>(\d+)</staves>", txt)
    if not m or int(m.group(1)) <= 2: return txt
    import xml.etree.ElementTree as ET
    root = ET.fromstring(txt.encode()); n = int(m.group(1))
    has_notes = {s: False for s in range(1, n + 1)}
    for nt in root.iter("note"):
        if nt.find("rest") is None: has_notes[int(nt.findtext("staff") or 1)] = True
    keep = [s for s in range(1, n + 1) if has_notes[s]]
    if len(keep) != 2: raise ValueError(f"{name}: {len(keep)} staves with notes")
    new = {old: i + 1 for i, old in enumerate(keep)}
    for meas in root.iter("measure"):
        for idx, child in enumerate(list(meas)):
            if child.tag == "note":
                st = int(child.findtext("staff") or 1)
                if st in new: child.find("staff").text = str(new[st])
                else:
                    dur = child.findtext("duration"); pos = list(meas).index(child)
                    meas.remove(child)
                    if dur and child.find("chord") is None:
                        fw = ET.Element("forward"); ET.SubElement(fw, "duration").text = dur; meas.insert(pos, fw)
            elif child.tag in ("direction", "harmony", "figured-bass"):
                se = child.find("staff")
                if se is not None:
                    if int(se.text) in new: se.text = str(new[int(se.text)])
                    else: meas.remove(child)
    for st in root.iter("staves"): st.text = "2"
    for at in root.iter("attributes"):
        for c in list(at.findall("clef")):
            k = int(c.get("number") or 1)
            if k in new: c.set("number", str(new[k]))
            else: at.remove(c)
    return ET.tostring(root, encoding="unicode")

def load(name):
    _bad.clear()
    with fixed_tuplets(typeless_rests=True) as report:
        voices = music_xml_string_to_tokens(xml_text(name))
    return voices, report, dict(_bad)

def octave_state(name):
    """per measure (0-based): (open_at_start, open_at_end) = an 8va/8vb bracket is open (any staff) at the start / end of the measure, from the XML directions"""
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_text(name).encode()); out = []; open_ = set()
    for m in root.find("part").findall("measure"):
        st = bool(open_)
        for d in m.findall("direction"):
            for o in d.iter("octave-shift"):
                k = (o.get("number"), d.findtext("staff"))
                if o.get("type") in ("up", "down"): open_.add(k)
                elif o.get("type") == "stop": open_.discard(k)
        out.append((st, bool(open_)))
    return out

# The ASAP MusicXML of some pieces (Ravel Une barque) has voices whose summed <duration>s are a few ticks short of the following <backup>
# (a 9:8 group of 32nds written with 53 ticks each: 9 x 53 = 477 of 480). The parser then refuses the piece ("Backup duration is too long").
# Here (script only, parser file untouched): a shortfall of at most TOLERANCE ticks (divisions are 480 per quarter) puts the position at 0.
# Note values come from <type>, so token durations are unaffected; only the interleaving of voices in that measure can shift by a few ticks.
TOLERANCE = 12
TOLERATED = {}
_orig_apc = mxp.TokensMeasure.append_position_change
def _apc(self, duration):
    new_position = self.current_position + duration
    if -TOLERANCE <= new_position < 0:
        TOLERATED[id(self)] = TOLERATED.get(id(self), 0) + 1
        self.current_position = 0
        return
    return _orig_apc(self, duration)
mxp.TokensMeasure.append_position_change = _apc
