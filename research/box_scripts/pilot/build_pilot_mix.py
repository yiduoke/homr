"""Build the two training lists of the pilot on the training box: base mixture + R copies of the pilot passages, same order in both arms.

usage (on vast-homr4, after upload_pilot.sh):
  /venv/main/bin/python build_pilot_mix.py [--repeat 8] [--seed 20261120] [--groups A,B] [--base ...] [--out /workspace/pilot/mix]

Inputs: the base list of the run-3 control (/workspace/run3/run2_train_excl_v3.txt, 107,444 lines `image,tokens`, absolute paths) and the two paired pilot lists
(/workspace/pilot/lists/pilot_twin_render.txt and pilot_scan.txt: identical line order, identical token files).
Output: mix_CTRL_RENDER_R<R>.txt and mix_SCAN_R<R>.txt. Line i of both files is the same passage (same tokens, same position in the list), only the image differs
(rendered twin or scanned crop). Both are shuffled with the same seed, so the trainer (same FT_SEED, same list length) shows the same passage in the same step in
both arms. Base lines are identical in both files. Checks: all files exist, token columns identical, no pilot path appears twice per copy.
Prints the exposure arithmetic for FT_MAX_STEPS (default 6716) at 32 samples per update.
--groups A (or A,B,...): keep only pilot passages of these groups (first letter of the crop name); default all. Group B pieces are already in the rendered mixture.
"""
import argparse, json, os, random, sys

ap = argparse.ArgumentParser()
ap.add_argument("--base", default="/workspace/run3/run2_train_excl_v3.txt")
ap.add_argument("--twin", default="/workspace/pilot/lists/pilot_twin_render.txt")
ap.add_argument("--scan", default="/workspace/pilot/lists/pilot_scan.txt")
ap.add_argument("--repeat", type=int, default=8)
ap.add_argument("--seed", type=int, default=20261120)
ap.add_argument("--groups", default="A,B,C")   # v2: C = Sonata 2 mvt 2 (C2), moved from validation to the train side; not in the rendered mixture
ap.add_argument("--steps", type=int, default=6716)
ap.add_argument("--batch", type=int, default=32)
ap.add_argument("--out", default="/workspace/pilot/mix")
a = ap.parse_args()
groups = set(a.groups.split(","))
base = [l.strip() for l in open(a.base) if l.strip()]
tw = [l.strip() for l in open(a.twin) if l.strip()]
sc = [l.strip() for l in open(a.scan) if l.strip()]
assert len(tw) == len(sc), (len(tw), len(sc))
keep = [i for i in range(len(tw)) if os.path.basename(sc[i].split(",")[0])[0] in groups]
tw, sc = [tw[i] for i in keep], [sc[i] for i in keep]
for t, s in zip(tw, sc):
    assert t.split(",")[1] == s.split(",")[1], (t, s)                    # same token file
    assert os.path.basename(t.split(",")[0]) == os.path.basename(s.split(",")[0]), (t, s)
    for p in (t.split(",")[0], s.split(",")[0], s.split(",")[1]):
        assert os.path.exists(p), p
n_pilot = len(tw)
slots = [("b", i) for i in range(len(base))] + [("p", i) for _ in range(a.repeat) for i in range(n_pilot)]
random.Random(a.seed).shuffle(slots)
os.makedirs(a.out, exist_ok=True)
for arm, plist in (("CTRL_RENDER", tw), ("SCAN", sc)):
    path = f"{a.out}/mix_{arm}_R{a.repeat}{'' if groups == {'A', 'B', 'C'} else '_' + ''.join(sorted(groups))}.txt"
    with open(path, "w") as f:
        for kind, i in slots:
            f.write((base[i] if kind == "b" else plist[i]) + "\n")
    print("wrote", path)
N = len(slots)
epochs = a.steps * a.batch / N
info = dict(base_lines=len(base), pilot_passages=n_pilot, repeat=a.repeat, pilot_lines=n_pilot * a.repeat, total_lines=N, pilot_share=n_pilot * a.repeat / N,
            steps=a.steps, samples=a.steps * a.batch, epochs_over_list=epochs, exposures_per_pilot_passage=a.repeat * epochs,
            pilot_samples_in_run=a.steps * a.batch * n_pilot * a.repeat / N, exposures_per_base_line=epochs, seed=a.seed, groups=sorted(groups))
json.dump(info, open(f"{a.out}/mix_info_R{a.repeat}.json", "w"), indent=1)
print(json.dumps(info, indent=1))
