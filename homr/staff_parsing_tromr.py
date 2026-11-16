from concurrent.futures import Future

from homr.model import Staff
from homr.transformer.configs import Config
from homr.transformer.staff2score import Staff2Score
from homr.transformer.vocabulary import EncodedSymbol, is_upper_or_has_no_position
from homr.type_definitions import NDArray

inference: Staff2Score | None = None


def parse_staff_tromr(staff: Staff, staff_image: NDArray, config: Config) -> list[EncodedSymbol]:
    return predict_best(staff_image, staff=staff, config=config)


def start_parse_staff_tromr(
    staff: Staff, staff_image: NDArray, config: Config
) -> "Future[list[EncodedSymbol]]":
    """
    Starts the inference without waiting for it, pass the result of the future
    to finish_parse_staff_tromr.
    """
    return _get_inference(config).submit(staff_image)


def finish_parse_staff_tromr(staff: Staff, result: list[EncodedSymbol]) -> list[EncodedSymbol]:
    if staff.is_grandstaff:
        return result
    return [r for r in result if is_upper_or_has_no_position(r.position)]


def _get_inference(config: Config) -> Staff2Score:
    global inference  # noqa: PLW0603
    if inference is None:
        inference = Staff2Score(config)
    return inference


def predict_best(org_image: NDArray, staff: Staff, config: Config) -> list[EncodedSymbol]:
    result = _get_inference(config).predict(org_image)
    return finish_parse_staff_tromr(staff, result)
