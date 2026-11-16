import os


def cpu_count() -> int:
    return os.cpu_count() or 1


def decoder_threads() -> int:
    """
    How many staffs of a page are decoded at the same time (HOMR_DECODER_THREADS).
    """
    value = os.environ.get("HOMR_DECODER_THREADS")
    if value:
        return max(1, int(value))
    return min(cpu_count(), 6)
