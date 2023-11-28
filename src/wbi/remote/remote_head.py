import paramiko


def connect(client=None, username=None, hostname=None):
    if client is None:
        assert (
            hostname is not None and username is not None
        ), "Specify hostname and username"
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username)


def parse_remote_stdout(client):
    try:
        cmd = 'bash -c "echo Hello $(hostname)"'
        stdin, stdout, stderr = client.exec_command(cmd)
        return stdout.read().decode()
    except FileNotFoundError:
        return ""
