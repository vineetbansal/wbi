import argparse
import logging
import paramiko
import time
from wbi.remote.remote_head import connect, parse_remote_stdout


logger = logging.getLogger(__name__)


def add_args(parser):
    parser.add_argument(
        "--hostname", type=str, required=True, help="Hostname of remote machine"
    )
    parser.add_argument(
        "--username", type=str, required=True, help="Username on remote machine"
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

    connect(client=client)

    while True:
        stdout = parse_remote_stdout(client)
        if "Hello" in stdout:
            break
        elif stdout == "":
            logger.info("Waiting...")
            time.sleep(5)
        else:
            logger.error(f"Unexpected output: {stdout}")

    stdout = parse_remote_stdout(client)
    logger.info(stdout)
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    args = add_args(parser).parse_args()
    main(args)
