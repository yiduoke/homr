"""Run 1 training/validation lists, mirroring training/transformer/build_round3_index.py.
Run from /workspace/homr_meter with PYTHONPATH=. ; writes /workspace/run1/*."""
import collections
import hashlib
import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, "/workspace/clean_index")
from homr.transformer.configs import Config  # noqa: E402
from training.transformer import train as base  # noqa: E402
from training.transformer.data_loader import _filter_valid_samples, load_dataset  # noqa: E402
from training.transformer.training_vocabulary import check_token_lines, read_tokens  # noqa: E402

R566 = "/workspace/homr566"
R = "/workspace/homr"
OUT = "/workspace/run1"
os.makedirs(OUT, exist_ok=True)
N_ORIG, N_VAL, REPEAT, HOLD, OTHERS, VB = 70000, 4000, 2, 0.1, 2, 1
R3_EXPOSURES = int(os.environ.get("R3_EXPOSURES", "13798"))
rng = random.Random(20261113)


def rd(p):
    return [ln.strip() for ln in open(p) if ln.strip()]


def absl(line, root):
    a, b = line.split(",")
    return f"{root}/{a},{root}/{b}\n"


def rel(line, root):
    return line.strip().replace(root + "/", "")


def _score_of(line):
    name = Path(line.split(",", 1)[0]).name.rsplit("-", 2)[0]
    return re.sub(r"(oct\d?)?(v\d)?$", "", name)


def _is_aug(line):
    return bool(re.search(r"oct\d?(v\d)?-\d+-\d+\.png", line.split(",", 1)[0]))


def _held(score, share):
    d = int(hashlib.sha256(("holdout" + score).encode()).hexdigest(), 16)
    return (d % 10_000) / 10_000 < share


_cache = {}


def tok(line):
    p = line.strip().split(",")[1]
    if p not in _cache:
        _cache[p] = open(p).read()
    return _cache[p]


def in_vocab(lines):
    out = []
    for ln in lines:
        try:
            check_token_lines(read_tokens(ln.strip().split(",")[1]))
        except Exception:  # noqa: BLE001
            continue
        out.append(ln)
    return out


def pid(line):
    return re.sub(r"-vrv$", "", Path(line.split(",", 1)[0]).name.rsplit("-", 2)[0])


stats = {}
# ---- original sources
lieder = rd(f"{R566}/datasets_meter/Lieder-main/index.txt")
gs = rd(f"{R566}/datasets_meter/grandstaff/index.txt")
pdmx = rd(f"{R566}/datasets_meter/pdmx/index.txt")
hard = rd(f"{R566}/datasets_meter/pdmx/hard/index.txt")
main_ids = {pid(ln) for ln in rd(f"{R566}/datasets/pdmx/index.txt")}
hard_ids = {pid(ln) for ln in rd(f"{R566}/datasets/pdmx/hard/index.txt")}
shared = main_ids & hard_ids
hard_dups = [ln for ln in hard if pid(ln) in shared]
stats["pdmx_shared_scores"] = len(shared)
stats["pdmx_main_lines"] = len(pdmx)
stats["pdmx_hard_dup_lines_added"] = len(hard_dups)
stats["pdmx_hard_dup_scores_present"] = len({pid(ln) for ln in hard_dups})
pdmx_all = pdmx + hard_dups
srcs = {"lieder": lieder, "grandstaff": gs, "pdmx": pdmx_all}
idx_files = []
for name in ["lieder", "grandstaff", "pdmx"]:
    p = f"{OUT}/src_{name}.txt"
    with open(p, "w") as f:
        f.writelines(absl(ln, R566) for ln in srcs[name])
    idx_files.append(p)
mixed = base.load_and_mix_training_sets(idx_files, [1.0] * 3, -1)
src_of = {}
for name in srcs:
    for ln in srcs[name]:
        src_of[Path(ln.split(",")[0]).name] = name
round_one = load_dataset(mixed, Config(), val_split=0.1)
validation_names = {Path(ln.split(",", 1)[0]).name for ln in round_one["validation_list"]}
cand = rng.sample(round_one["train_list"], int(N_ORIG * 1.05))
orig_train = [ln for ln in cand if "octaveShift" not in tok(ln)][:N_ORIG]
orig_val = rng.sample(round_one["validation_list"], N_VAL)
orig_train = in_vocab(orig_train)
orig_val = in_vocab(orig_val)

# ---- octave
ms_all = [absl(ln, R) for ln in rd(f"{R}/datasets_meter/musescore_octave/index.txt")]
ly_all = [absl(ln, R) for ln in rd(f"{R}/datasets_meter/lilypond/index.txt")]
r3_ly = {ln for ln in rd(f"{R}/datasets/lilypond/round3_train_clean.txt") if "/lilypond/flat/" in ln}
r3_ly_rel = {ln.replace("datasets/lilypond", "datasets_meter/lilypond").replace(".png,", ".png,") for ln in r3_ly}
recut = _filter_valid_samples(in_vocab(sorted(set(ms_all))))
n_recut_all = len(recut)
recut = [ln for ln in recut if Path(ln.split(",", 1)[0]).name not in validation_names]
recut_with = [ln for ln in recut if "octaveShift" in tok(ln)]
recut_without = [ln for ln in recut if "octaveShift" not in tok(ln)]
others = int(len(recut_with) * OTHERS)
recut_sel = recut_with * REPEAT + rng.sample(recut_without, min(others, len(recut_without)))

# lilypond: pool = round 3's lilypond staffs (train) which survived relabeling; holdout by score hash
ly_ok = set(ly_all)
r3_new = set()
for ln in r3_ly:
    png, t = ln.split(",")
    r3_new.add(f"{R}/{png},{R}/{t.replace('datasets/', 'datasets_meter/', 1)}\n")
ly_kept_pool = sorted(ln for ln in ly_ok if ln in r3_new)
lily = _filter_valid_samples(in_vocab(ly_kept_pool))
kept = [ln for ln in lily if not _held(_score_of(ln), HOLD)]
assert len(kept) == len(lily), (len(kept), len(lily))
with_bracket = [ln for ln in kept if "octaveShift_8v" in tok(ln)]
with_8vb = [ln for ln in with_bracket if "octaveShift_8vb" in tok(ln)]
train_oct = recut_sel + kept + with_bracket * (REPEAT - 1) + with_8vb * (VB - 1)
exp_before = sum("octaveShift" in tok(ln) for ln in train_oct)
extra = R3_EXPOSURES - exp_before
pool = sorted(set(with_bracket) | set(recut_with))
topup = []
while len(topup) < extra:
    take = rng.sample(pool, min(extra - len(topup), len(pool)))
    topup += take
train = orig_train + train_oct + topup
rng.shuffle(train)
exp_after = sum("octaveShift" in tok(ln) for ln in train_oct + topup)

# holdouts from the relabeled lilypond clean set (all rounds' staffs)
ly_hold = _filter_valid_samples(in_vocab(sorted(ln for ln in ly_ok if _held(_score_of(ln), HOLD))))
held_real = [ln for ln in ly_hold if not _is_aug(ln)]
held_ins = [ln for ln in ly_hold if _is_aug(ln)]


def w(name, lines):
    with open(f"{OUT}/{name}", "w") as f:
        f.writelines(ln if ln.endswith("\n") else ln + "\n" for ln in lines)


w("run1_train.txt", train)
w("run1_val.txt", orig_val)
w("holdout_real.txt", held_real)
w("holdout_inserted.txt", held_ins)

# ---- control lists
CT = f"{OUT}/control_tokens"
conv_files = 0


def old_form(text):
    out = []
    prev = None
    for line in text.split("\n"):
        parts = []
        for p in line.split(" & "):
            f = p.split(" ")
            if f[0].startswith("timeSignature_"):
                v = f[0][len("timeSignature_"):]
                den = "4" if v == "common" else "2" if v == "cut" else v.split("/")[1]
                f[0] = f"timeSignature/{den}"
                p = " ".join(f)
            parts.append(p)
        out.append(" & ".join(parts))
    return "\n".join(out)


def control_line(ln):
    global conv_files
    png, t = ln.strip().split(",")
    text = tok(ln)
    if "timeSignature_" not in text:
        return ln.strip()
    newp = CT + "/" + t.lstrip("/")
    if not os.path.exists(newp):
        os.makedirs(os.path.dirname(newp), exist_ok=True)
        # drop a time signature line repeating the previous one (the old loader removed those)
        lines_out, prev = [], None
        for line in old_form(text).split("\n"):
            if line.startswith("timeSignature/"):
                if line.split(" ")[0] == prev:
                    continue
                prev = line.split(" ")[0]
            lines_out.append(line)
        open(newp, "w").write("\n".join(lines_out))
        conv_files += 1
    return f"{png},{newp}"


w("control_train.txt", [control_line(ln) for ln in train])
w("control_val.txt", [control_line(ln) for ln in orig_val])

# ---- stats and sanity
def source_of(ln):
    name = Path(ln.split(",", 1)[0]).name
    if "/datasets/lilypond/" in ln:
        return "lilypond"
    if "/datasets/musescore_octave/" in ln:
        return "musescore_octave"
    return src_of.get(name, "?")


cnt = collections.Counter(source_of(ln) for ln in train)
exp_ms = sum("octaveShift" in tok(ln) for ln in train if "/musescore_octave/" in ln)
exp_ly = sum("octaveShift" in tok(ln) for ln in train if "/datasets/lilypond/" in ln)
stats.update(
    train_total=len(train),
    train_by_source=dict(cnt),
    val_total=len(orig_val),
    val_by_source=dict(collections.Counter(source_of(ln) for ln in orig_val)),
    original_train=len(orig_train),
    round_one_train=len(round_one["train_list"]), round_one_val=len(round_one["validation_list"]),
    musescore_recut_index_lines=n_recut_all,
    musescore_recut_with_bracket=len(recut_with),
    musescore_recut_selected=len(recut_sel),
    lilypond_round3_lines_in_clean_relabeled=len(r3_ly),
    lilypond_staffs_kept=len(kept),
    lilypond_with_bracket=len(with_bracket),
    lilypond_with_8vb=len(with_8vb),
    holdout_real=len(held_real), holdout_inserted=len(held_ins),
    round3_bracket_exposures=R3_EXPOSURES,
    bracket_exposures_before_topup=exp_before,
    topup_lines=len(topup),
    bracket_exposures_after_topup=exp_after,
    bracket_exposures_musescore=exp_ms, bracket_exposures_lilypond=exp_ly,
    control_token_files_written=conv_files,
)
# sanity
import analyze  # noqa: E402

bad_missing = bad_eval = 0
for ln in set(train) | set(orig_val) | set(held_real) | set(held_ins):
    png, t = ln.strip().split(",")
    if not (os.path.exists(png) and os.path.exists(t)):
        bad_missing += 1
    relpng = rel(png, R566) if png.startswith(R566) else rel(png, R)
    kind, key, text, hits = analyze.classify(relpng + "," + relpng)
    if hits:
        bad_eval += 1
stats["sanity_missing_files"] = bad_missing
stats["sanity_eval_piece_hits"] = bad_eval
bad_vocab = 0
for ln in set(train) | set(orig_val):
    try:
        check_token_lines(read_tokens(ln.strip().split(",")[1]))
    except Exception:  # noqa: BLE001
        bad_vocab += 1
stats["sanity_out_of_vocabulary"] = bad_vocab
json.dump(stats, open(f"{OUT}/run1_stats.json", "w"), indent=1)
print(json.dumps(stats, indent=1))
