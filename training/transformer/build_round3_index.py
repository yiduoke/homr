"""Sample lists for round three.

Round two showed that the model reads octave brackets in styles it was shown, and that
it is fragile about framing: half a staff space more margin could lose every bracket of
a page. Two things in the data explain that. The MuseScore staff images were cut without
regard to the brackets, so the tokens named brackets the image did not show. And a third
of the LilyPond staffs of scores with lyrics showed another part of the score than their
tokens, because picture and geometry came from two engraving runs.

Round three therefore trains only on staffs whose image is known to contain what the
tokens name:
  - LilyPond staffs, engraved once per page (convert_lilypond.py), of the scores with
    real octave shifts and of scores with inserted ones (augment_octave_shifts.py):
    short brackets, brackets over the lower staff, octave-lower brackets;
  - the MuseScore staffs of scores with octave shifts, cut again so that the bracket is
    inside (recrop_musescore_octave.py);
  - a random part of round one's training samples without octave shifts, so that
    nothing else is forgotten.
Validation is a slice of round one's validation samples. LilyPond staffs are held out by
score for octave_eval.py, separately for real and for inserted brackets.

    PYTHONPATH=. python training/transformer/build_round3_index.py
Environment: R3_ORIGINAL (70000), R3_VAL (4000), R3_BRACKET_REPEAT (2), R3_HOLDOUT (0.1),
R3_RECUT_OTHERS (2, staffs without a bracket per staff with one from the scores cut again),
R3_8VB_REPEAT (1, extra repeats of LilyPond staffs with an octave-lower bracket),
R3_NAME (round3, prefix of the lists written).
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
from training.omr_datasets.recrop_musescore_octave import octave_index
from training.transformer import train as base
from training.transformer.data_loader import _filter_valid_samples, load_dataset
from training.transformer.training_vocabulary import check_token_lines, read_tokens


def _score_of(line: str) -> str:
    """lc5104275-2-8.png, lc5104275v2-1-3.png, lc5104275oct-1-3.png and
    lc5104275oct4-1-3.png -> lc5104275"""
    name = Path(line.split(",", maxsplit=1)[0]).name.rsplit("-", 2)[0]
    return re.sub(r"(oct\d?)?(v\d)?$", "", name)


def _is_augmented(line: str) -> bool:
    return bool(re.search(r"oct\d?(v\d)?-\d+-\d+\.png", line.split(",", maxsplit=1)[0]))


def _held_out(score: str, share: float) -> bool:
    digest = int(hashlib.sha256(("holdout" + score).encode()).hexdigest(), 16)
    return (digest % 10_000) / 10_000 < share


def _tokens(line: str) -> str:
    with open(line.strip().split(",")[1]) as f:
        return f.read()


def _has_bracket(line: str) -> bool:
    return "octaveShift_8v" in _tokens(line)


def _in_vocabulary(lines: list[str]) -> list[str]:
    kept = []
    for line in lines:
        try:
            check_token_lines(read_tokens(line.strip().split(",")[1]))
        except Exception:  # noqa: BLE001, S112 - a token the model has no word for
            continue
        kept.append(line)
    return kept


def main() -> None:
    n_original = int(os.environ.get("R3_ORIGINAL", "70000"))
    n_val = int(os.environ.get("R3_VAL", "4000"))
    repeat = int(os.environ.get("R3_BRACKET_REPEAT", "2"))
    holdout_share = float(os.environ.get("R3_HOLDOUT", "0.1"))
    rng = random.Random(20261113)  # noqa: S311

    indexes = [
        base.lieder_train_index,
        base.grandstaff_train_index,
        base.primus_train_index,
        base.pdmx_train_index,
        base.musetrainer_train_index,
    ]
    mixed = base.load_and_mix_training_sets(indexes, [1.0] * len(indexes), -1)
    round_one = load_dataset(mixed, Config(), val_split=0.1)
    validation_names = {
        Path(line.split(",", maxsplit=1)[0]).name for line in round_one["validation_list"]
    }
    candidates = rng.sample(round_one["train_list"], int(n_original * 1.05))
    original_train = [line for line in candidates if "octaveShift" not in _tokens(line)][
        :n_original
    ]
    original_val = rng.sample(round_one["validation_list"], n_val)

    with open(octave_index) as f:
        recut = _filter_valid_samples(_in_vocabulary(sorted(set(f.readlines()))))
    # The same staffs under another path must not leak from round one's validation
    recut = [
        line for line in recut if Path(line.split(",", maxsplit=1)[0]).name not in validation_names
    ]
    # Only one staff in twenty of these scores has a bracket. The others are in round
    # one's samples already, so a part of them is enough.
    recut_with = [line for line in recut if "octaveShift" in _tokens(line)]
    recut_without = [line for line in recut if "octaveShift" not in _tokens(line)]
    others = int(len(recut_with) * float(os.environ.get("R3_RECUT_OTHERS", "2")))
    recut = recut_with * repeat + rng.sample(recut_without, min(others, len(recut_without)))

    with open(lily_train_index) as f:
        lily = _filter_valid_samples(_in_vocabulary(sorted(set(f.readlines()))))
    held = [line for line in lily if _held_out(_score_of(line), holdout_share)]
    kept = [line for line in lily if not _held_out(_score_of(line), holdout_share)]
    with_bracket = [line for line in kept if _has_bracket(line)]

    with_8vb = [line for line in with_bracket if "octaveShift_8vb" in _tokens(line)]
    vb_repeat = int(os.environ.get("R3_8VB_REPEAT", "1"))
    train = original_train + recut + kept + with_bracket * (repeat - 1) + with_8vb * (vb_repeat - 1)
    rng.shuffle(train)

    def write(name: str, lines: list[str]) -> None:
        with open(os.path.join(lily_root, name), "w") as f:
            f.writelines(lines)

    held_real = [line for line in held if not _is_augmented(line)]
    held_inserted = [line for line in held if _is_augmented(line)]
    name = os.environ.get("R3_NAME", "round3")
    write(f"{name}_train.txt", train)
    write(f"{name}_val.txt", original_val)
    write("holdout_real.txt", held_real)
    write("holdout_inserted.txt", held_inserted)
    summary = {
        "train_total": len(train),
        "from_round_one_without_octave_shifts": len(original_train),
        "musescore_staffs_cut_again": len(recut),
        "musescore_cut_again_with_octave_shift": len(recut_with),
        "lilypond_staffs": len(kept),
        "lilypond_with_bracket": len(with_bracket),
        "lilypond_inserted_brackets": sum(_is_augmented(line) for line in with_bracket),
        "lilypond_with_octave_lower": sum(
            "octaveShift_8vb" in _tokens(line) for line in with_bracket
        ),
        "bracket_repeat": repeat,
        "octave_lower_repeat": vb_repeat,
        "val_from_round_one": len(original_val),
        "holdout_real_staffs": len(held_real),
        "holdout_real_with_bracket": sum(_has_bracket(line) for line in held_real),
        "holdout_inserted_staffs": len(held_inserted),
        "holdout_inserted_with_bracket": sum(_has_bracket(line) for line in held_inserted),
    }
    eprint(json.dumps(summary, indent=1))
    write(f"{name}_summary.json", [json.dumps(summary)])


if __name__ == "__main__":
    main()
