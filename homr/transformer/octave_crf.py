"""
Octave CRF (on by default since Round 7 variant P; HOMR_OCTAVE_CRF=0 turns it off): a learned linear-chain CRF over the per-note
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
    return os.environ.get("HOMR_OCTAVE_CRF", "1") == "1"


def _island_table(values: Sequence[Any]) -> np.ndarray:
    """(2, k) penalties per bracket mark and run length; a flat [va, vb] is one-note islands only."""
    table = np.asarray(
        [v if isinstance(v, Sequence | np.ndarray) else [v] for v in values], dtype=np.float64
    )
    if table.ndim != 2 or table.shape[0] != len(NOTE_OCTAVE_CLASSES) - 1:  # noqa: PLR2004
        raise ValueError("The island penalties are one list of run lengths per bracket mark")
    return table


class OctaveCrf:
    """
    Linear-chain CRF with the 4x4 first-order matrix plus penalties on short islands only.
    island_gap[X-1][k-1] (X = 8va, 8vb) is subtracted from the score of every run of exactly k
    "none" notes between two runs of mark X (a mark that drops out for k notes inside one
    bracket), island_blip[X-1][k-1] from every run of exactly k notes of mark X between two
    "none" notes (a stray mark). Longer runs and longer gaps cost nothing extra, so a real
    bracket end (X, none, none, ...) is priced by the first-order matrix and the head alone. A
    flat list [a, b] means one-note islands only. Without islands this is the first-order CRF of
    the first version. Decoding is exact Viterbi over (previous run's mark, mark, run length).
    """

    def __init__(
        self,
        scale: float,
        transitions: Sequence[Sequence[float]],
        island_gap: Sequence[Any] = (0.0, 0.0),
        island_blip: Sequence[Any] = (0.0, 0.0),
    ) -> None:
        t = np.asarray(transitions, dtype=np.float64)
        if t.shape != (len(STATES), len(STATES)):
            raise ValueError(f"The octave CRF needs a {len(STATES)}x{len(STATES)} matrix")
        self.scale = float(scale)
        self.start = t[0, 1:]
        self.end = t[1:, 0]
        self.transitions = t[1:, 1:]
        self.gap = _island_table(island_gap)
        self.blip = _island_table(island_blip)
        self.has_islands = bool(self.gap.any() or self.blip.any())
        self._max_len = max(self.gap.shape[1], self.blip.shape[1])
        self._build_state_graph()

    def _build_state_graph(self) -> None:
        """States (p, y, l): the previous run's mark (3 = chain start), this mark, the run length (capped)."""
        k, cap = len(STATES) - 1, self._max_len + 1
        self._k, self._cap = k, cap
        count = (k + 1) * k * cap
        weights = np.full((count, count), -np.inf)
        for p in range(k + 1):
            for y in range(k):
                for run in range(1, cap + 1):
                    s = self.state_index(p, y, run)
                    weights[s, self.state_index(p, y, min(run + 1, cap))] = self.transitions[y, y]
                    for n in range(k):
                        if n != y:
                            weights[s, self.state_index(y, n, 1)] = self.transitions[
                                y, n
                            ] - self._island(p, y, run, n)
        self._weights = weights

    def state_index(self, p: int, y: int, run: int) -> int:
        return (p * self._k + y) * self._cap + run - 1

    def _island(self, p: int, y: int, run: int, n: int) -> float:
        """Penalty of closing a run of `run` notes of mark y, after mark p and before mark n."""
        if y == 0 and p == n and n > 0 and run <= self.gap.shape[1]:
            return float(self.gap[n - 1, run - 1])
        if y > 0 and p == 0 and n == 0 and run <= self.blip.shape[1]:
            return float(self.blip[y - 1, run - 1])
        return 0.0

    @staticmethod
    def load(path: str | Path | None = None) -> "OctaveCrf":
        path = path or os.environ.get("HOMR_OCTAVE_CRF_WEIGHTS") or DEFAULT_WEIGHTS
        with open(path) as f:
            data = json.load(f)
        if list(data["states"]) != list(STATES):
            raise ValueError(f"Octave CRF states {data['states']} are not {STATES}")
        return OctaveCrf(
            data["emission_scale"],
            data["transitions"],
            data.get("island_gap", (0.0, 0.0)),
            data.get("island_blip", (0.0, 0.0)),
        )

    def emissions(self, logits: np.ndarray) -> np.ndarray:
        logits = np.asarray(logits, dtype=np.float64)
        shifted = logits - logits.max(axis=-1, keepdims=True)
        log_probs = shifted - np.log(np.exp(shifted).sum(axis=-1, keepdims=True))
        return self.scale * log_probs

    def sequence_score(self, emissions: np.ndarray, labels: Sequence[int]) -> float:
        score = self.start[labels[0]] + self.end[labels[-1]]
        score += sum(emissions[i, y] for i, y in enumerate(labels))
        score += sum(self.transitions[a, b] for a, b in zip(labels, labels[1:], strict=False))
        # runs of equal marks: (mark, length); the island penalty of a run needs both neighbours
        runs: list[list[int]] = []
        for y in labels:
            if runs and runs[-1][0] == y:
                runs[-1][1] += 1
            else:
                runs.append([y, 1])
        for before, run, after in zip(runs, runs[1:], runs[2:], strict=False):
            score -= self._island(before[0], run[0], run[1], after[0])
        return float(score)

    def viterbi(self, emissions: np.ndarray) -> list[int]:
        """The exact highest-scoring label sequence (ties: the lower class index)."""
        n = len(emissions)
        if n == 0:
            return []
        if self.has_islands and n >= 3:  # noqa: PLR2004
            return self._viterbi_runs(emissions)
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

    def _viterbi_runs(self, emissions: np.ndarray) -> list[int]:
        k, cap = self._k, self._cap
        count = self._weights.shape[0]
        mark_of = np.array([(s // cap) % k for s in range(count)])
        score = np.full(count, -np.inf)
        for y in range(k):
            score[self.state_index(k, y, 1)] = self.start[y] + emissions[0, y]
        back = np.zeros((len(emissions), count), dtype=np.int64)
        for i in range(1, len(emissions)):
            candidates = score[:, None] + self._weights
            back[i] = candidates.argmax(axis=0)
            score = candidates.max(axis=0) + emissions[i][mark_of]
        state = int((score + self.end[mark_of]).argmax())
        path = [int(mark_of[state])]
        for i in range(len(emissions) - 1, 0, -1):
            state = int(back[i, state])
            path.append(int(mark_of[state]))
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
