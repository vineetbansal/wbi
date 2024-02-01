import argparse
from wbi.remote.remote import submit


def add_args(parser):
    parser.add_argument(
        "template",
        nargs="?",
        default="hello",
        help="Template to use for job script (default: %(default)s)",
    )
    parser.add_argument(
        "--hostname", type=str, required=True, help="Hostname of remote machine"
    )
    parser.add_argument(
        "--username", type=str, required=True, help="Username on remote machine"
    )
    parser.add_argument(
        "--cluster",
        default=False,
        action="store_true",
        help="Specify if you want to execute command using srun/sbatch",
    )
    parser.add_argument(
        "--timelimit",
        type=str,
        default=None,
        help="Time limit string to pass to slurm (--cluster mode only)",
    )
    parser.add_argument(
        "--interactive",
        default=False,
        action="store_true",
        help="Monitor and wait for job to finish (--cluster mode only)",
    )
    parser.add_argument(
        "--no-stdout",
        default=False,
        action="store_true",
        help="Suppress remote stdout",
    )
    parser.add_argument(
        "--stderr",
        default=False,
        action="store_true",
        help="Show remote stderr",
    )

    return parser


def main(args, **kwargs):
    submit(
        template_name=args.template,
        timelimit=args.timelimit,
        hostname=args.hostname,
        username=args.username,
        cluster=args.cluster,
        interactive=args.interactive,
        show_stdout=not args.no_stdout,
        show_stderr=args.stderr,
        **kwargs,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
