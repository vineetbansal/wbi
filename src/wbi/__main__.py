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
    i = 0
    while i < len(unknown_args):
        key = unknown_args[i].lstrip("-")
        i += 1  # Move to the next item assuming it's a value
        if i < len(unknown_args) and not unknown_args[i].startswith("-"):
            value = unknown_args[i]
            i += 1  # Move past the value for the next iteration
        else:
            # If the current key is a boolean flag set its value to True
            value = True
        unknown_dict[key] = value

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    args.func(args, **unknown_dict)


if __name__ == "__main__":
    main()
