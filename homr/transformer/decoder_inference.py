import os
from typing import Any

import numpy as np
import onnxruntime as ort

from homr.onnx_providers import gpu_providers
from homr.simple_logging import eprint
from homr.transformer.beam_search import beam_width, decode
from homr.transformer.configs import Config
from homr.transformer.octave_crf import apply_octave_crf, octave_crf_enabled
from homr.transformer.vocabulary import (
    NOTE_OCTAVE_CLASSES,
    OCTAVE_SHIFT_STOP,
    OCTAVE_SHIFTS,
    EncodedSymbol,
)
from homr.type_definitions import NDArray

# A staff never holds a long run of one repeating cycle: the longest in the test references is 24
# notes, while a decoder stuck in a loop repeats a pair of notes for hundreds of steps until it
# hits max_seq_len. A cycle of up to LOOP_MAX_PERIOD symbols repeated for LOOP_RUN symbols ends
# the staff, keeping the first LOOP_KEEP symbols of the repeat. HOMR_LOOP_GUARD=0 switches it off.
LOOP_GUARD = os.environ.get("HOMR_LOOP_GUARD", "1") != "0"
LOOP_MAX_PERIOD = 4
LOOP_RUN = 64
LOOP_KEEP = 24


def _loop_key(symbol: EncodedSymbol) -> tuple[str, str, str, str]:
    return (symbol.rhythm, symbol.pitch, symbol.lift, symbol.position)


def _loop_cut(symbols: list[EncodedSymbol], runs: list[int]) -> int | None:
    """The length to cut the symbols to if the last one completes a long repeating run."""
    last = _loop_key(symbols[-1])
    for period in range(1, LOOP_MAX_PERIOD + 1):
        if len(symbols) > period and _loop_key(symbols[-1 - period]) == last:
            runs[period] += 1
            if runs[period] >= LOOP_RUN:
                return len(symbols) - runs[period] - period + LOOP_KEEP
        else:
            runs[period] = 0
    return None


class ScoreDecoder:
    def __init__(
        self,
        transformer: ort.InferenceSession,
        fp16: bool,
        use_gpu: bool,
        config: Config,
        ignore_index: int = -100,
    ):
        super().__init__()
        self.ignore_index = ignore_index
        self.config = config
        self.net = transformer
        self.io_binding = self.net.io_binding()
        self.max_seq_len = config.max_seq_len
        self.eos_token = config.eos_token

        self.inv_rhythm_vocab = {v: k for k, v in config.rhythm_vocab.items()}
        self.inv_pitch_vocab = {v: k for k, v in config.pitch_vocab.items()}
        self.inv_lift_vocab = {v: k for k, v in config.lift_vocab.items()}
        self.inv_articulation_vocab = {v: k for k, v in config.articulation_vocab.items()}
        self.inv_slur_vocab = {v: k for k, v in config.slur_vocab.items()}
        self.inv_position_vocab = {v: k for k, v in config.position_vocab.items()}

        # Newer decoders (since comb6) read the position of the previous symbol as an extra
        # input and some have a per-note octave head. Both are read from the model, so the
        # older released models keep working unchanged.
        self.has_position_feedback = "positions" in {item.name for item in self.net.get_inputs()}
        self.per_note_octaves = "out_octaves" in {item.name for item in self.net.get_outputs()}
        # With the octave head the brackets come from the notes, the legacy octave direction
        # symbols are never generated
        self.legacy_octave_rhythms = (
            [config.rhythm_vocab[token] for token in (*OCTAVE_SHIFTS, OCTAVE_SHIFT_STOP)]
            if self.per_note_octaves
            else []
        )

        self.fp16 = fp16
        self.use_gpu = use_gpu
        self.device = "cuda" if use_gpu else "cpu"
        self.device_id = 0
        self.output_names = [
            "out_rhythms",
            "out_pitchs",
            "out_lifts",
            "out_positions",
            "out_articulations",
            "out_slurs",
            *(["out_octaves"] if self.per_note_octaves else []),
            "attention",
        ]

    def clone(self) -> "ScoreDecoder":
        """
        A decoder with its own IO binding on the same session, so that several
        threads can decode different staffs at the same time.
        """
        return ScoreDecoder(self.net, self.fp16, self.use_gpu, self.config, self.ignore_index)

    def generate(
        self,
        start_tokens: NDArray,
        nonote_tokens: NDArray,
        **kwargs: Any,
    ) -> list[EncodedSymbol]:
        """
        kwargs: context (encoder output), optionally beam_width (default HOMR_BEAM) and
        meter (length of the time signature in force before the staff, for the reranking).
        """
        width = kwargs.get("beam_width") or beam_width()
        if width <= 1:
            symbols = self.generate_greedy(start_tokens, nonote_tokens, **kwargs)
        else:
            symbols = decode(
                self, start_tokens, nonote_tokens, width, kwargs["context"], kwargs.get("meter")
            )
        if self.per_note_octaves and octave_crf_enabled():
            apply_octave_crf(symbols)
        return symbols

    def generate_greedy(
        self,
        start_tokens: NDArray,
        nonote_tokens: NDArray,
        **kwargs: Any,
    ) -> list[EncodedSymbol]:
        num_dims = len(start_tokens.shape)

        if num_dims == 1:
            start_tokens = start_tokens[None, :]

        b, t = start_tokens.shape

        out_rhythm = start_tokens
        out_pitch = nonote_tokens
        out_lift = nonote_tokens
        out_articulations = nonote_tokens
        out_slurs = nonote_tokens
        previous_position = nonote_tokens[:, -1:]
        cache, kv_input_names, kv_output_names = self.init_cache()
        output_names = self.output_names + kv_output_names
        context = kwargs["context"]
        context_reduced = kwargs["context"][:, :1]

        symbols: list[EncodedSymbol] = []
        # Consecutive matches with the symbol p places back, for cycles of up to LOOP_MAX_PERIOD
        runs = [0] * (LOOP_MAX_PERIOD + 1)

        for step in range(self.max_seq_len):
            x_lift = out_lift[:, -1:]  # for all: shape=(1,1)
            x_pitch = out_pitch[:, -1:]
            x_rhythm = out_rhythm[:, -1:]
            x_articulations = out_articulations[:, -1:]
            x_slurs = out_slurs[:, -1:]

            # after the first step we don't pass the full context into the decoder
            # x_transformers uses [:, :0] to split the context
            # which caused a Reshape error when loading the onnx model
            context = context if step == 0 else context_reduced

            # Bind Inputs
            self.io_binding.bind_cpu_input("rhythms", x_rhythm)
            self.io_binding.bind_cpu_input("pitchs", x_pitch)
            self.io_binding.bind_cpu_input("lifts", x_lift)
            self.io_binding.bind_cpu_input("articulations", x_articulations)
            self.io_binding.bind_cpu_input("slurs", x_slurs)
            if self.has_position_feedback:
                self.io_binding.bind_cpu_input("positions", previous_position)
            self.io_binding.bind_cpu_input("context", context)
            self.io_binding.bind_cpu_input("cache_len", np.array([step], dtype=np.int64))
            for name, cache_val in zip(kv_input_names, cache, strict=True):
                self.io_binding.bind_ortvalue_input(name, cache_val)

            # Bind Outputs
            for name in output_names:
                self.io_binding.bind_output(name, self.device, self.device_id)

            # Run inference
            self.net.run_with_iobinding(iobinding=self.io_binding)

            # Get outputs
            outputs = self.io_binding.get_outputs()
            cache = outputs[len(self.output_names) :]

            # Greedy decoding: pick the highest logit directly for each output
            rhythmsp = outputs[0].numpy()
            pitchsp = outputs[1].numpy()
            liftsp = outputs[2].numpy()
            positionsp = outputs[3].numpy()
            articulationsp = outputs[4].numpy()
            slursp = outputs[5].numpy()
            attention = outputs[self.output_names.index("attention")].numpy()

            rhythm_logits = rhythmsp[:, -1, :]
            if self.per_note_octaves:
                rhythm_logits = rhythm_logits.copy()
                rhythm_logits[:, self.legacy_octave_rhythms] = -np.inf
            rhythm_sample = np.array([[rhythm_logits.argmax()]])
            pitch_sample = np.array([[pitchsp[:, -1, :].argmax()]])
            lift_sample = np.array([[liftsp[:, -1, :].argmax()]])
            articulation_sample = np.array([[articulationsp[:, -1, :].argmax()]])
            slur_sample = np.array([[slursp[:, -1, :].argmax()]])
            position_sample = np.array([[positionsp[:, -1, :].argmax()]])

            lift_token = detokenize(lift_sample, self.inv_lift_vocab)
            pitch_token = detokenize(pitch_sample, self.inv_pitch_vocab)
            rhythm_token = detokenize(rhythm_sample, self.inv_rhythm_vocab)
            articulation_token = detokenize(articulation_sample, self.inv_articulation_vocab)
            slur_token = detokenize(slur_sample, self.inv_slur_vocab)
            position_token = detokenize(position_sample, self.inv_position_vocab)

            if rhythm_sample[0][0] == self.eos_token:
                break

            octave_mark = None
            note_octave_logits = None
            if self.per_note_octaves and rhythm_token[0].startswith("note_"):
                octave_logits = outputs[self.output_names.index("out_octaves")].numpy()
                note_octave_logits = octave_logits[0, -1, :].astype(np.float32)
                octave_mark = NOTE_OCTAVE_CLASSES[note_octave_logits.argmax()]
            symbol = EncodedSymbol(
                rhythm=rhythm_token[0],
                pitch=pitch_token[0],
                lift=lift_token[0],
                articulation=articulation_token[0],
                slur=slur_token[0],
                position=position_token[0],
                coordinates=attention,
                octave_mark=octave_mark,
            )
            # the head's logits, for the octave CRF (HOMR_OCTAVE_CRF)
            symbol.octave_logits = note_octave_logits
            symbols.append(symbol)
            cut = _loop_cut(symbols, runs) if LOOP_GUARD else None
            if cut is not None:
                eprint(f"Repeating output stopped after {len(symbols)} symbols, kept {cut}")
                del symbols[cut:]
                break

            out_lift = np.concatenate((out_lift, lift_sample), axis=-1)
            out_pitch = np.concatenate((out_pitch, pitch_sample), axis=-1)
            out_rhythm = np.concatenate((out_rhythm, rhythm_sample), axis=-1)
            out_articulations = np.concatenate((out_articulations, articulation_sample), axis=-1)
            out_slurs = np.concatenate((out_slurs, slur_sample), axis=-1)
            previous_position = position_sample

        return symbols

    def init_cache(self, cache_len: int = 0) -> tuple[list[NDArray], list[str], list[str]]:
        cache = []
        input_names = []
        output_names = []
        heads = self.config.decoder_heads
        head_dim = self.config.decoder_dim // heads
        for i in range(self.config.decoder_depth * 4):
            if self.fp16:  # the cache needs to be fp16 as well
                cache.append(
                    ort.OrtValue.ortvalue_from_numpy(
                        np.zeros((1, heads, cache_len, head_dim), dtype=np.float16),
                        self.device,
                        self.device_id,
                    )
                )
            else:
                cache.append(
                    ort.OrtValue.ortvalue_from_numpy(
                        np.zeros((1, heads, cache_len, head_dim), dtype=np.float32),
                        self.device,
                        self.device_id,
                    )
                )
            input_names.append(f"cache_in{i}")
            output_names.append(f"cache_out{i}")
        return cache, input_names, output_names


def detokenize(tokens: NDArray, vocab: dict[int, str]) -> list[str]:
    toks = [vocab[tok.item()] for tok in tokens]
    toks = [t for t in toks if t not in ("[BOS]", "[EOS]", "[PAD]")]
    return toks


def get_decoder(config: Config) -> ScoreDecoder:
    """
    Returns Tromr's Decoder
    """
    use_gpu = False
    if config.use_gpu_inference:
        try:
            providers, device = gpu_providers()
            onnx_transformer = ort.InferenceSession(
                config.filepaths.decoder_path_fp16, providers=providers
            )
            fp16 = True
            # Sometimes Ort falls automatically back to the CPU EP
            # if so we get an error due to the device selection in init_cache().
            # CoreML binds IO on the CPU (device == "cpu") even when the GPU/ANE runs the
            # compute, so we only flip use_gpu on when CUDA/ROCm device memory is in play.
            active = onnx_transformer.get_providers()
            if device == "cuda":
                for active_provider in active:
                    if active_provider in {"CUDAExecutionProvider", "ROCMExecutionProvider"}:
                        use_gpu = True
                        break
                if not use_gpu:
                    eprint(
                        "Onnxruntime is not using GPU and therefore falling back to CPU. "
                        "This is slow."
                    )

        except Exception as ex:
            eprint(ex)
            eprint("Going on without GPU support")
            onnx_transformer = ort.InferenceSession(config.filepaths.decoder_path_fp16)
            fp16 = True

    else:
        # A decoding step is too small to profit from several threads (one thread is
        # faster than ten), so the staffs are decoded in parallel instead, see Staff2Score.
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        onnx_transformer = ort.InferenceSession(config.filepaths.decoder_path, options)
        fp16 = False

    return ScoreDecoder(onnx_transformer, fp16, use_gpu, config=config)
