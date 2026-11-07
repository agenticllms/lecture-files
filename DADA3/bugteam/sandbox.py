"""Sandboxes for running code, from W09b.2. Given.

    with open_sandbox() as (sandbox, workdir):
        upload_files(sandbox, repo_files(), f"{workdir}/original")
        print(sandbox.execute(f"cd {workdir}/original && python -m unittest discover -s tests").output)

The sandbox is deleted when the with block ends, even if the code inside it fails.
"""
import os
from contextlib import contextmanager
from pathlib import Path

import certifi

from . import config

os.environ.setdefault("SSL_CERT_FILE", certifi.where())   # python.org Python on a Mac, as in W09b.2


@contextmanager
def open_sandbox():
    """A new sandbox with no network. Yields (sandbox, workdir), where workdir is the folder the
    sandbox's user can write to."""
    if config.SANDBOX == "docker":
        from .docker_sandbox import DockerSandbox
        sandbox = DockerSandbox(timeout=60)
        try:
            yield sandbox, "/workspace"
        finally:
            sandbox.stop()
        return
    from daytona import CreateSandboxFromSnapshotParams, Daytona
    from langchain_daytona import DaytonaSandbox
    remote = Daytona().create(CreateSandboxFromSnapshotParams(language="python", network_block_all=True, ephemeral=True))
    try:
        yield DaytonaSandbox(sandbox=remote, timeout=60), "/home/daytona"
    finally:
        remote.delete()


def upload_files(sandbox, files, folder):
    """Put {path: text} files into the sandbox under folder."""
    responses = sandbox.upload_files([(f"{folder}/{path}", text.encode()) for path, text in files.items()])
    failed = [r.path for r in responses if r.error]
    if failed:
        raise RuntimeError(f"Could not upload {failed}")


def read_sandbox_file(sandbox, path):
    """The text of one file in the sandbox, or '' if it is not there."""
    f = sandbox.download_files([path])[0]
    return "" if f.error else f.content.decode(errors="replace")


def save_files(sandbox, folder, local_dir):
    """Copy the files under folder in the sandbox to local_dir, as in W09b.2. The paths come from the
    sandbox, so each one is checked to stay inside local_dir before it is written."""
    local_dir = Path(local_dir).resolve()
    paths = [m["path"] for m in sandbox.glob("**/*", path=folder).matches]
    saved = []
    for f in sandbox.download_files(paths):
        target = (local_dir / Path(f.path).relative_to(folder)).resolve()
        if f.error or not target.is_relative_to(local_dir) or "__pycache__" in target.parts:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f.content)
        saved.append(str(target.relative_to(local_dir)))
    return saved
