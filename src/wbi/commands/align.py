import argparse
import logging
from wbi.experiment import Experiment
from wbi.ui.image_align import image_align
from wbi import config


logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--input_folder",
        type=str,
        required=True,
        help="Path to folder containing data files",
    )
    parser.add_argument(
        "--output_folder",
        type=str,
        default=None,
        help="Path to the folder to save output files",
    )
    parser.add_argument(
        "--background_file",
        type=str,
        default=config.alignment.background_file,
        help="Path to the background file",
    )
    parser.add_argument(
        "--save_frame_values",
        action="store_true",
        help="Choose whether to save frame numbers with coordinates",
    )
    return parser


def main(args, **kwargs):
    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    input_folder, output_folder, background_file, save_frame_values = (
        args.input_folder,
        args.output_folder,
        args.background_file,
        args.save_frame_values,
    )

    logger.info(f"Input: {input_folder} Output: {output_folder}")

    experiment = Experiment(input_folder)
    image_align(experiment, output_folder, background_file, save_frame_values)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
