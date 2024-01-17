import argparse
import logging
from wbi.experiment import Experiment
from wbi.ui.image_align import image_align

logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--input_folder",
        type=str,
        required=True,
        help="Path to folder containing data files",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    return parser


def main(args):
    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug("Input folder needs to have sCMOS_Frames_U16_1024x512.dat")

    logger.info(f"Input: { args.input_folder}")

    experiment = Experiment(args.input_folder)
    image_align(experiment)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
