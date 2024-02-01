import logging
from wbi.commands import remote
from wbi.commands import flash_finder, centerline, align

logger = logging.getLogger("wbi")


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    import wbi

    parser.add_argument("--version", action="version", version="wbi " + wbi.__version__)

    modules = (remote, flash_finder, centerline, align)

    subparsers = parser.add_subparsers(title="Choose a command")
    subparsers.required = True

    def get_str_name(module):
        return os.path.splitext(os.path.basename(module.__file__))[0]

    for module in modules:
        this_parser = subparsers.add_parser(
            get_str_name(module), description=module.__doc__
        )
        module_parser = module.add_args(this_parser)
        module_parser.add_argument(
            "-v", "--verbose", action="store_true", help="Increase verbosity"
        )
        this_parser.set_defaults(func=module.main)

    args, unknown_args = parser.parse_known_args()

    unknown_dict = {}
    if unknown_args:
        for i in range(0, len(unknown_args), 2):
            key = unknown_args[i].lstrip("--")
            value = unknown_args[i + 1] if i + 1 < len(unknown_args) else ""
            unknown_dict[key] = value

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    args.func(args, **unknown_dict)


if __name__ == "__main__":
    main()
