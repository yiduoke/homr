import time
import unittest

from homr.parallelism import map_in_order


def _slow_square(x: int) -> int:
    # Later items finish first
    time.sleep(0.3 if x == 0 else 0)
    if x == 3:  # noqa: PLR2004
        raise ValueError("three")
    return x * x


class TestMapInOrder(unittest.TestCase):
    def test_results_are_in_the_order_of_the_items(self) -> None:
        for workers in (1, 3):
            result = list(map_in_order(_slow_square, [0, 1, 2, 3, 4], workers))
            self.assertEqual([item for item, _, _ in result], [0, 1, 2, 3, 4])
            self.assertEqual([value for _, value, _ in result], [0, 1, 4, None, 16])
            errors = [type(error) for _, _, error in result]
            self.assertEqual(errors, [type(None)] * 3 + [ValueError, type(None)])
