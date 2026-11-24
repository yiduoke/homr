"""
Beam search over the rhythm head of the ONNX decoder (HOMR_BEAM=<width>), with exact bar-fill
reranking of the final hypotheses (bar_fill.py).

The six heads read one decoder state. Rhythm, pitch, lift, articulation and slur are fed back,
and the position too when the decoder has a `positions` input (models trained with position
feedback), so a step's distribution is the product of the heads. Every beam proposes its `width`
most likely rhythm tokens. The model's own top rhythm keeps the argmax of every other head,
exactly as the greedy decoder does; another rhythm takes the argmax of each other head among the
values the labels pair with its kind. A hypothesis scores the summed log probabilities of the
rhythm and of the five field heads. A per-note octave head (`out_octaves`, HOMR_PER_NOTE_OCTAVES=1)
is read as greedy reads it: the argmax for every note; it is not fed back and not scored. With
that head the legacy octave-line rhythms are masked, as in the greedy decoder.

Width 1 is the greedy decoding, token for token.

The module only uses attributes of the decoder object (`ScoreDecoder` of decoder_inference.py),
so the same file works with every decoder that has them.
"""

import hashlib
import os
import pickle
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from homr.transformer.bar_fill import Hypothesis, choose
from homr.transformer.vocabulary import NOTE_OCTAVE_CLASSES, EncodedSymbol
from homr.type_definitions import NDArray

FIELD_INPUTS = ["pitchs", "lifts", "articulations", "slurs", "positions"]


def beam_width() -> int:
    return max(1, int(os.environ.get("HOMR_BEAM", "1") or "1"))


@dataclass
class _Beam:
    # Last rhythm, pitch, lift, articulation, slur and position token: the next step's input
    inputs: list[int]
    cache: list[Any]
    log_prob: float
    symbols: list[EncodedSymbol]
    runs: list[int]
    # On the greedy path: the top token at every step
    greedy: bool = False


def _log_softmax(logits: NDArray) -> NDArray:
    x = logits.astype(np.float64)
    x = x - x.max()
    return x - np.log(np.exp(x).sum())


def branch_mode() -> str:
    """
    Which alternatives a beam may take (HOMR_BEAM_BRANCH): "timing" (default) only replaces a
    note, rest or chord token by another note, rest or chord token, the tokens whose time the
    bar-fill rerank can judge; "durations" only replaces a note by a note and a rest by a rest;
    "all" takes any rhythm token, the end of the staff included.
    """
    return os.environ.get("HOMR_BEAM_BRANCH", "timing")


def _is_timing(rhythm: str) -> bool:
    return rhythm.startswith(("note", "rest")) or rhythm == "chord"


def _may_branch(top: str, alternative: str, mode: str) -> bool:
    if mode == "all":
        return True
    if mode == "durations":
        return top.split("_", maxsplit=1)[0] == alternative.split("_", maxsplit=1)[
            0
        ] and top.startswith(("note", "rest"))
    return _is_timing(top) and _is_timing(alternative)


def _rhythm_kind(rhythm: str) -> str:
    if rhythm.startswith("note"):
        return "note"
    if rhythm.startswith(("rest", "clef", "dynamic", "octaveShift")):
        return "plain"
    return "nonote"


def field_masks(config: Any) -> dict[str, list[NDArray]]:
    """
    Per kind of rhythm token, an additive mask (0 or -inf) for the pitch, lift, articulation,
    slur and position heads: the values that the labels pair with that kind. Notes have a pitch,
    a lift, an articulation, a slur and a position; rests, clefs, dynamics and octave lines have
    "_" for pitch and lift; everything else (bar lines, key and time signatures, chord) has "."
    in the four fed-back fields.
    """
    vocabs = [
        config.pitch_vocab,
        config.lift_vocab,
        config.articulation_vocab,
        config.slur_vocab,
        config.position_vocab,
    ]

    def mask(vocab: dict[str, int], allowed: Any) -> NDArray:
        m = np.full(len(vocab), -np.inf)
        for token, index in vocab.items():
            if allowed(token):
                m[index] = 0.0
        return m

    def not_in(*tokens: str) -> Any:
        return lambda t: t not in tokens

    def only(*tokens: str) -> Any:
        return lambda t: t in tokens

    anything = not_in()
    return {
        "note": [
            mask(v, a) for v, a in zip(vocabs, [not_in(".", "_")] + [not_in(".")] * 4, strict=True)
        ],
        "plain": [
            mask(v, a)
            for v, a in zip(
                vocabs, [only("_"), only("_"), not_in("."), not_in("."), not_in(".")], strict=True
            )
        ],
        "nonote": [mask(v, a) for v, a in zip(vocabs, [only(".")] * 4 + [anything], strict=True)],
    }


def _run_step(
    decoder: Any, inputs: list[int], cache: list[Any], context: NDArray, step: int
) -> dict[str, Any]:
    """
    One decoder step for one hypothesis. A fresh IO binding each time: a binding writes its
    outputs into the buffers of its previous run, which would overwrite the cache of the other
    hypotheses.
    """
    binding = decoder.net.io_binding()
    names = ["rhythms", *FIELD_INPUTS[: len(inputs) - 1]]
    for name, value in zip(names, inputs, strict=True):
        binding.bind_cpu_input(name, np.array([[value]], dtype=np.int64))
    binding.bind_cpu_input("context", context)
    binding.bind_cpu_input("cache_len", np.array([step], dtype=np.int64))
    layers = range(decoder.config.decoder_depth * 4)
    for i, cache_val in zip(layers, cache, strict=True):
        binding.bind_ortvalue_input(f"cache_in{i}", cache_val)
    output_names = list(decoder.output_names)
    for name in output_names + [f"cache_out{i}" for i in layers]:
        binding.bind_output(name, decoder.device, decoder.device_id)
    decoder.net.run_with_iobinding(iobinding=binding)
    outputs = list(binding.get_outputs())
    result = dict(zip(output_names, outputs[: len(output_names)], strict=True))
    result["cache"] = outputs[len(output_names) :]
    return result


@dataclass
class BeamResult:
    # At most `width` finished hypotheses, most likely first
    hypotheses: list[Hypothesis]
    # The greedy reading of the same staff (the path of the top token at every step)
    greedy: Hypothesis


def generate_beams(
    decoder: Any,
    start_tokens: NDArray,
    nonote_tokens: NDArray,
    width: int,
    context: NDArray,
) -> list[Hypothesis]:
    """At most `width` finished hypotheses, most likely first."""
    return beam_search(decoder, start_tokens, nonote_tokens, width, context).hypotheses


def beam_search(  # noqa: C901, PLR0912, PLR0915
    decoder: Any,
    start_tokens: NDArray,
    nonote_tokens: NDArray,
    width: int,
    context: NDArray,
) -> BeamResult:
    """
    The beam search, which also follows the greedy path to its end: when the greedy path falls
    out of the beam it is carried on as an extra hypothesis that never enters the beam's own
    ranking, so the greedy reading comes at the cost of the steps it spends outside the beam.
    """
    # decoder_inference imports this module
    from homr.transformer.decoder_inference import (  # noqa: PLC0415
        LOOP_GUARD,
        LOOP_MAX_PERIOD,
        _loop_cut,
    )

    if getattr(decoder, "has_tuplets", False):
        raise ValueError("HOMR_BEAM is not adapted to tuplet tokens")
    position_feedback = getattr(decoder, "has_position_feedback", False)
    per_note_octaves = getattr(decoder, "per_note_octaves", False)
    rhythm_mask = np.zeros(len(decoder.inv_rhythm_vocab))
    if per_note_octaves:
        rhythm_mask[decoder.legacy_octave_rhythms] = -np.inf
    cache, _, _ = decoder.init_cache()
    context_reduced = context[:, :1]
    masks = field_masks(decoder.config)
    start = int(start_tokens.reshape(-1)[-1])
    nonote = int(nonote_tokens.reshape(-1)[-1])
    field_vocabs = [
        decoder.inv_pitch_vocab,
        decoder.inv_lift_vocab,
        decoder.inv_articulation_vocab,
        decoder.inv_slur_vocab,
        decoder.inv_position_vocab,
    ]
    fed_back = 5 if position_feedback else 4
    mode = branch_mode()
    first = _Beam([start] + [nonote] * fed_back, cache, 0.0, [], [0] * (LOOP_MAX_PERIOD + 1))
    first.greedy = True
    beams = [first]
    # The greedy path while it is outside the beam
    greedy_beam: _Beam | None = None
    greedy: Hypothesis | None = None
    searching = True
    finished: list[Hypothesis] = []
    left: list[_Beam] = []

    def extend(parent: _Beam, r: int, fields: list[int], out: dict[str, Any], score: float) -> Any:
        """The extended beam, or a finished Hypothesis at the end of the staff or of a loop."""
        if r == decoder.eos_token:
            return Hypothesis(parent.symbols, score)
        rhythm = decoder.inv_rhythm_vocab[r]
        extra = {}
        if per_note_octaves:
            octave_mark = None
            if rhythm.startswith("note_"):
                octave_mark = NOTE_OCTAVE_CLASSES[
                    int(out["out_octaves"].numpy()[0, -1, :].argmax())
                ]
            extra = {"octave_mark": octave_mark}
        symbol = EncodedSymbol(
            rhythm=rhythm,
            pitch=field_vocabs[0][fields[0]],
            lift=field_vocabs[1][fields[1]],
            articulation=field_vocabs[2][fields[2]],
            slur=field_vocabs[3][fields[3]],
            position=field_vocabs[4][fields[4]],
            coordinates=out["attention"].numpy(),
            **extra,
        )
        symbols = [*parent.symbols, symbol]
        runs = list(parent.runs)
        cut = _loop_cut(symbols, runs) if LOOP_GUARD else None
        if cut is not None:
            return Hypothesis(symbols[:cut], score)
        return _Beam([r, *fields[:fed_back]], out["cache"], score, symbols, runs)

    for step in range(decoder.max_seq_len):
        step_context = context if step == 0 else context_reduced
        candidates: list[tuple[float, int, _Beam, int, list[int], dict[str, Any], bool]] = []
        for beam in beams:
            out = _run_step(decoder, beam.inputs, beam.cache, step_context, step)
            rhythm_lp = _log_softmax(out["out_rhythms"].numpy()[0, -1, :] + rhythm_mask)
            # pitch, lift, articulation, slur, position: the order of the fed-back inputs
            fields_lp = [
                _log_softmax(out[name].numpy()[0, -1, :])
                for name in ("out_pitchs", "out_lifts", "out_articulations", "out_slurs")
            ] + [_log_softmax(out["out_positions"].numpy()[0, -1, :])]
            top = int(rhythm_lp.argmax())
            top_rhythm = decoder.inv_rhythm_vocab[top]
            order = [top]
            for i in np.argsort(-rhythm_lp, kind="stable"):
                if len(order) >= width or not np.isfinite(rhythm_lp[i]):
                    break
                if i != top and _may_branch(top_rhythm, decoder.inv_rhythm_vocab[int(i)], mode):
                    order.append(int(i))
            for r in order:
                score = beam.log_prob + float(rhythm_lp[r])
                fields: list[int] = []
                if r == top:
                    fields = [int(lp.argmax()) for lp in fields_lp]
                elif r != decoder.eos_token:
                    kind_masks = masks[_rhythm_kind(decoder.inv_rhythm_vocab[r])]
                    fields = [
                        int((lp + m).argmax()) for lp, m in zip(fields_lp, kind_masks, strict=True)
                    ]
                if r != decoder.eos_token:
                    score += sum(float(lp[f]) for lp, f in zip(fields_lp, fields, strict=True))
                is_greedy = beam.greedy and r == top
                candidates.append((score, len(candidates), beam, r, fields, out, is_greedy))
        candidates.sort(key=lambda c: (-c[0], c[1]))
        new_beams: list[_Beam] = []
        greedy_next = None
        for score, _, parent, r, fields, out, is_greedy in candidates:
            if not (searching and parent is not greedy_beam):
                # the greedy path outside the beam, or the beam search is over
                if is_greedy:
                    greedy_next = (parent, r, fields, out, score)
                continue
            if len(new_beams) >= width:
                if is_greedy:
                    greedy_next = (parent, r, fields, out, score)
                continue
            result = extend(parent, r, fields, out, score)
            if isinstance(result, Hypothesis):
                finished.append(result)
                if is_greedy:
                    greedy = result
                continue
            result.greedy = is_greedy
            new_beams.append(result)
        greedy_beam = None
        if greedy_next is not None:
            result = extend(*greedy_next)
            if isinstance(result, Hypothesis):
                greedy = result
            else:
                result.greedy = True
                greedy_beam = result
        if searching:
            stop = not new_beams
            if not stop and len(finished) >= width:
                kth = sorted((h.log_prob for h in finished), reverse=True)[width - 1]
                stop = all(b.log_prob <= kth for b in new_beams)
            if stop:
                searching = False
                left = new_beams
                for b in new_beams:
                    if b.greedy:
                        greedy_beam = b
                new_beams = []
        beams = new_beams + ([greedy_beam] if greedy_beam is not None else [])
        if not beams:
            break
    if searching:
        left = [b for b in beams if b is not greedy_beam]
    finished.extend(Hypothesis(b.symbols, b.log_prob) for b in left)
    if greedy is None:
        # max_seq_len reached on the greedy path
        path = greedy_beam or next((b for b in left if b.greedy), None)
        greedy = Hypothesis(path.symbols, path.log_prob) if path else finished[0]
    finished.sort(key=lambda h: -h.log_prob)
    return BeamResult(finished[:width], greedy)


def decode(
    decoder: Any,
    start_tokens: NDArray,
    nonote_tokens: NDArray,
    width: int,
    context: NDArray,
    meter: Fraction | None = None,
) -> list[EncodedSymbol]:
    """
    Beam search, then the choice among the hypotheses (bar_fill.choose, HOMR_BEAM_RERANK).
    Research aid: HOMR_BEAM_DUMP=<dir> stores the greedy reading and the hypotheses of every
    staff (keyed by a hash of the encoder output) and reuses them when they are there, so that
    other choices can be scored without decoding again.
    """
    dump_dir = os.environ.get("HOMR_BEAM_DUMP")
    path = None
    if dump_dir:
        key = hashlib.sha1(
            np.ascontiguousarray(context).tobytes(), usedforsecurity=False
        ).hexdigest()[:20]
        path = Path(dump_dir) / f"{key}.pkl"
        if path.exists():
            with open(path, "rb") as f:
                stored = pickle.load(f)  # noqa: S301 (our own files)
            if os.environ.get("HOMR_BEAM_RERANK") == "greedy":
                return stored["greedy"]
            greedy = Hypothesis(stored["greedy"], stored.get("greedy_log_prob", 0.0))
            return choose(stored["hyps"], meter, greedy).symbols
    result = beam_search(decoder, start_tokens, nonote_tokens, width, context)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        with open(tmp, "wb") as f:
            pickle.dump(
                {
                    "greedy": result.greedy.symbols,
                    "greedy_log_prob": result.greedy.log_prob,
                    "hyps": result.hypotheses,
                },
                f,
            )
        tmp.rename(path)
    if os.environ.get("HOMR_BEAM_RERANK") == "greedy":
        return result.greedy.symbols
    return choose(result.hypotheses, meter, result.greedy).symbols
