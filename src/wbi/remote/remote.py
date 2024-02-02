from jinja2 import Environment, PackageLoader, select_autoescape
import os.path
import paramiko
import tempfile
import logging

logger = logging.getLogger(__name__)


def connect(username, hostname):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username)

    return client


def submit(
    template_name,
    timelimit=None,
    hostname=None,
    username=None,
    cluster=False,
    interactive=False,
    show_stdout=True,
    show_stderr=False,
    remote_temp_dir="/scratch/gpfs/{username}/tmp",
    **kwargs,
):
    client = connect(username, hostname)

    env = Environment(
        loader=PackageLoader("wbi.remote.templates", package_path=""),
        autoescape=select_autoescape(),
    )

    template = env.get_template(f"{template_name}.jinja")
    jobfile = template.render(
        timelimit=timelimit, template_name=template_name, **kwargs
    )

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(jobfile.encode("utf8"))
    temp_file.close()

    remote_temp_dir = remote_temp_dir.format(username=username)

    temp_basename = os.path.basename(temp_file.name)
    remote_temp_script_path = os.path.join(remote_temp_dir, temp_basename)
    with client.open_sftp() as sftp:
        sftp.put(temp_file.name, remote_temp_script_path)
    client.exec_command(
        f"mkdir -p {remote_temp_dir} && chmod +x {remote_temp_script_path}"
    )

    if cluster:
        if interactive:
            assert timelimit is not None, "Specify Time limit"
            cmd_flags = (f"--time {timelimit}",)
            cmd = "srun"
        else:
            cmd_flags = (
                f"--time {timelimit}" if timelimit is not None else "",
                "--parsable",
            )
            cmd = "sbatch"

        cmd_flags = " ".join(cmd_flags)
        cmd = f"{cmd} {cmd_flags} {remote_temp_script_path}"
    else:
        cmd = f"bash -c {remote_temp_script_path}"

    logger.info(f"Executing remote command: {cmd}")
    _, stdout, stderr = client.exec_command(cmd)

    if cluster and not interactive:
        job_id = int(stdout.read().decode())
        logger.info(f"Submitted job with ID {job_id}")
    else:
        if show_stdout:
            stdout_str = "\n".join(stdout.readlines()).strip()
            logger.info(f"Remote stdout\n{stdout_str}")

        return_code = stdout.channel.recv_exit_status()
        if return_code != 0 or show_stderr:
            stderr = "\n".join(stderr.readlines()).strip()
            logger.info(f"Remote stderr\n{stderr}")

    client.close()
