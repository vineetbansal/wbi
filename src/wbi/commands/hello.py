import argparse
import logging


logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--greeting", type=str, default="Hello", help="Greeting to print"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )
    parser.add_argument(
        "--num",
        type=int,
        default=3,
        help="Number of times to greet (default %(default)s)",
    )

    return parser


def main(args):
    if not isinstance(args, argparse.Namespace):
        args = add_args(argparse.ArgumentParser()).parse_args(args)

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.debug(f"Will greet {args.num} times")
    greeting = " ".join(args.num * [args.greeting])
    logger.info(greeting)
    return greeting


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
