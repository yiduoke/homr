"""Sample lists for round two: LilyPond-engraved staffs mixed into the round-one data.

Round one taught the octave tokens on MuseScore renders only, and the model learned
MuseScore's bracket label rather than the bracket. Round two continues from those
weights on:
  - every LilyPond staff that isn't held out, those with an octave bracket several times,
  - a random part of round one's *training* samples, so nothing else is forgotten.
Validation is a slice of round one's validation samples, so the per-epoch accuracy stays
comparable with round one and never sees a sample twice.

LilyPond staffs are held out by score, not by staff, so the held-out brackets come from
music the model never saw in this style. They are for octave_eval.py, not for the trainer.

    PYTHONPATH=. python training/transformer/build_round2_index.py
Environment: R2_ORIGINAL (70000), R2_VAL (4000), R2_OCTAVE_REPEAT (4), R2_HOLDOUT (0.1).
"""

import hashlib
import json
import os
import random
import re
from pathlib import Path

from homr.simple_logging import eprint
from homr.transformer.configs import Config
from training.omr_datasets.convert_lilypond import lily_root, lily_train_index
from training.transformer import train as base
from training.transformer.data_loader import _filter_valid_samples, load_dataset


def _score_of(line: str) -> str:
    """lc5104275-2-8.png and lc5104275v2-1-3.png (a second render) -> lc5104275"""
    name = Path(line.split(",", maxsplit=1)[0]).name.rsplit("-", 2)[0]
    return re.sub(r"v\d$", "", name)


def _held_out(score: str, share: float) -> bool:
    digest = int(hashlib.sha256(("holdout" + score).encode()).hexdigest(), 16)
    return (digest % 10_000) / 10_000 < share


def _has_octave_bracket(line: str) -> bool:
    with open(line.strip().split(",")[1]) as f:
        return "octaveShift_8v" in f.read()


def main() -> None:
    n_original = int(os.environ.get("R2_ORIGINAL", "70000"))
    n_val = int(os.environ.get("R2_VAL", "4000"))
    repeat = int(os.environ.get("R2_OCTAVE_REPEAT", "4"))
    holdout_share = float(os.environ.get("R2_HOLDOUT", "0.1"))
    rng = random.Random(20261112)  # noqa: S311

    indexes = [
        base.lieder_train_index,
        base.grandstaff_train_index,
        base.primus_train_index,
        base.pdmx_train_index,
        base.musetrainer_train_index,
    ]
    mixed = base.load_and_mix_training_sets(indexes, [1.0] * len(indexes), -1)
    round_one = load_dataset(mixed, Config(), val_split=0.1)
    original_train = rng.sample(round_one["train_list"], n_original)
    original_val = rng.sample(round_one["validation_list"], n_val)

    with open(lily_train_index) as f:
        lily = _filter_valid_samples(sorted(set(f.readlines())))
    held = [line for line in lily if _held_out(_score_of(line), holdout_share)]
    kept = [line for line in lily if not _held_out(_score_of(line), holdout_share)]
    with_bracket = [line for line in kept if _has_octave_bracket(line)]
    held_with_bracket = [line for line in held if _has_octave_bracket(line)]

    train = original_train + kept + with_bracket * (repeat - 1)
    rng.shuffle(train)

    def write(name: str, lines: list[str]) -> str:
        path = os.path.join(lily_root, name)
        with open(path, "w") as f:
            f.writelines(lines)
        return path

    write("round2_train.txt", train)
    write("round2_val.txt", original_val)
    write("holdout.txt", held)
    summary = {
        "train_total": len(train),
        "from_round_one": len(original_train),
        "lilypond_staffs": len(kept),
        "lilypond_with_bracket": len(with_bracket),
        "bracket_repeat": repeat,
        "val_from_round_one": len(original_val),
        "holdout_staffs": len(held),
        "holdout_with_bracket": len(held_with_bracket),
        "holdout_scores": len({_score_of(line) for line in held}),
    }
    eprint(json.dumps(summary, indent=1))
    write("round2_summary.json", [json.dumps(summary)])


if __name__ == "__main__":
    main()
