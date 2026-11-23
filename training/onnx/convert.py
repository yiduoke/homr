import os
from typing import Any

import torch
from torch.export import Dim

from homr.segmentation.config import segnet_path_onnx, segnet_path_torch
from homr.simple_logging import eprint
from homr.transformer.configs import Config
from training.architecture.segmentation.model import create_segnet  # type: ignore
from training.architecture.transformer.decoder import (
    ScoreTransformerWrapper,
    get_score_wrapper,
    init_cache,
)
from training.architecture.transformer.encoder import get_encoder


class DecoderWrapper(torch.nn.Module):
    def __init__(self, model: ScoreTransformerWrapper) -> None:
        super().__init__()
        self.model = model

    def forward(
        self,
        rhythms: torch.Tensor,
        pitchs: torch.Tensor,
        lifts: torch.Tensor,
        articulations: torch.Tensor,
        slurs: torch.Tensor,
        positions: torch.Tensor,
        context: torch.Tensor,
        cache_len: torch.Tensor,
        *cache: torch.Tensor,
    ) -> tuple[Any, ...]:
        (
            out_rhythms,
            out_pitchs,
            out_lifts,
            out_positions,
            out_articulations,
            out_slurs,
            _x,
            attention,
            cache_out,
            *extra_logits,
        ) = self.model(
            rhythms=rhythms,
            pitchs=pitchs,
            lifts=lifts,
            articulations=articulations,
            slurs=slurs,
            positions=positions,
            context=context,
            cache_len=cache_len,
            mask=None,
            cache=cache,
            return_center_of_attention=True,
        )
        return (
            out_rhythms,
            out_pitchs,
            out_lifts,
            out_positions,
            out_articulations,
            out_slurs,
            *extra_logits,
            attention,
            cache_out,
        )


def decoder_io_names(config: Config) -> tuple[list[str], list[str]]:
    """
    The names of the inputs and outputs of the decoder graph. The input `positions` (the
    position of the previous symbol) comes after `slurs`; with the per-note octave head
    (HOMR_PER_NOTE_OCTAVES=1) the output `out_octaves` comes after `out_slurs`.
    """
    _cache, kv_input_names, kv_output_names, _dynamic, _length = init_cache(0, torch.device("cpu"))
    inputs = ["rhythms", "pitchs", "lifts", "articulations", "slurs", "positions"]
    outputs = [
        "out_rhythms",
        "out_pitchs",
        "out_lifts",
        "out_positions",
        "out_articulations",
        "out_slurs",
    ]
    if config.per_note_octaves:
        outputs.append("out_octaves")
    return (
        [*inputs, "context", "cache_len", *kv_input_names],
        [*outputs, "attention", *kv_output_names],
    )


def convert_encoder(overwrite: bool) -> str | None:
    """
    Converts the encoder to onnx
    """
    config = Config()

    path_out = config.filepaths.encoder_path

    if os.path.exists(path_out) and not overwrite:
        eprint(
            f"Encoder already exists at {path_out}. Use --overwrite to overwrite the existing file."
        )
        return None

    # Get Encoder
    model = get_encoder(config)

    # Load weights
    model.load_state_dict(
        torch.load(r"encoder_weights.pt", weights_only=True, map_location=torch.device("cpu")),
        strict=True,
    )

    # Set eval mode
    model.eval()

    # Prepare input tensor
    input_tensor = torch.randn(1, 1, config.max_height, config.max_width).float()

    # Export to onnx
    torch.onnx.export(
        model,
        input_tensor,  # type: ignore
        path_out,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
    )

    return path_out


def convert_decoder(overwrite: bool) -> str | None:
    """
    Converts the decoder to onnx.
    """
    config = Config()
    model = get_score_wrapper(config, attn_flash=False)
    model.eval()

    path_out = config.filepaths.decoder_path

    if os.path.exists(path_out) and not overwrite:
        eprint(
            f"Decoder already exists at {path_out}. Use --overwrite to overwrite the existing file."
        )
        return None

    model.load_state_dict(
        torch.load(r"decoder_weights.pt", weights_only=True, map_location=torch.device("cpu")),
        strict=True,
    )

    # Using a wrapper model with a custom forward() function
    wrapped_model = DecoderWrapper(model)
    wrapped_model.eval()

    # Create input data
    # Mask is not used since it caused problems with the tensor size
    kv_cache, _kv_input_names, _kv_output_names, dynamic_axes, cache_length = init_cache(
        0, torch.device("cpu")
    )
    input_names, output_names = decoder_io_names(config)
    rhythms = torch.randint(0, config.num_rhythm_tokens, (1, 1)).long()
    pitchs = torch.randint(0, config.num_pitch_tokens, (1, 1)).long()
    lifts = torch.randint(0, config.num_lift_tokens, (1, 1)).long()
    articulations = torch.randint(0, config.num_articulation_tokens, (1, 1)).long()
    slurs = torch.randint(0, config.num_slur_tokens, (1, 1)).long()
    positions = torch.zeros((1, 1), dtype=torch.int64)
    cache_len = torch.tensor([cache_length]).long()
    cache = kv_cache
    image_tokens = config.max_height // config.patch_size * (config.max_width // config.patch_size)
    context = torch.randn((1, image_tokens, config.encoder_dim)).float()

    dynamic_axes["context"] = {1: "cache_exists"}

    torch.onnx.export(
        wrapped_model,
        (rhythms, pitchs, lifts, articulations, slurs, positions, context, cache_len, *cache),
        path_out,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        opset_version=18,
        do_constant_folding=True,
        export_params=True,
        dynamo=False,
    )
    return path_out


def convert_segnet(overwrite: bool) -> str | None:
    """
    Converts the segnet model to onnx.
    """
    path_out = segnet_path_onnx

    if os.path.exists(path_out) and not overwrite:
        eprint(
            f"Segnet already exists at {path_out}. Use --overwrite to overwrite the existing file."
        )
        return None

    model = create_segnet()
    model.load_state_dict(torch.load(segnet_path_torch, weights_only=True), strict=True)
    model.eval()

    # Input dimension is 1x3x320x320
    sample_inputs = torch.randn(8, 3, 320, 320)

    torch.onnx.export(
        model,
        sample_inputs,  # type: ignore
        path_out,
        opset_version=18,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        # dyamic axes are required for dynamic batch_size
        dynamic_shapes={"image": (Dim("batch_size"), 3, 320, 320)},
        dynamo=True,
        external_data=False,
    )
    return path_out
