from jinja2 import Environment, PackageLoader, select_autoescape
import os.path
import paramiko
import tempfile


def submit(
    template_name,
    mins,
    remote_temp_dir="/scratch/gpfs/{username}/tmp",
    chdir=None,
    client=None,
    username=None,
    hostname=None,
    **kwargs,
):

    if client is None:
        assert (
            hostname is not None and username is not None
        ), "Specify hostname and username"
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username)
    else:
        hostname = client.get_transport().getpeername()[0]
        username = client.get_transport().get_username()

    env = Environment(
        loader=PackageLoader("wbi.remote.templates", package_path=""),
        autoescape=select_autoescape(),
    )

    template = env.get_template(f"{template_name}.jinja")
    jobfile = template.render(
        mins=mins, chdir=chdir, template_name=template_name, **kwargs
    )

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(jobfile.encode("utf8"))
    temp_file.close()

    remote_temp_dir = remote_temp_dir.format(username=username)

    temp_basename = os.path.basename(temp_file.name)
    remote_temp_script_path = os.path.join(remote_temp_dir, temp_basename)
    remote_temp_stdout_path = os.path.join(remote_temp_dir, f"{temp_basename}_stdout")
    with client.open_sftp() as sftp:
        sftp.put(temp_file.name, remote_temp_script_path)

    sbatch_flags = " ".join(
        [
            "--parsable",
            f"--time 00:{mins}:00",
            f"--chdir {chdir}" if chdir is not None else "",
            f"--out={remote_temp_stdout_path}",
        ]
    )
    cmd = f"sbatch {sbatch_flags} {remote_temp_script_path}"

    stdin, stdout, stderr = client.exec_command(cmd)
    job_id = int(stdout.read().decode())

    return job_id, remote_temp_stdout_path


def parse_remote_stdout(client, remote_temp_stdout_path):
    try:
        cmd = f"cat {remote_temp_stdout_path}"
        stdin, stdout, stderr = client.exec_command(cmd)
        return stdout.read().decode()
    except FileNotFoundError:
        return ""
