"""
Octave CRF (HOMR_OCTAVE_CRF=1, off by default): a learned linear-chain CRF over the per-note
octave head (classes "_", "8va", "8vb") of a decoder with the output `out_octaves`.

The model reads every note's octave mark on its own, so one note inside a printed 8va line can
lose its mark and split one printed bracket into two in the MusicXML. The CRF adds learned
transition weights between the marks of consecutive notes and decodes the most likely mark
sequence exactly (Viterbi); the backbone and the octave head are unchanged.

Chain: the notes of one staff of one decoded staff image (the decoder's "upper*" positions are
staff 1, "lower*" staff 2), in decoded order. The decoder reads left to right, so this is time
order; all voices of the staff are in one chain, as the MusicXML writer draws one bracket per
staff. Rests, clefs and the other symbols are not in the chain.

Score of a mark sequence y_1..y_n with head logits l_i (log-softmax over the three classes):
    sum_i scale * log_softmax(l_i)[y_i] + T[B, y_1] + sum_i T[y_i, y_i+1] + T[y_n, B]
T is a 4x4 matrix over the states (B, "_", "8va", "8vb"), B the boundary (start and end of the
chain); T[B, B] is unused. With 15 transition weights and the emission scale that makes 16
learned numbers, fitted by maximum CRF likelihood on training-set head logits (frozen model,
see run/round6_prep/octave_crf/).
"""

import json
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from homr.transformer.vocabulary import NOTE_OCTAVE_CLASSES, is_lower_position

STATES = ("B", *NOTE_OCTAVE_CLASSES)
DEFAULT_WEIGHTS = Path(__file__).with_name("octave_crf_weights.json")


def octave_crf_enabled() -> bool:
    return os.environ.get("HOMR_OCTAVE_CRF") == "1"


class OctaveCrf:
    def __init__(self, scale: float, transitions: Sequence[Sequence[float]]) -> None:
        t = np.asarray(transitions, dtype=np.float64)
        if t.shape != (len(STATES), len(STATES)):
            raise ValueError(f"The octave CRF needs a {len(STATES)}x{len(STATES)} matrix")
        self.scale = float(scale)
        self.start = t[0, 1:]
        self.end = t[1:, 0]
        self.transitions = t[1:, 1:]

    @staticmethod
    def load(path: str | Path | None = None) -> "OctaveCrf":
        path = path or os.environ.get("HOMR_OCTAVE_CRF_WEIGHTS") or DEFAULT_WEIGHTS
        with open(path) as f:
            data = json.load(f)
        if list(data["states"]) != list(STATES):
            raise ValueError(f"Octave CRF states {data['states']} are not {STATES}")
        return OctaveCrf(data["emission_scale"], data["transitions"])

    def emissions(self, logits: np.ndarray) -> np.ndarray:
        logits = np.asarray(logits, dtype=np.float64)
        shifted = logits - logits.max(axis=-1, keepdims=True)
        log_probs = shifted - np.log(np.exp(shifted).sum(axis=-1, keepdims=True))
        return self.scale * log_probs

    def sequence_score(self, emissions: np.ndarray, labels: Sequence[int]) -> float:
        score = self.start[labels[0]] + self.end[labels[-1]]
        score += sum(emissions[i, y] for i, y in enumerate(labels))
        score += sum(self.transitions[a, b] for a, b in zip(labels, labels[1:], strict=False))
        return float(score)

    def viterbi(self, emissions: np.ndarray) -> list[int]:
        """The exact highest-scoring label sequence (ties: the lower class index)."""
        n = len(emissions)
        if n == 0:
            return []
        best = self.start + emissions[0]
        back = np.zeros((n, emissions.shape[1]), dtype=np.int64)
        for i in range(1, n):
            candidates = best[:, None] + self.transitions  # previous x current
            back[i] = candidates.argmax(axis=0)
            best = candidates.max(axis=0) + emissions[i]
        last = int((best + self.end).argmax())
        path = [last]
        for i in range(n - 1, 0, -1):
            path.append(int(back[i, path[-1]]))
        return path[::-1]


_crf: OctaveCrf | None = None


def _get_crf() -> OctaveCrf:
    global _crf  # noqa: PLW0603
    if _crf is None:
        _crf = OctaveCrf.load()
    return _crf


def apply_octave_crf(symbols: list[Any], crf: OctaveCrf | None = None) -> list[Any]:
    """
    Replaces the octave marks of the notes by the CRF's Viterbi decoding, per staff. Only
    notes that carry the head's logits (attribute octave_logits) take part.
    """
    crf = crf or _get_crf()
    chains: dict[int, list[Any]] = {1: [], 2: []}
    for symbol in symbols:
        if getattr(symbol, "octave_logits", None) is None:
            continue
        chains[2 if is_lower_position(symbol.position) else 1].append(symbol)
    for chain in chains.values():
        if not chain:
            continue
        emissions = crf.emissions(np.stack([s.octave_logits for s in chain]))
        for symbol, label in zip(chain, crf.viterbi(emissions), strict=True):
            symbol.octave_mark = NOTE_OCTAVE_CLASSES[label]
    return symbols
