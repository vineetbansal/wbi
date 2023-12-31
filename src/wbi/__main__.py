from wbi.commands import remote
from wbi.commands import flash_finder, centerline


def main():
    import argparse
    import os

    parser = argparse.ArgumentParser(description=__doc__)
    import wbi

    parser.add_argument("--version", action="version", version="wbi " + wbi.__version__)

    modules = (remote, flash_finder, centerline)

    subparsers = parser.add_subparsers(title="Choose a command")
    subparsers.required = True

    def get_str_name(module):
        return os.path.splitext(os.path.basename(module.__file__))[0]

    for module in modules:
        this_parser = subparsers.add_parser(
            get_str_name(module), description=module.__doc__
        )
        module.add_args(this_parser)
        this_parser.set_defaults(func=module.main)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
