"""Count measures whose contents don't sum to the time signature."""
import warnings, re, collections
from music21 import converter

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    converter.parse("run/pathetique_homr.musicxml", forceSource=True)

overfull = [str(w.message) for w in caught if "overfull" in str(w.message)]
print(f"overfull measures: {len(overfull)}")
ratios = []
for m in overfull:
    hit = re.search(r"is overfull: (\S+) > ([\d.]+)", m)
    if hit:
        num, den = hit.group(1), hit.group(2)
        ratios.append((num, den))
for r, c in collections.Counter(ratios).most_common(10):
    print(f"  {r[0]} vs expected {r[1]}   x{c}")
