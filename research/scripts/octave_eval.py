# ruff: noqa: T201

"""How well does a checkpoint read octave marks specifically?

The trainer's eval accuracy averages over every token, and octave marks are in
well under 1% of samples, so that number says nothing about them. This runs free
generation (no teacher forcing) on held-out samples that contain an octave token,
plus a set that contains none, and counts the octave tokens in truth vs prediction.

    PYTHONPATH=. python training/transformer/octave_eval.py current_training/checkpoint-9809
"""

import os
import random
import sys
from collections import Counter

import torch
from safetensors.torch import load_file

from homr.simple_logging import eprint
from homr.transformer.configs import Config
from training.architecture.transformer.tromr_arch import TrOMR
from training.transformer import train as base
from training.transformer.data_loader import DataLoader, load_dataset

CLASSES = {
    "8va start": lambda t: t == "octaveShift_8va",
    "8vb start": lambda t: t == "octaveShift_8vb",
    "shift stop": lambda t: t == "octaveShiftStop",
    "octave clef": lambda t: t.startswith("clef_") and t.endswith(("_8va", "_8vb")),
}


def classify(rhythms: list[str]) -> Counter:
    counts: Counter = Counter()
    for token in rhythms:
        for name, test in CLASSES.items():
            if test(token):
                counts[name] += 1
    return counts


def truth_rhythms(token_file: str) -> list[str]:
    with open(token_file) as f:
        return [line.split()[0] for line in f if line.strip()]


def main() -> None:
    checkpoint = sys.argv[1]
    max_positive = int(os.environ.get("EVAL_POS", "400"))
    max_negative = int(os.environ.get("EVAL_NEG", "300"))

    config = Config()
    index_file = os.environ.get("EVAL_INDEX", "")
    if index_file:
        # A prebuilt list, e.g. the held-out LilyPond staffs of build_round2_index.py
        with open(index_file) as f:
            entries = f.readlines()
        validation = DataLoader(entries, config, is_validation=True)
    else:
        indexes = [
            base.lieder_train_index,
            base.grandstaff_train_index,
            base.primus_train_index,
            base.pdmx_train_index,
            base.musetrainer_train_index,
        ]
        train_index = base.load_and_mix_training_sets(indexes, [1.0] * len(indexes), -1)
        datasets = load_dataset(train_index, config, val_split=0.1)
        validation = datasets["validation"]
        entries = datasets["validation_list"]

    positives, negatives = [], []
    for i, entry in enumerate(entries):
        counts = classify(truth_rhythms(entry.strip().split(",")[1]))
        (positives if counts else negatives).append(i)
    eprint(f"validation: {len(entries)} samples, {len(positives)} contain an octave token")
    rng = random.Random(0)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    positives, negatives = positives[:max_positive], negatives[:max_negative]

    model = TrOMR(config)
    weights = (
        checkpoint
        if checkpoint.endswith(".safetensors")
        else os.path.join(checkpoint, "model.safetensors")
    )
    model.load_state_dict(load_file(weights), strict=True)
    model.cuda().eval_mode()

    truth_total: Counter = Counter()
    predicted_total: Counter = Counter()
    matched: Counter = Counter()
    exact = 0
    false_positive_samples = 0
    for n, i in enumerate(positives + negatives):
        truth = classify(truth_rhythms(entries[i].strip().split(",")[1]))
        image = validation[i]["inputs"].unsqueeze(0).cuda()
        with torch.no_grad():
            predicted = classify([s.rhythm for s in model.generate(image)])
        if n < len(positives):
            truth_total.update(truth)
            predicted_total.update(predicted)
            for name in CLASSES:
                matched[name] += min(truth[name], predicted[name])
            exact += truth == predicted
        elif predicted:
            false_positive_samples += 1
        if n % 50 == 0:
            eprint(n, "of", len(positives) + len(negatives))

    print(f"checkpoint {checkpoint}" + (f" on {index_file}" if index_file else ""))
    print(f"samples with octave marks: {len(positives)}; without: {len(negatives)}")
    print(f"{'class':12} {'in truth':>9} {'predicted':>10} {'recall':>8} {'precision':>10}")
    for name in CLASSES:
        t, p, m = truth_total[name], predicted_total[name], matched[name]
        recall = f"{m / t:.1%}" if t else "n/a"
        precision = f"{m / p:.1%}" if p else "n/a"
        print(f"{name:12} {t:9d} {p:10d} {recall:>8} {precision:>10}")
    print(f"samples with every octave token count right: {exact}/{len(positives)}")
    print(
        print(
            "clean samples where an octave token was invented: "
            f"{false_positive_samples}/{len(negatives)}"
        )
    )


if __name__ == "__main__":
    main()
