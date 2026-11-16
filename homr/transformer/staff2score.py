import os
import queue
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from time import perf_counter

import numpy as np
from PIL import Image

from homr.parallelism import decoder_threads as default_decoder_threads
from homr.simple_logging import eprint
from homr.transformer.configs import Config
from homr.transformer.decoder_inference import ScoreDecoder, get_decoder
from homr.transformer.encoder_inference import Encoder
from homr.transformer.vocabulary import EncodedSymbol
from homr.type_definitions import NDArray


class Staff2Score:
    """
    Inference class for Tromr. Use predict() for prediction or submit() to
    process several staffs at the same time.
    """

    def __init__(self, config: Config, decoder_threads: int | None = None) -> None:
        self.config = config
        self.encoder = Encoder(self.config)
        decoder = get_decoder(self.config)

        if not os.path.exists(self.config.filepaths.rhythmtokenizer):
            raise RuntimeError(
                "Failed to find tokenizer config" + self.config.filepaths.rhythmtokenizer
            )  # noqa: E501

        # The ONNX models have a fixed batch size of one and the decoder quantizes its
        # activations per tensor, so a batch wouldn't give the results of single staffs.
        # Instead every thread decodes one staff, the encoder already uses all cores.
        threads = 1 if decoder.use_gpu else (decoder_threads or default_decoder_threads())
        self._decoders: queue.Queue[ScoreDecoder] = queue.Queue()
        for _ in range(threads):
            self._decoders.put(decoder.clone())
        self._encoder_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=threads, thread_name_prefix="decoder")

    def predict(self, image: NDArray) -> list[EncodedSymbol]:
        """
        Inference an image (NDArray) using Tromr.
        """
        return self.submit(image).result()

    def submit(self, image: NDArray) -> "Future[list[EncodedSymbol]]":
        """
        Starts the inference of an image, results can be retrieved in any order.
        """
        return self._executor.submit(self._predict, image)

    def _predict(self, image: NDArray) -> list[EncodedSymbol]:
        x = _transform(image=image)

        t0 = perf_counter()

        # Create special tokens
        start_token = np.array([[1]], dtype=np.int64)
        nonote_token = np.array([[0]], dtype=np.int64)

        # Generate context with encoder. The encoder and decoder may run in
        # different precisions (e.g. the CoreML encoder is fp16 while the
        # decoder stays on the fp32 CPU model), so cast the context to the
        # dtype the decoder expects before handing it over.
        with self._encoder_lock:
            # copy: the encoder reuses its output buffer for the next staff
            context = self.encoder.generate(x).copy()
        decoder = self._decoders.get()
        try:
            context_dtype = np.float16 if decoder.fp16 else np.float32
            if context.dtype != context_dtype:
                context = context.astype(context_dtype)

            # Make a prediction using decoder
            out = decoder.generate(
                start_token,
                nonote_token,
                seq_len=self.config.max_seq_len,
                eos_token=self.config.eos_token,
                context=context,
            )
        finally:
            self._decoders.put(decoder)

        eprint(f"Inference Time Tromr: {perf_counter()-t0}")

        return out


class ConvertToArray:
    def __init__(self) -> None:
        self.mean = np.array([0.7931]).reshape(1, 1, 1)
        self.std = np.array([0.1738]).reshape(1, 1, 1)

    def normalize(self, array: NDArray) -> NDArray:
        return (array - self.mean) / self.std

    def __call__(self, image: NDArray) -> NDArray:
        arr = np.array(image) / 255
        arr = arr[np.newaxis, np.newaxis, :, :]
        return self.normalize(arr).astype(np.float32)


_transform = ConvertToArray()


def test_transformer_on_image(path_to_img: str) -> None:
    """
    Tests the transformer on an image and prints the results.
    Args:
        path_to_img(str): Path to the image to test
    """

    model = Staff2Score(Config())
    image = Image.open(path_to_img)
    out = model.predict(np.array(image))
    eprint(out)


if __name__ == "__main__":
    import sys

    test_transformer_on_image(sys.argv[1])
