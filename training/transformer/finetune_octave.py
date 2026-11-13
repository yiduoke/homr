"""Warm-start the octave-shift vocabulary from the last published PyTorch checkpoint.

The octave branch grows two token lists (rhythm 260 -> 285, articulation 62 -> 89)
and leaves the architecture alone, so every weight of checkpoint 465 has a home in
the new model. Tensors with unchanged shapes are copied as they are; the six that
grew are copied row by row, matching tokens by *name* (articulation indices moved,
rhythm indices did not). Rows for tokens the old model never saw start at the mean
of the old rows, except accentStrong_* which start from their accent_* sibling.

Unlike upstream's `--fine` mode (which unfreezes only the lift head), everything
trains here: the new tokens live in the rhythm head and need the decoder to learn
when to emit them.

Runs on the training box from the repo root:
    PYTHONPATH=. python training/transformer/finetune_octave.py
Environment: FT_EPOCHS (6), FT_LR (5e-5), FT_BATCH (32), FT_MAX_FILES (-1 = all),
FT_CKPT, FT_OLD_VOCAB, FT_RESUME (checkpoint folder name inside current_training),
FT_DATASETS (comma-separated substrings of index paths, for smoke tests), FT_EVAL_ONLY,
FT_INIT (safetensors to continue from), FT_TRAIN_INDEX / FT_VAL_INDEX (prebuilt lists),
FT_NAME (output file prefix).
"""

import json
import os
import sys

import torch
from transformers import EarlyStoppingCallback, TrainingArguments

from homr.simple_logging import eprint
from homr.transformer.configs import Config
from training.architecture.transformer.tromr_arch import TrOMR
from training.run_id import get_run_id
from training.transformer import train as base
from training.transformer.data_loader import DataLoader, label_names, load_dataset
from training.transformer.distribute import Distribute
from training.transformer.metrics import HomrTrainer

GROWN = {
    "decoder.net.rhythm_emb.emb.weight": "rhythm",
    "decoder.net.to_logits_rhythm.weight": "rhythm",
    "decoder.net.to_logits_rhythm.bias": "rhythm",
    "decoder.net.articulation_emb.emb.weight": "articulation",
    "decoder.net.to_logits_articulations.weight": "articulation",
    "decoder.net.to_logits_articulations.bias": "articulation",
}
# Buffers derived from the vocabulary; the freshly built model already has the right one.
REBUILT = {"decoder.note_mask"}


def sibling(token: str, old_index: dict[str, int]) -> int | None:
    """Old token a new one should start from, e.g. accentStrong_staccato <- accent_staccato."""
    if "accentStrong" in token:
        candidate = token.replace("accentStrong", "accent")
        parts = sorted(set(candidate.split("_")))
        return old_index.get("_".join(parts))
    return None


def warm_start(model: TrOMR, checkpoint: str, old_vocab_path: str) -> None:
    old_state = torch.load(checkpoint, map_location="cpu", weights_only=True)
    with open(old_vocab_path) as f:
        old_vocab = json.load(f)
    new_vocab = {
        "rhythm": model.config.vocab.rhythm,
        "articulation": model.config.vocab.articulation,
    }
    state = model.state_dict()

    copied = remapped = fresh = 0
    for key, old in old_state.items():
        if key in REBUILT:
            continue
        if key not in state:
            raise KeyError(f"{key} is in the checkpoint but not in the model")
        if old.shape == state[key].shape:
            state[key] = old
            copied += 1
            continue
        head = GROWN[key]
        old_index, new_index = old_vocab[head], new_vocab[head]
        if old.shape[0] != len(old_index) or state[key].shape[0] != len(new_index):
            raise ValueError(f"{key}: {tuple(old.shape)} / {tuple(state[key].shape)} vs vocab")
        target = old.mean(dim=0, keepdim=True).expand_as(state[key]).clone().to(state[key].dtype)
        for token, new_row in new_index.items():
            old_row = old_index.get(token)
            if old_row is None:
                old_row = sibling(token, old_index)
                fresh += 1
            else:
                remapped += 1
            if old_row is not None:
                target[new_row] = old[old_row]
        state[key] = target
    missing = [k for k in state if k not in old_state]
    if missing:
        raise KeyError(f"model keys absent from checkpoint: {missing[:5]}")
    model.load_state_dict(state, strict=True)
    eprint(f"Warm start: {copied} tensors copied, {remapped} rows remapped, {fresh} new rows")


def main() -> None:
    epochs = int(os.environ.get("FT_EPOCHS", "6"))
    learning_rate = float(os.environ.get("FT_LR", "5e-5"))
    # 32 fits PrIMuS/GrandStaff but runs out of 24 GB on the long Lieder/PDMX systems.
    batch_size = int(os.environ.get("FT_BATCH", "16"))
    accumulation = int(os.environ.get("FT_ACCUM", "2"))
    max_files = int(os.environ.get("FT_MAX_FILES", "-1"))
    checkpoint = os.environ.get(
        "FT_CKPT",
        "/workspace/ckpt/pytorch_model_465-597144cab54c8f6d0f6c9619df5c5312694eadd6.pth",
    )
    old_vocab = os.environ.get("FT_OLD_VOCAB", "/workspace/ckpt/vocab_465.json")
    resume = os.environ.get("FT_RESUME", "")

    distribute = Distribute()
    checkpoint_folder = "current_training"
    resume_from = os.path.join(base.git_root, checkpoint_folder, resume) if resume else None

    if not hasattr(Config, "to_json_string"):
        # transformers' TensorBoard callback wants this; upstream adds it on feature/beams.
        Config.to_json_string = lambda self: json.dumps(self.to_dict(), default=str)  # type: ignore[attr-defined]
    config = Config()

    train_file, val_file = os.environ.get("FT_TRAIN_INDEX"), os.environ.get("FT_VAL_INDEX")
    if train_file and val_file:
        # Prebuilt lists (see build_round2_index.py), already filtered and shuffled
        with open(train_file) as f:
            train_list = f.readlines()
        with open(val_file) as f:
            val_list = f.readlines()
        eprint(f"Training with {len(train_list)} and validating with {len(val_list)} (prebuilt)")
        datasets = {
            "train": DataLoader(train_list, config, is_validation=False),
            "validation": DataLoader(val_list, config, is_validation=True),
        }
    else:
        indexes = [
            base.lieder_train_index,
            base.grandstaff_train_index,
            base.primus_train_index,
            base.pdmx_train_index,
            base.musetrainer_train_index,
        ]
        selected = os.environ.get("FT_DATASETS", "")
        if selected:
            indexes = [i for i in indexes if any(name in i for name in selected.split(","))]
            eprint("Restricting to", indexes)
        elif not os.environ.get("FT_SKIP_CHECK"):
            base._check_datasets_are_present(indexes)
        train_index = base.load_and_mix_training_sets(indexes, [1.0] * len(indexes), max_files)
        datasets = load_dataset(train_index, config, val_split=0.1)

    model = TrOMR(config)
    init = os.environ.get("FT_INIT", "")
    if init:
        # Continue from weights that already have this vocabulary (an earlier round)
        from safetensors.torch import load_file  # noqa: PLC0415

        model.load_state_dict(load_file(init), strict=True)
        eprint("Initialised from", init)
    elif not resume:
        warm_start(model, checkpoint, old_vocab)

    run_id = get_run_id()
    args = TrainingArguments(
        checkpoint_folder,
        # Data loading (augmentation on the CPU) is the bottleneck here, not the GPU,
        # so compiling buys nothing and is one more thing to fail unattended.
        torch_compile=os.environ.get("FT_COMPILE", "0") == "1",
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=3,
        learning_rate=learning_rate,
        optim="adamw_torch_fused",
        gradient_accumulation_steps=accumulation,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size // 2,
        num_train_epochs=epochs,
        weight_decay=0.05,
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        load_best_model_at_end=True,
        metric_for_best_model="eval_accuracy",
        greater_is_better=True,
        report_to=["tensorboard"],
        logging_dir=os.path.join("logs", f"octave{run_id}"),
        logging_steps=100,
        label_names=label_names,
        bf16=True,
        dataloader_pin_memory=True,
        dataloader_num_workers=int(os.environ.get("FT_WORKERS", "11")),
    )

    destination = os.path.join(
        base.git_root,
        "training",
        "architecture",
        "transformer",
        os.environ.get("FT_NAME", "pytorch_model_octave") + f"_{run_id}.pth",
    )
    trainer = HomrTrainer(
        model,
        args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        distribute=distribute,
    )
    try:
        if os.environ.get("FT_EVAL_ONLY"):
            eprint("Warm-start evaluation:", trainer.evaluate())
            return
        trainer.train(resume_from_checkpoint=resume_from)
    except KeyboardInterrupt:
        eprint("Interrupted")
    torch.save(model.state_dict(), destination)
    eprint(f"Saved model to {destination}")
    distribute.destroy()


if __name__ == "__main__":
    # Forked loader workers deadlock on this box before delivering a first batch
    # (threads inherited mid-flight from the parent); fresh interpreters don't.
    torch.multiprocessing.set_start_method(os.environ.get("FT_START_METHOD", "forkserver"))
    sys.exit(main())
