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
        "--max-frames", type=int, default=None, help="Max frames to process"
    )
    parser.add_argument("--plot", action="store_true", help="Plot centerlines")

    return parser


def main(args, **kwargs):
    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    logger.info(f"Input: {args.input_folder}")
    make_centerline(
        input_folder=args.input_folder,
        max_frames=args.max_frames,
        plot=args.plot,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
