import argparse
import glob
import os
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterator
from concurrent.futures import Future
from dataclasses import dataclass
from enum import Enum
from functools import partial

import cv2
import numpy as np
import onnxruntime as ort

from homr import color_adjust, download_utils
from homr.autocrop import autocrop_with_offset
from homr.bar_line_detection import (
    detect_bar_lines,
    prepare_bar_line_image,
)
from homr.bounding_boxes import (
    BoundingEllipse,
    RotatedBoundingBox,
    create_bounding_ellipses,
    create_rotated_bounding_boxes,
)
from homr.combined_switches import tuplet_pass as tuplet_pass_enabled
from homr.debug import Debug
from homr.hires_page import load_hires_page
from homr.model import InputPredictions, MultiStaff, Note, Staff
from homr.music_xml_generator import (
    TimeSignatureMemory,
    XmlGeneratorArguments,
    generate_xml,
)
from homr.noise_filtering import filter_predictions
from homr.note_detection import add_notes_to_staffs, combine_noteheads_with_stems
from homr.onnx_providers import coreml_available, cuda_available, rocm_available
from homr.parallelism import default_workers, map_in_order
from homr.pdf_utils import render_pdf_to_image
from homr.point_mapping import PointMapping, chain, undo_crop, undo_resize
from homr.relieur import process_concat
from homr.resize import resize_image
from homr.segmentation.config import segnet_path_onnx, segnet_path_onnx_fp16
from homr.segmentation.inference_segnet import extract
from homr.simple_logging import eprint
from homr.staff_detection import (
    break_wide_fragments,
    detect_staff,
    estimate_unit_size_from_clefs,
    make_lines_stronger,
)
from homr.staff_parsing import parse_staffs
from homr.staff_position_save_load import load_staff_positions, save_staff_positions
from homr.system_repair import repair_systems
from homr.title_detection import detect_title, download_ocr_weights
from homr.transformer.configs import Config, default_config
from homr.transformer.vocabulary import EncodedSymbol
from homr.type_definitions import NDArray

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


class PredictedSymbols:
    def __init__(
        self,
        noteheads: list[BoundingEllipse],
        staff_fragments: list[RotatedBoundingBox],
        clefs_keys: list[RotatedBoundingBox],
        stems_rest: list[RotatedBoundingBox],
        bar_lines: list[RotatedBoundingBox],
    ) -> None:
        self.noteheads = noteheads
        self.staff_fragments = staff_fragments
        self.clefs_keys = clefs_keys
        self.stems_rest = stems_rest
        self.bar_lines = bar_lines


class InvalidProgramArgumentException(Exception):
    """Raise this exception for issues which the user can address."""


class GpuSupport(Enum):
    No = "no"
    AUTO = "auto"
    FORCE = "force"


def get_predictions(
    original: NDArray,
    preprocessed: NDArray,
    img_path: str,
    enable_cache: bool,
    segnet_use_gpu: bool,
) -> InputPredictions:
    result = extract(
        preprocessed,
        img_path,
        step_size=320,
        use_cache=enable_cache,
        use_gpu_inference=segnet_use_gpu,
    )
    original_image = cv2.resize(original, (result.staff.shape[1], result.staff.shape[0]))
    preprocessed_image = cv2.resize(preprocessed, (result.staff.shape[1], result.staff.shape[0]))
    return InputPredictions(
        original=original_image,
        preprocessed=preprocessed_image,
        notehead=result.notehead.astype(np.uint8),
        symbols=result.symbols.astype(np.uint8),
        staff=result.staff.astype(np.uint8),
        clefs_keys=result.clefs_keys.astype(np.uint8),
        stems_rest=result.stems_rests.astype(np.uint8),
    )


def replace_extension(path: str, new_extension: str) -> str:
    return os.path.splitext(path)[0] + new_extension


def load_and_preprocess_predictions(
    image_path: str, enable_debug: bool, enable_cache: bool, segnet_use_gpu: bool
) -> tuple[InputPredictions, Debug, PointMapping]:
    """
    The returned mapping takes coordinates of the predictions back to the input image.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise InvalidProgramArgumentException(
            "The file format is not supported, please provide a JPG or PNG image file:" + image_path
        )
    image, crop_top_left = autocrop_with_offset(image)
    cropped_shape = image.shape
    image = resize_image(image)
    preprocessed = color_adjust.apply_clahe(image)
    predictions = get_predictions(image, preprocessed, image_path, enable_cache, segnet_use_gpu)
    to_input_image = chain(
        undo_resize(cropped_shape, predictions.preprocessed.shape), undo_crop(*crop_top_left)
    )
    debug = Debug(predictions.original, image_path, enable_debug)
    debug.write_image("color_adjust", preprocessed)

    predictions = filter_predictions(predictions, debug)

    predictions.staff = make_lines_stronger(predictions.staff, (1, 2))
    debug.write_threshold_image("staff", predictions.staff)
    debug.write_threshold_image("symbols", predictions.symbols)
    debug.write_threshold_image("stems_rest", predictions.stems_rest)
    debug.write_threshold_image("notehead", predictions.notehead)
    debug.write_threshold_image("clefs_keys", predictions.clefs_keys)
    return predictions, debug, to_input_image


def predict_symbols(debug: Debug, predictions: InputPredictions) -> PredictedSymbols:
    eprint("Creating bounds for noteheads")
    noteheads = create_bounding_ellipses(predictions.notehead, min_size=(4, 4))
    eprint("Creating bounds for staff_fragments")
    staff_fragments = create_rotated_bounding_boxes(
        predictions.staff, skip_merging=True, min_size=(5, 1), max_size=(10000, 100)
    )

    eprint("Creating bounds for clefs_keys")
    clefs_keys = create_rotated_bounding_boxes(
        predictions.clefs_keys, min_size=(20, 40), max_size=(1000, 1000)
    )
    eprint("Creating bounds for stems_rest")
    stems_rest = create_rotated_bounding_boxes(predictions.stems_rest)
    eprint("Creating bounds for bar_lines")
    bar_line_img = prepare_bar_line_image(predictions.stems_rest)
    debug.write_threshold_image("bar_line_img", bar_line_img)
    bar_lines = create_rotated_bounding_boxes(bar_line_img, skip_merging=True, min_size=(1, 5))

    return PredictedSymbols(noteheads, staff_fragments, clefs_keys, stems_rest, bar_lines)


@dataclass
class ProcessingConfig:
    enable_debug: bool
    enable_cache: bool
    write_staff_positions: bool
    read_staff_positions: bool
    selected_staff: int
    # The transformer (encoder/decoder) only benefits from CUDA/ROCm: its fp16 "GPU"
    # models are slower than the fp32 ones when they end up on the CPU EP, and
    # the CoreML EP cannot run the decoder. Segnet additionally supports CoreML.
    transformer_use_gpu: bool
    segnet_use_gpu: bool
    # Opt-in (--coreml-encoder): run the encoder on the Apple GPU via CoreML.
    # Only helps across many images (slow one-time MLProgram compile).
    coreml_encoder: bool
    title_detection: bool


@dataclass
class RecognizedPage:
    """What the recognition of a page found, the XML is generated from it afterwards."""

    xml_file: str
    result_staffs: list[list[EncodedSymbol]]
    title: str


def recognize_page(image_path: str, config: ProcessingConfig) -> RecognizedPage:
    """
    Segmentation, staff detection and transformer for a page. It doesn't depend on any other
    page, so pages can be recognized in parallel. Use write_page for the result.
    """
    eprint("Processing " + image_path)
    xml_file = replace_extension(image_path, ".musicxml")
    debug_cleanup: Debug | None = None
    try:
        if config.read_staff_positions:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("Failed to read " + image_path)
            original_shape = image.shape
            image = resize_image(image)
            to_input_image = undo_resize(original_shape, image.shape)
            debug = Debug(image, image_path, config.enable_debug)
            staff_position_files = replace_extension(image_path, ".txt")
            multi_staffs = load_staff_positions(
                debug, image, staff_position_files, config.selected_staff
            )
            title = ""
            # parse_staffs() expects a grayscale image (cv2.findContours requires it),
            # matching what the normal detect_staffs_in_image() path hands it
            # (predictions.preprocessed). Apply the same CLAHE preprocessing here so the
            # two code paths feed the symbol-recognition encoder consistent input.
            image = color_adjust.apply_clahe(image)
        else:
            multi_staffs, image, debug, title_future, _, to_input_image = detect_staffs_in_image(
                image_path, config
            )
        debug_cleanup = debug
        multi_staffs = repair_systems(debug, multi_staffs)

        transformer_config = Config()
        transformer_config.use_gpu_inference = config.transformer_use_gpu
        transformer_config.use_coreml_encoder = config.coreml_encoder

        result_staffs = parse_staffs(
            debug,
            multi_staffs,
            image,
            selected_staff=config.selected_staff,
            config=transformer_config,
            page_to_input_image=to_input_image,
            hires=load_hires_page(image_path, image.shape, to_input_image),
        )

        if not config.read_staff_positions:
            title = title_future.result(60)
        eprint("Found title:", title)

        teaser_file = replace_extension(image_path, "_teaser.png")
        if config.write_staff_positions:
            staff_position_files = replace_extension(image_path, ".txt")
            save_staff_positions(multi_staffs, image.shape, staff_position_files)
        debug.write_teaser(teaser_file, multi_staffs)
        debug.clean_debug_files_from_previous_runs()
    except:
        if os.path.exists(xml_file):
            os.remove(xml_file)
        raise
    finally:
        if debug_cleanup is not None:
            debug_cleanup.clean_debug_files_from_previous_runs()
    return RecognizedPage(xml_file, result_staffs, title)


def write_page(
    page: RecognizedPage,
    xml_generator_args: XmlGeneratorArguments,
    time_signatures: TimeSignatureMemory | None = None,
) -> str:
    """
    time_signatures: Pass the same object for all pages of a score, so that a page
    without a time signature continues with the one of the previous page. The pages have to
    be written in the order of the score.
    """
    try:
        eprint("Writing XML", page.result_staffs)
        xml = generate_xml(xml_generator_args, page.result_staffs, page.title, time_signatures)
        ET.ElementTree(xml).write(page.xml_file, encoding="unicode", xml_declaration=True)
        eprint("Finished parsing " + str(len(page.result_staffs)) + " staves")
        eprint("Result was written to", page.xml_file)
    except:
        if os.path.exists(page.xml_file):
            os.remove(page.xml_file)
        raise
    return page.xml_file


def process_image(
    image_path: str,
    config: ProcessingConfig,
    xml_generator_args: XmlGeneratorArguments,
    time_signatures: TimeSignatureMemory | None = None,
) -> str:
    """
    time_signatures: Pass the same object for all pages of a score, so that a page
    without a time signature continues with the one of the previous page.
    """
    page = recognize_page(image_path, config)
    return write_page(page, xml_generator_args, time_signatures)


@dataclass
class SingleStaffs:
    """The staffs of a page before they are grouped into systems."""

    predictions: InputPredictions
    debug: Debug
    to_input_image: PointMapping
    staffs: list[Staff]
    notes: list[Note]


def detect_single_staffs(image_path: str, config: ProcessingConfig) -> SingleStaffs:
    predictions, debug, to_input_image = load_and_preprocess_predictions(
        image_path, config.enable_debug, config.enable_cache, config.segnet_use_gpu
    )
    symbols = predict_symbols(debug, predictions)

    symbols.staff_fragments = break_wide_fragments(symbols.staff_fragments)
    debug.write_bounding_boxes("staff_fragments", symbols.staff_fragments)
    eprint("Found " + str(len(symbols.staff_fragments)) + " staff line fragments")

    noteheads_with_stems = combine_noteheads_with_stems(symbols.noteheads, symbols.stems_rest)
    debug.write_bounding_boxes_alternating_colors("notehead_with_stems", noteheads_with_stems)
    eprint("Found " + str(len(noteheads_with_stems)) + " noteheads")
    if len(noteheads_with_stems) > 0:
        average_note_head_height = float(
            np.median([notehead.notehead.size[1] for notehead in noteheads_with_stems])
        )
    else:
        unit_size = estimate_unit_size_from_clefs(symbols.staff_fragments, symbols.clefs_keys)
        if unit_size is None:
            raise Exception("No noteheads or clefs found")
        average_note_head_height = unit_size
    eprint("Average note head height: " + str(average_note_head_height))

    all_noteheads = [notehead.notehead for notehead in noteheads_with_stems]
    all_stems = [note.stem for note in noteheads_with_stems if note.stem is not None]
    bar_lines_or_rests = [
        line
        for line in symbols.bar_lines
        if not line.is_overlapping_with_any(all_noteheads)
        and not line.is_overlapping_with_any(all_stems)
    ]
    bar_line_boxes = detect_bar_lines(bar_lines_or_rests, average_note_head_height)
    debug.write_bounding_boxes_alternating_colors("bar_lines", bar_line_boxes)
    eprint("Found " + str(len(bar_line_boxes)) + " bar lines")

    debug.write_bounding_boxes(
        "anchor_input", symbols.staff_fragments + bar_line_boxes + symbols.clefs_keys
    )
    staffs = detect_staff(
        debug,
        predictions.staff,
        symbols.staff_fragments,
        symbols.clefs_keys,
        bar_line_boxes,
        predictions.symbols,
    )
    if len(staffs) == 0:
        raise Exception("No staffs found")

    debug.write_bounding_boxes_alternating_colors("staffs", staffs)

    notes = add_notes_to_staffs(
        staffs, noteheads_with_stems, predictions.symbols, predictions.notehead
    )
    return SingleStaffs(predictions, debug, to_input_image, staffs, notes)


def group_staffs(predictions: InputPredictions, staffs: list[Staff]) -> list[MultiStaff]:
    from homr import staff_relations  # noqa: PLC0415

    staffs = staff_relations.join_pieces_with_model(predictions, staffs)
    pairs, crops = staff_relations.page_inputs(predictions, staffs)
    probabilities = staff_relations.get_model().predict(crops)
    for (i, j), p in zip(pairs, probabilities, strict=True):
        scores = ", ".join(
            f"{name} {p_class:.2f}"
            for name, p_class in zip(staff_relations.CLASSES, p, strict=True)
        )
        best = staff_relations.CLASSES[int(p.argmax())]
        eprint(f"Staffs {i} and {j} (from the top): {best} ({scores})")
    return staff_relations.group_staffs(staffs, pairs, probabilities)


def detect_staffs_in_image(
    image_path: str, config: ProcessingConfig
) -> tuple[list[MultiStaff], NDArray, Debug, Future[str], int, PointMapping]:
    single = detect_single_staffs(image_path, config)
    debug, staffs = single.debug, single.staffs
    if config.title_detection:
        title_future = detect_title(debug, staffs[0])
    else:
        title_future = Future()
        title_future.set_result("")

    multi_staffs = group_staffs(single.predictions, staffs)
    eprint(
        "Found",
        len(multi_staffs),
        "connected staffs (after merging grand staffs, multiple voices): ",
        [len(staff.staffs) for staff in multi_staffs],
    )

    debug.write_all_bounding_boxes_alternating_colors("notes", multi_staffs, single.notes)

    return (
        multi_staffs,
        single.predictions.preprocessed,
        debug,
        title_future,
        len(staffs),
        single.to_input_image,
    )


def get_all_image_files_in_folder(folder: str) -> list[str]:
    image_files = []
    for ext in ["png", "jpg", "jpeg", "pdf", "PNG", "JPG", "JPEG", "PDF"]:
        image_files.extend(glob.glob(os.path.join(folder, "**", f"*.{ext}"), recursive=True))
    # On case-insensitive file systems the upper and lower case patterns match the same files
    image_files = list(dict.fromkeys(image_files))
    without_teasers = [
        img
        for img in image_files
        if "_teaser" not in img
        and "_debug" not in img
        and "_staff" not in img
        and "_tesseract" not in img
    ]
    return sorted(without_teasers)


def download_weights(segnet_use_gpu: bool, transformer_use_gpu: bool, coreml_encoder: bool) -> None:
    base_url = "https://github.com/liebharc/homr/releases/download/onnx_checkpoints/"
    # The fork's own fine-tuned models are on the fork's releases, upstream models (like 566)
    # on upstream's.
    fork_releases = {
        "pytorch_model_octave": "octave_checkpoints",
        "pytorch_model_meteracc": "meteracc_checkpoints",
    }
    transformer_url = base_url
    for prefix, release in fork_releases.items():
        if prefix in default_config.filepaths.decoder_path:
            transformer_url = f"https://github.com/yiduoke/homr/releases/download/{release}/"
    models = [segnet_path_onnx_fp16 if segnet_use_gpu else segnet_path_onnx]
    if transformer_use_gpu:
        # CUDA runs the whole transformer on the fp16 models.
        models.append(default_config.filepaths.encoder_path_fp16)
        models.append(default_config.filepaths.decoder_path_fp16)
    else:
        # On the CPU EP the fp32 models are faster, and the CoreML EP cannot run
        # the decoder, so the decoder always uses fp32. The CoreML encoder, when
        # enabled, uses the fp16 encoder instead of the fp32 one.
        if coreml_encoder:
            models.append(default_config.filepaths.encoder_path_fp16)
        else:
            models.append(default_config.filepaths.encoder_path)
        models.append(default_config.filepaths.decoder_path)
    from homr import staff_relations  # noqa: PLC0415

    models.append(staff_relations.model_path)
    models.append(staff_relations.horizontal_model_path)
    missing_models = [model for model in models if not os.path.exists(model)]

    if len(missing_models) == 0:
        return

    eprint("Downloading", len(missing_models), "models - this is only required once")
    for model in missing_models:
        if not os.path.exists(model):
            base_name = os.path.basename(model).split(".")[0]
            eprint(f"Downloading {base_name}")
            try:
                zip_name = base_name + ".zip"
                is_transformer = base_name.startswith(("encoder_", "decoder_"))
                download_url = (transformer_url if is_transformer else base_url) + zip_name
                os.makedirs(os.path.dirname(model), exist_ok=True)
                downloaded_zip = os.path.join(os.path.dirname(model), zip_name)
                download_utils.download_file(download_url, downloaded_zip)

                destination_dir = os.path.dirname(model)
                download_utils.unzip_file(downloaded_zip, destination_dir)
            finally:
                if os.path.exists(downloaded_zip):
                    os.remove(downloaded_zip)


def _initialize_worker(title_detection: bool) -> None:
    if title_detection:
        download_ocr_weights()


def recognize_pages(
    images: list[str], config: ProcessingConfig, workers: int | None = None
) -> Iterator[tuple[str, RecognizedPage | None, BaseException | None]]:
    """
    Recognizes the pages on several processes, yields (image, page, error) in the order of
    the images. Everything which depends on the order of the pages has to be done by the
    caller with the yielded pages.
    """
    if workers is None:
        workers = default_workers()
    yield from map_in_order(
        partial(recognize_page, config=config),
        images,
        workers,
        _initialize_worker,
        (config.title_detection,),
    )


def continue_tuplets(xml_paths: list[str]) -> None:
    """
    Runs the page level tuplet pass (research_scripts/tuplet_pass.py) on the page files of a
    score in the order of the pages, so that a ratio read on one page continues on the next.
    A file where nothing is converted is not written. HOMR_TUPLET_PASS=0 or
    HOMR_COMBINED_OFF=C turns it off.
    """
    if not tuplet_pass_enabled():
        return
    try:
        from research_scripts import tuplet_pass  # noqa: PLC0415
    except ImportError:
        eprint("The tuplet pass is not part of this installation, it is skipped")
        return
    state: dict = {}
    first_bar = 0
    for path in xml_paths:
        # Comments carry the image positions of the symbols
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))  # noqa: S314
        tree = ET.parse(path, parser=parser)  # noqa: S314
        root = tree.getroot()
        decisions, _ = tuplet_pass.process(root, None, state, first_bar)
        if any(decision.status == "converted" for decision in decisions):
            tree.write(path, encoding="utf-8", xml_declaration=True)
        first_bar += max((len(part.findall("measure")) for part in root.findall("part")), default=0)


def run_homr(
    images: list,
    config: ProcessingConfig,
    xml_generator_args: XmlGeneratorArguments,
    workers: int | None = None,
) -> None:
    """
    Runs homr on all images in a list and merges them into musicxml using relieur
    """
    eprint("Merging", len(images), "files:", images)
    xml_paths = []
    time_signatures = TimeSignatureMemory()
    for image_file, page, error in recognize_pages(images, config, workers):
        eprint("=========================================")
        try:
            if error is not None or page is None:
                raise error or RuntimeError("No result for " + image_file)
            # The time signature of a page continues on the next one, so the pages
            # are written one after the other in their order
            xml_paths.append(write_page(page, xml_generator_args, time_signatures))
            eprint("Finished", image_file)
        except Exception as e:
            eprint(f"An error occurred while processing {image_file}: {e}")
            raise

    if len(xml_paths) == len(images):
        continue_tuplets(xml_paths)

    if len(xml_paths) == len(images) and len(xml_paths) > 1:
        m, _, _ = process_concat(xml_paths)
        for path in xml_paths:
            if os.path.exists(path):
                os.remove(path)
        filename = os.path.splitext(images[0])[0]
        output_path = f"{filename}.musicxml"
        ET.ElementTree(m).write(output_path, encoding="UTF-8", xml_declaration=True)

        eprint(f"Saved the generated musicxml at {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="homer", description="An optical music recognition (OMR) system"
    )
    parser.add_argument("image", type=str, nargs="*", help="Path to the image to process")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Downloads the models if they are missing and then exits. "
        + "You don't have to call init before processing images, "
        + "it's only useful if you want to prepare for example a Docker image.",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument(
        "--cache", action="store_true", help="Read an existing cache file or create a new one"
    )
    parser.add_argument(
        "--output-large-page",
        action="store_true",
        help="Adds instructions to the musicxml so that it gets rendered on larger pages",
    )
    parser.add_argument(
        "--output-metronome", type=int, help="Adds a metronome to the musicxml with the given bpm"
    )
    parser.add_argument(
        "--output-tempo", type=int, help="Adds a tempo to the musicxml with the given bpm"
    )
    parser.add_argument(
        "--write-staff-positions",
        action="store_true",
        help="Writes the position of all detected staffs to a txt file.",
    )
    parser.add_argument(
        "--read-staff-positions",
        action="store_true",
        help="Reads the position of all staffs from a txt file instead"
        + " of running the built-in staff detection.",
    )
    parser.add_argument(
        "--gpu",
        type=GpuSupport,
        choices=list(GpuSupport),
        default=GpuSupport.AUTO,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--coreml-encoder",
        action="store_true",
        help="On Apple Silicon, run the transformer encoder on the GPU via "
        + "CoreML. Compiling the model takes 26-60 s at startup, so this only "
        + "pays off when processing many images. Has no effect with CUDA.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="How many pages are recognized at the same time on several processes, "
        + "every one loads the models. Default: HOMR_WORKERS or the lower of 4 and the "
        + "number of cores.",
    )
    parser.add_argument(
        "--no-title", action="store_true", help="Don't detect title for faster inference"
    )

    args = parser.parse_args()

    force_gpu = args.gpu == GpuSupport.FORCE
    auto_gpu = args.gpu == GpuSupport.AUTO

    # CUDA/ROCm speeds up the whole pipeline. CoreML only helps segnet: the fp16
    # models the GPU path uses are slower on the CPU EP than the fp32 ones,
    # and the CoreML EP cannot run the decoder (see Segnet for details).
    transformer_use_gpu = force_gpu or (auto_gpu and (cuda_available() or rocm_available()))
    segnet_use_gpu = force_gpu or (
        auto_gpu and (cuda_available() or rocm_available() or coreml_available())
    )
    # The CoreML encoder is a separate opt-in and only applies when the
    # transformer isn't already on CUDA/ROCm.
    coreml_encoder = args.coreml_encoder and not transformer_use_gpu and coreml_available()

    download_weights(segnet_use_gpu, transformer_use_gpu, coreml_encoder)

    if not args.no_title:
        download_ocr_weights()

    if args.init:
        eprint("Init finished")
        return

    config = ProcessingConfig(
        args.debug,
        args.cache,
        args.write_staff_positions,
        args.read_staff_positions,
        -1,
        transformer_use_gpu,
        segnet_use_gpu,
        coreml_encoder,
        not args.no_title,
    )

    xml_generator_args = XmlGeneratorArguments(
        args.output_large_page, args.output_metronome, args.output_tempo
    )
    if args.debug:
        eprint(f"Using Log Level {2} for OnnxRuntime")
        ort.set_default_logger_severity(2)
    else:
        ort.set_default_logger_severity(3)

    if not args.image:
        eprint("No image provided")
        parser.print_help()
        sys.exit(1)

    images_to_combine = []
    for image in args.image:
        if os.path.isfile(image):
            # Multiple files are getting merged
            if image.lower().endswith(".pdf"):
                images_to_combine += render_pdf_to_image(image)
            else:
                images_to_combine.append(image)

        elif os.path.isdir(image):
            # Directories are never merged
            image_files = get_all_image_files_in_folder(image)
            eprint("Processing", len(image_files), "files:", image_files)
            error_files = []
            # The images are independent of each other, PDFs are processed afterwards
            plain_images = [f for f in image_files if not f.lower().endswith(".pdf")]
            pdf_files = [f for f in image_files if f.lower().endswith(".pdf")]
            for image_file, page, error in recognize_pages(plain_images, config, args.workers):
                eprint("=========================================")
                try:
                    if error is not None or page is None:
                        raise error or RuntimeError("No result for " + image_file)
                    write_page(page, xml_generator_args)
                    eprint("Finished", image_file)
                except Exception as e:
                    eprint(f"An error occurred while processing {image_file}: {e}")
                    error_files.append(image_file)
            for image_file in pdf_files:
                eprint("=========================================")
                try:
                    rendered_images = render_pdf_to_image(image_file)
                    run_homr(rendered_images, config, xml_generator_args, args.workers)
                    eprint("Finished", image_file)
                except Exception as e:
                    eprint(f"An error occurred while processing {image_file}: {e}")
                    error_files.append(image_file)
            if len(error_files) > 0:
                eprint("Errors occurred while processing the following files:", error_files)

        else:
            eprint(f"{image} is not a valid file or directory")
            sys.exit(2)

    # Check if we have any images
    if images_to_combine:
        # After collectiong all images we run homr on them
        try:
            run_homr(images_to_combine, config, xml_generator_args, args.workers)
        except InvalidProgramArgumentException as e:
            eprint(str(e))
            sys.exit(2)
        except Exception:
            sys.exit(1)


if __name__ == "__main__":
    main()
