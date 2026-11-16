from homr.transformer.vocabulary import EncodedSymbol, empty


def strip_naturals(
    symbols: list[EncodedSymbol],
) -> list[EncodedSymbol]:
    """
    Evaluation only: ignores printed naturals. Training labels keep them, the lift is the
    printed sign (see homr.accidentals).
    """
    results = []
    for symbol in symbols:
        if symbol.lift == "N":
            results.append(symbol.change_lift(empty))
        else:
            results.append(symbol)

    return results
