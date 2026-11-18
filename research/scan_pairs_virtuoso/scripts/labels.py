"""ASAP MusicXML -> per-measure token lists -> token text for a measure range (code of integration_wt: MeasureCutter)."""
import sys, os, zipfile, io
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/integration_wt")
from unittest import mock
for _m in ("augraphy","augraphy.base","augraphy.base.augmentationpipeline","augraphy.base.augmentation","augraphy.utilities","augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
from training.omr_datasets.music_xml_parser import music_xml_string_to_tokens
from training.omr_datasets.convert_lieder import MeasureCutter
from homr.transformer.vocabulary import EncodedSymbol
ASAP = "/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/"

import training.omr_datasets.music_xml_parser as mxp
ROUNDED = {}   # piece -> {0-based measure index: reason} for measures the converter cannot encode exactly (system is quarantined)
_orig_process_note = mxp._process_note
_current = {"name": None}
def _process_note(part, note):
    t = part.tuplets; saved = (t.open_tuplets, t.last_stop_position)
    try:
        _orig_process_note(part, note)
    except ValueError as e:
        if "Tuplet can't be encoded" not in str(e): raise
        t.open_tuplets, t.last_stop_position = saved
        ROUNDED.setdefault(_current["name"], {})[len(part.measures)] = "irregular tuplet (rhythm rounded by the converter)"
        part.sounding_pitch = True
        try: _orig_process_note(part, note)
        finally: part.sounding_pitch = False
mxp._process_note = _process_note
_orig_shift = mxp._process_octave_shift
def _process_octave_shift(part, el, staff):
    try: _orig_shift(part, el, staff)
    except ValueError as e:
        if "octave shifts by one octave" not in str(e): raise
        ROUNDED.setdefault(_current["name"], {})[len(part.measures)] = "octave shift of two octaves (15ma/15mb) not in the vocabulary"
mxp._process_octave_shift = _process_octave_shift

def load(name):
    _current["name"] = name
    z = zipfile.ZipFile(ASAP + name + ".mxl")
    txt = z.read("score.xml").decode("utf-8").replace("<type>long</type>", "<type>breve</type>")  # hidden cue notes of ASAP Beethoven 14-3
    return music_xml_string_to_tokens(txt)

def tok_text(symbols):
    from training.transformer.training_vocabulary import token_lines_to_str
    return token_lines_to_str(symbols)

if __name__ == "__main__":
    voices = load(sys.argv[1])
    print(len(voices), [len(v) for v in voices])
    v = voices[0]
    mc = MeasureCutter(list(v))
    n = int(sys.argv[2])
    syms = mc.extract_measures(n)
    print(tok_text(syms))
