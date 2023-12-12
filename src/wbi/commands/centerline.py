import argparse
import logging
from wbi.legacy.make_centerline import make_centerline

logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--input_folder",
        type=str,
        required=True,
        help="Path to folder containing data files",
    )
    parser.add_argument(
        "--model-path", type=str, required=True, help="Path to best_model.h5"
    )
    parser.add_argument(
        "--max-frames", type=int, default=None, help="Max frames to process"
    )
    parser.add_argument("--plot", action="store_true", help="Plot centerlines")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    return parser


def main(args):

    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    make_centerline(
        data_path=args.input_folder,
        model_path=args.model.path,
        max_frames=args.max_frames,
        plot=args.plot,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
