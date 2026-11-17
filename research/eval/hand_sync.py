"""How well do the two hand parts of a Schott Liszt output stay on the same bar? Each hand is aligned to the reference staff on its own
(same DP as the scorer); for every output bar where both hands were matched we check that they point to the same reference bar.
usage: python hand_sync.py OUT.musicxml REF.musicxml   (run with cwd=integration_wt, PYTHONPATH=.)"""
import sys
from pathlib import Path
from validation.score_notes import parse_musicxml, align_measures, _staff_bars, Score
def sync(pred_path, ref_path):
    ref, pred = parse_musicxml(Path(ref_path).read_text()), parse_musicxml(Path(pred_path).read_text())
    rb, pb = _staff_bars(ref), _staff_bars(pred)
    maps = []
    for k in range(2):
        pairs = align_measures(Score(rb[k], 2), Score(pb[k], 2))
        maps.append({j: i for i, j in pairs})
    n = min(len(pb[0]), len(pb[1]))
    both = [j for j in range(n) if j in maps[0] and j in maps[1]]
    same = sum(maps[0][j] == maps[1][j] for j in both)
    off = [maps[0][j] - maps[1][j] for j in both if maps[0][j] != maps[1][j]]
    return dict(bars=(len(pb[0]), len(pb[1])), both_matched=len(both), same_ref_bar=same, pct=100 * same / max(1, len(both)),
                max_offset=max((abs(o) for o in off), default=0))
if __name__ == "__main__":
    print(sync(sys.argv[1], sys.argv[2]))
