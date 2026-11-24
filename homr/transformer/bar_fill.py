"""
Exact bar fill of a decoded staff: does every bar hold as much time as the meter in force?

Time is counted as the MusicXML writer counts it (`_advance_to_next_group` in
homr/music_xml_generator.py): the symbols of one chord start together, the next chord starts
when the first of the sounding notes or rests ends, grace notes take no time. Tuplets are part
of the rhythm token (note_12 is an eighth of a triplet), so they need no extra rule here.

A bar is the time between two bar lines. Only closed bars count: the part of the staff after
its last bar line may continue on the next system. Bars without notes or rests and bars with a
multi-measure rest are skipped. A staff (upper or lower) fills a bar when its last note or rest
ends exactly at the length of the meter, or when it holds only rests (the writer writes those
as a bar rest of the meter in force).

The meter of a bar is the last time signature the staff showed before it, else the meter given
by the caller (the one in force from earlier staffs), else the writer's own guess: the median
length of the bars of this staff.
"""

from dataclasses import dataclass, field
from fractions import Fraction

from homr.transformer.vocabulary import (
    EncodedSymbol,
    _group_into_chords,
    is_lower_position,
    parse_time_signature_token,
)


@dataclass
class Bar:
    # End of the last note or rest per staff ("upper", "lower"), from the start of the bar
    ends: dict[str, Fraction] = field(default_factory=dict)
    # Staffs that hold notes in this bar (a staff with only rests is a bar rest)
    with_notes: set[str] = field(default_factory=set)
    # Length of the time signature printed before the bar on this staff, if any
    printed_meter: Fraction | None = None
    multirest: bool = False

    @property
    def length(self) -> Fraction:
        return max(self.ends.values(), default=Fraction(0))

    def fills(self, meter: Fraction) -> bool:
        return all(end == meter for staff, end in self.ends.items() if staff in self.with_notes)


def meter_length(token: str) -> Fraction:
    beats, beat_type, _symbol = parse_time_signature_token(token)
    return Fraction(beats, beat_type)


def _staff(symbol: EncodedSymbol) -> str:
    return "lower" if is_lower_position(symbol.position) else "upper"


def _is_bar_line(chord: list[EncodedSymbol]) -> bool:
    rhythm = chord[0].rhythm
    return "barline" in rhythm or "repeat" in rhythm


def closed_bars(symbols: list[EncodedSymbol]) -> list[Bar]:
    """The bars of a staff which end with a bar line and hold notes or rests."""
    bars: list[Bar] = []
    printed: Fraction | None = None
    bar = Bar()
    clock = Fraction(0)
    sounding: list[Fraction] = []
    for chord in _group_into_chords(symbols):
        if not chord:
            continue
        if _is_bar_line(chord):
            if bar.ends and not bar.multirest:
                bars.append(bar)
            bar = Bar()
            clock = Fraction(0)
            sounding = []
            continue
        for symbol in chord:
            if symbol.rhythm.startswith("timeSignature"):
                try:
                    printed = meter_length(symbol.rhythm)
                except ValueError:
                    continue
        timed = []
        for symbol in chord:
            if not symbol.rhythm.startswith(("note", "rest")):
                continue
            if symbol.rhythm.endswith("m"):
                bar.multirest = True
            duration = symbol.get_duration().fraction
            if duration <= 0:
                continue  # grace notes take no time
            if not bar.ends:
                bar.printed_meter = printed
            staff = _staff(symbol)
            bar.ends[staff] = max(bar.ends.get(staff, Fraction(0)), clock + duration)
            if symbol.rhythm.startswith("note"):
                bar.with_notes.add(staff)
            timed.append(duration)
        if timed:
            sounding.extend(clock + d for d in timed)
            clock = min(end for end in sounding if end > clock)
    return bars


def _median(values: list[Fraction]) -> Fraction:
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def misfit_bars(symbols: list[EncodedSymbol], meter: Fraction | None = None) -> tuple[int, int]:
    """
    (bars which don't fill their meter, closed bars) of a staff. meter: length of the time
    signature in force before the staff, if known.
    """
    bars = closed_bars(symbols)
    if not bars:
        return 0, 0
    fallback = meter if meter is not None else _median([b.length for b in bars])
    misfits = 0
    for bar in bars:
        in_force = bar.printed_meter if bar.printed_meter is not None else fallback
        if not bar.fills(in_force):
            misfits += 1
    return misfits, len(bars)


def last_printed_meter(symbols: list[EncodedSymbol]) -> Fraction | None:
    """Length of the last time signature of a staff, to carry over to the next staff."""
    result = None
    for symbol in symbols:
        if symbol.rhythm.startswith("timeSignature"):
            try:
                result = meter_length(symbol.rhythm)
            except ValueError:
                continue
    return result


@dataclass
class Hypothesis:
    symbols: list[EncodedSymbol]
    log_prob: float


def rerank(hypotheses: list[Hypothesis], meter: Fraction | None = None) -> Hypothesis:
    """
    The hypothesis with the most bars that fill their meter, then the fewest that don't, then
    the one the model finds most likely. Counting filled bars first keeps a hypothesis that
    drops a bar line (and so has fewer bars to get wrong) from winning.
    """

    def key(h: Hypothesis) -> tuple[int, int, float]:
        misfits, bars = misfit_bars(h.symbols, meter)
        return (-(bars - misfits), misfits, -h.log_prob)

    return min(hypotheses, key=key)


def _fill(h: Hypothesis, meter: Fraction | None) -> tuple[int, int]:
    """(bars that fill their meter, -bars that don't): higher is better."""
    misfits, bars = misfit_bars(h.symbols, meter)
    return bars - misfits, -misfits


def likelihood_margin() -> float | None:
    """
    HOMR_BEAM_MARGIN: the lead in log probability (nats) over the greedy reading at which the
    most likely hypothesis replaces it even without better bar fill; "none": never. Default 10
    (odds of about 20,000 to 1): a greedy reading that is that much less likely than the best beam
    has gone astray (a loop, lost bar lines), while the near ties below it are rewrites of chords,
    staffs or octave lines that bar fill cannot judge.
    """
    import os  # noqa: PLC0415

    value = os.environ.get("HOMR_BEAM_MARGIN", "10")
    return None if value in ("", "none") else float(value)


def choose(
    hypotheses: list[Hypothesis],
    meter: Fraction | None = None,
    greedy: Hypothesis | None = None,
) -> Hypothesis:
    """
    The reading a beam search returns. The hypotheses come most likely first; greedy is the
    greedy reading of the same staff, with its log probability. HOMR_BEAM_RERANK:
    - "anchored" (default): the greedy reading, unless the bar-fill rerank finds a hypothesis
      whose bars add up better (more bars that fill their meter, or as many and fewer that
      don't), or the most likely hypothesis leads the greedy reading by more than
      HOMR_BEAM_MARGIN nats. The model's own reading stands wherever neither the bar arithmetic
      nor a decisive lead of the model's own score gives a reason to change it.
    - "fill": the bar-fill rerank among the beam's hypotheses (the first version).
    - "0": the most likely hypothesis.
    """
    import os  # noqa: PLC0415

    mode = os.environ.get("HOMR_BEAM_RERANK", "anchored")
    if mode == "0":
        return hypotheses[0]
    best = rerank(hypotheses, meter)
    if mode in {"fill", "1"} or greedy is None:
        return best
    if _fill(best, meter) > _fill(greedy, meter):
        return best
    margin = likelihood_margin()
    if margin is not None and hypotheses[0].log_prob - greedy.log_prob > margin:
        return hypotheses[0]
    return greedy
