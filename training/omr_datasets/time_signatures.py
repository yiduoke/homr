"""Time signature tokens for the dataset conversions."""

from homr.transformer.vocabulary import (
    NUMERIC_TIME_SIGNATURES,
    TIME_SIGNATURE_COMMON,
    TIME_SIGNATURE_CUT,
    time_signature_token,
)


class UnsupportedTimeSignatureError(ValueError):
    """
    The time signature isn't in the vocabulary. The conversions skip such samples,
    the callers count them.
    """


def numeric_time_signature_token(beats: str | int, beat_type: str | int) -> str:
    """The token of a printed numeric time signature, e.g. timeSignature_3/4."""
    try:
        pair = (int(beats), int(beat_type))
    except ValueError:
        raise UnsupportedTimeSignatureError(
            f"Unsupported time signature {beats}/{beat_type}"
        ) from None
    if pair not in NUMERIC_TIME_SIGNATURES:
        raise UnsupportedTimeSignatureError(f"Unsupported time signature {pair[0]}/{pair[1]}")
    return time_signature_token(*pair)


def symbol_time_signature_token(cut: bool) -> str:
    """C or cut C, whatever the numbers of the source say."""
    return TIME_SIGNATURE_CUT if cut else TIME_SIGNATURE_COMMON
