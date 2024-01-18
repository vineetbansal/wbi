import argparse
import logging
from wbi.experiment import Experiment

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
        "--chunksize", type=int, required=False, help="Approximate number of frames"
    )
    return parser


def main(args):
    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    input_folder, output_folder, chunksize = (
        args.input_folder,
        args.output_folder,
        args.chunksize,
    )
    logger.info(f"Input: {input_folder} Output: {output_folder} ChunkSize: {chunksize}")

    experiment = Experiment(input_folder)
    experiment.flash_finder(
        output_folder=output_folder,
        chunk_size=chunksize,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
