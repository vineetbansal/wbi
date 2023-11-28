import argparse
import logging
import paramiko
import time
from wbi.remote.remote import submit, parse_remote_stdout


logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--hostname", type=str, required=True, help="Hostname of remote machine"
    )
    parser.add_argument(
        "--username", type=str, required=True, help="Username on remote machine"
    )
    parser.add_argument(
        "--template",
        type=str,
        default="hello",
        help="Template to use for job script (default: hello)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Increase verbosity"
    )

    return parser


def main(args):
    hostname, username = args.hostname, args.username
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username)

    job_id, remote_temp_stdout_path = submit(
        template=args.template, mins=1, client=client
    )
    logger.info(f"Submitted job with ID {job_id}")
    logger.info(f"Remote stdout path: {remote_temp_stdout_path}")

    while True:
        stdout = parse_remote_stdout(client, remote_temp_stdout_path)
        if "Hello" in stdout:
            break
        elif stdout == "":
            logger.info("Job has not started yet. Waiting 5 seconds.")
            time.sleep(5)
        else:
            logger.error(f"Unexpected output: {stdout}")

    stdout = parse_remote_stdout(client, remote_temp_stdout_path)
    logger.info(stdout)
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
