import argparse
import logging

logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--input_folder",
        type=str,
        required=True,
        help="Path to folder containing data files",
    )
    return parser


def main(args):

    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
