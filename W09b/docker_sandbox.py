"""A deep-agents sandbox backend that runs every command inside a Docker container.

BaseSandbox builds all the file tools (ls, read_file, write_file, edit_file, glob, grep) on top of four
methods, so these four are all a sandbox has to provide. Needs Docker Desktop running.
"""
import shlex
import subprocess

from deepagents.backends.protocol import ExecuteResponse, FileDownloadResponse, FileUploadResponse
from deepagents.backends.sandbox import BaseSandbox


class DockerSandbox(BaseSandbox):
    """A fresh container per sandbox: no network by default, limited memory and CPU, removed on stop()."""

    def __init__(self, image="python:3.12-slim", network=False, memory="512m", cpus="1", timeout=60):
        args = ["docker", "run", "--detach", "--rm", "--memory", memory, "--cpus", cpus,
                "--workdir", "/workspace"]
        if not network:
            args += ["--network", "none"]
        result = subprocess.run(args + [image, "sleep", "infinity"], capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Could not start a container. Is Docker running?\n{result.stderr}")
        self._id = result.stdout.strip()
        self.timeout = timeout

    @property
    def id(self) -> str:
        return self._id

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        limit = timeout or self.timeout
        try:
            r = subprocess.run(["docker", "exec", self._id, "sh", "-c", command],
                               capture_output=True, text=True, timeout=limit)
        except subprocess.TimeoutExpired:
            return ExecuteResponse(output=f"Command timed out after {limit} s.", exit_code=124)
        output = r.stdout + ("\n" + r.stderr if r.stderr else "")
        return ExecuteResponse(output=output, exit_code=r.returncode)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        responses = []
        for path, content in files:
            q = shlex.quote(path)
            r = subprocess.run(["docker", "exec", "-i", self._id, "sh", "-c", f"mkdir -p \"$(dirname {q})\" && cat > {q}"],
                               input=content, capture_output=True)
            responses.append(FileUploadResponse(path=path, error=None if r.returncode == 0 else "permission_denied"))
        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        responses = []
        for path in paths:
            r = subprocess.run(["docker", "exec", self._id, "cat", path], capture_output=True)
            if r.returncode == 0:
                responses.append(FileDownloadResponse(path=path, content=r.stdout, error=None))
            else:
                responses.append(FileDownloadResponse(path=path, content=None, error="file_not_found"))
        return responses

    def stop(self):
        subprocess.run(["docker", "rm", "--force", self._id], capture_output=True)
