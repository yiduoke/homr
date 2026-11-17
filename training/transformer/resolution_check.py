"""Shape check and smoke test for the input-resolution experiment (see HOMR_INPUT_SCALE).

One process is one arm: the canvas size is fixed at import time from HOMR_INPUT_SCALE.

    # forward pass on a fixed validation batch, loss in eval mode (deterministic)
    HOMR_INPUT_SCALE=1.5 python -m training.transformer.resolution_check forward
    # a few optimiser steps from the released weights: step time, peak memory, finite loss
    HOMR_INPUT_SCALE=1.5 python -m training.transformer.resolution_check smoke --batch 16 --accum 2

Environment as for finetune_octave.py: FT_CKPT, FT_OLD_VOCAB, FT_VAL_INDEX, FT_TRAIN_INDEX.
Never point the lists at evaluation data.
"""

# ruff: noqa: T201

import argparse
import os
import time

import torch

from homr.transformer.configs import Config
from training.architecture.transformer.tromr_arch import TrOMR
from training.transformer.data_loader import DataLoader, collate_trimmed
from training.transformer.finetune_octave import warm_start


def build(config: Config) -> TrOMR:
    torch.manual_seed(7)
    model = TrOMR(config)
    warm_start(model, os.environ["FT_CKPT"], os.environ["FT_OLD_VOCAB"])
    return model


def read_list(env: str, count: int) -> list[str]:
    with open(os.environ[env]) as f:
        return [next(f) for _ in range(count)]


def forward(count: int, noise: bool) -> None:
    config = Config()
    model = build(config).cuda().eval()
    data = DataLoader(read_list("FT_VAL_INDEX", count), config, is_validation=True)
    batch = collate_trimmed([data[i] for i in range(count)])
    if noise:
        # Same input for the original and the changed code: augmentations are not seeded
        generator = torch.Generator().manual_seed(1)
        batch["inputs"] = torch.randn(batch["inputs"].shape, generator=generator)
    batch = {k: v.cuda() for k, v in batch.items()}
    with torch.no_grad(), torch.autocast("cuda", dtype=torch.bfloat16):
        context = model.encoder(batch["inputs"])
        out = model(**batch)
    print(
        f"scale {getattr(config, 'input_scale', 1.0)}: "
        f"canvas {config.max_height}x{config.max_width}"
    )
    print("input", tuple(batch["inputs"].shape), "-> encoder tokens", tuple(context.shape))
    print(
        "pos_embed_h",
        tuple(model.encoder.pos_embed_h.shape),
        "pos_embed_w",
        tuple(model.encoder.pos_embed_w.shape),
    )
    print(
        "eval loss",
        float(out["loss"]),
        {k: round(float(v), 4) for k, v in out.items() if k.startswith("loss_")},
    )


def longest_samples(count: int, scan: int = 4000) -> list[str]:
    """The samples with the longest token sequences among the first `scan`: worst case memory."""
    from training.transformer.training_vocabulary import read_tokens  # noqa: PLC0415

    entries = read_list("FT_TRAIN_INDEX", scan)
    entries.sort(key=lambda e: len(read_tokens(e.strip().split(",")[1])), reverse=True)
    return entries[:count]


def smoke(
    batch_size: int, accum: int, steps: int, workers: int, synthetic: bool, longest: bool
) -> None:
    config = Config()
    model = build(config).cuda().train()
    if longest:
        train_list = longest_samples(batch_size)
        workers, synthetic = 0, True
    else:
        train_list = read_list("FT_TRAIN_INDEX", batch_size * accum * (steps + 2))
    data = DataLoader(train_list, config, is_validation=False)
    loader = torch.utils.data.DataLoader(
        data,
        batch_size=batch_size,
        num_workers=workers,
        collate_fn=collate_trimmed,
        multiprocessing_context="forkserver" if workers else None,
        shuffle=False,
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.05, fused=True)
    torch.cuda.reset_peak_memory_stats()
    it = iter(loader)
    fixed = None
    times, losses = [], []
    for step in range(steps):
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(accum):
            if synthetic and fixed is not None:
                batch = fixed
            else:
                batch = {k: v.cuda(non_blocking=True) for k, v in next(it).items()}
                fixed = batch
            with torch.autocast("cuda", dtype=torch.bfloat16):
                loss = model(**batch)["loss"]
            (loss / accum).backward()
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.synchronize()
        times.append(time.perf_counter() - t0)
        losses.append(float(loss))
        print(f"step {step} {times[-1]:.2f}s loss {losses[-1]:.4f}", flush=True)
    steady = times[2:] or times
    print(
        f"scale {getattr(config, 'input_scale', 1.0)} batch {batch_size}x{accum} "
        f"synthetic={synthetic}: "
        f"median step {sorted(steady)[len(steady) // 2]:.2f}s, "
        f"peak memory {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB, "
        f"all finite {all(abs(loss) < 1e6 for loss in losses)}"
    )


def loader_speed(batch_size: int, batches: int, workers: int) -> None:
    """Images per second the CPU workers deliver, without the model."""
    config = Config()
    data = DataLoader(read_list("FT_TRAIN_INDEX", batch_size * (batches + 1)), config)
    loader = torch.utils.data.DataLoader(
        data,
        batch_size=batch_size,
        num_workers=workers,
        collate_fn=collate_trimmed,
        multiprocessing_context="forkserver",
        prefetch_factor=1,
    )
    it = iter(loader)
    next(it)
    t0 = time.perf_counter()
    for _ in range(batches - 1):
        next(it)
    rate = batch_size * (batches - 1) / (time.perf_counter() - t0)
    print(
        f"scale {getattr(config, 'input_scale', 1.0)}: {rate:.1f} images/s with {workers} workers"
        f" -> {32 / rate:.2f} s per optimiser step of 32"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("forward")
    f.add_argument("--count", type=int, default=8)
    f.add_argument("--noise", action="store_true", help="seeded noise instead of images")
    s = sub.add_parser("smoke")
    s.add_argument("--batch", type=int, default=16)
    s.add_argument("--accum", type=int, default=2)
    s.add_argument("--steps", type=int, default=6)
    s.add_argument("--workers", type=int, default=12)
    s.add_argument("--synthetic", action="store_true", help="reuse the first batch every step")
    s.add_argument("--longest", action="store_true", help="worst-case batch: longest sequences")
    ld = sub.add_parser("loader")
    ld.add_argument("--batch", type=int, default=16)
    ld.add_argument("--batches", type=int, default=30)
    ld.add_argument("--workers", type=int, default=13)
    a = parser.parse_args()
    if a.cmd == "loader":
        loader_speed(a.batch, a.batches, a.workers)
    elif a.cmd == "forward":
        forward(a.count, a.noise)
    else:
        smoke(a.batch, a.accum, a.steps, a.workers, a.synthetic, a.longest)
