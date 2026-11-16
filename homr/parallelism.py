import multiprocessing
import os
import sys
import types
from collections.abc import Callable, Iterator
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from typing import Any


def cpu_count() -> int:
    return os.cpu_count() or 1


def default_workers() -> int:
    """
    How many pages are recognized at the same time (HOMR_WORKERS or --workers).
    """
    value = os.environ.get("HOMR_WORKERS")
    if value:
        return max(1, int(value))
    return min(4, cpu_count())


def decoder_threads() -> int:
    """
    How many staffs of a page are decoded at the same time (HOMR_DECODER_THREADS).
    """
    value = os.environ.get("HOMR_DECODER_THREADS")
    if value:
        return max(1, int(value))
    return min(cpu_count(), 6)


def session_options() -> Any:
    """
    Options for the CPU sessions. The workers of a page pool share the cores, a session
    which uses all of them and waits busily for work makes the others slow.
    The number of threads doesn't change the results.
    """
    import onnxruntime as ort  # noqa: PLC0415

    options = ort.SessionOptions()
    value = os.environ.get("HOMR_ORT_THREADS")
    if value:
        options.intra_op_num_threads = max(1, int(value))
        options.add_session_config_entry("session.intra_op.allow_spinning", "0")
    return options


def _initialize_worker(
    threads: int, ort_threads: int, initializer: Callable[..., None] | None, initargs: tuple
) -> None:
    # The cores are shared by the workers
    os.environ.setdefault("HOMR_DECODER_THREADS", str(threads))
    os.environ.setdefault("HOMR_ORT_THREADS", str(ort_threads))
    if initializer is not None:
        initializer(*initargs)


@contextmanager
def _main_module_hidden() -> Iterator[None]:
    """
    Spawned processes import the main module of their parent again. That executes scripts
    which start homr without a "if __name__ == '__main__'" guard once more in every worker.
    The workers only need homr itself, so the main module is hidden while they get started.
    """
    main = sys.modules.get("__main__")
    sys.modules["__main__"] = types.ModuleType("__main__")
    try:
        yield
    finally:
        if main is not None:
            sys.modules["__main__"] = main


@contextmanager
def process_pool(
    workers: int, initializer: Callable[..., None] | None = None, initargs: tuple = ()
) -> Iterator[ProcessPoolExecutor]:
    """
    A pool of worker processes. Every worker loads the models once, when it processes its
    first page.
    """
    share = max(1, cpu_count() // workers)
    threads = min(decoder_threads(), share)
    with _main_module_hidden():
        pool = ProcessPoolExecutor(
            max_workers=workers,
            mp_context=multiprocessing.get_context("spawn"),
            initializer=_initialize_worker,
            initargs=(threads, share, initializer, initargs),
        )
        try:
            yield pool
        finally:
            pool.shutdown(wait=True, cancel_futures=True)


def map_in_order(
    function: Any,
    items: list[Any],
    workers: int,
    initializer: Callable[..., None] | None = None,
    initargs: tuple = (),
) -> Iterator[tuple[Any, Any, BaseException | None]]:
    """
    Calls function(item) for all items on up to workers processes and yields
    (item, result, error) in the order of the items as soon as the result is there.
    With one worker it runs in this process, one item per step of the iteration.
    """
    workers = min(workers, len(items))
    if workers <= 1:
        for item in items:
            try:
                yield item, function(item), None
            except Exception as e:
                yield item, None, e
        return
    with process_pool(workers, initializer, initargs) as pool:
        futures = [pool.submit(function, item) for item in items]
        for item, future in zip(items, futures, strict=True):
            error = future.exception()
            yield item, None if error else future.result(), error
