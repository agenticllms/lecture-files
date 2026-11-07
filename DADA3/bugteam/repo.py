"""The huskyutils repository and its open issues. Given."""
import difflib
import json
import os
import shutil

from . import config


def load_issues():
    """The open issues, as GitHub returns them: number, title, body, user, labels."""
    with open(config.ISSUES_FILE) as f:
        return json.load(f)["issues"]


def issue_text(issue):
    """One issue as the agents read it."""
    return f"Issue #{issue['number']}: {issue['title']}\n(opened by {issue['user']})\n\n{issue['body']}"


def repo_files():
    """Every file in the repository, as {path: text}, with paths like 'huskyutils/text.py'."""
    files = {}
    for root, dirs, names in os.walk(config.REPO_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
        for name in names:
            if name.endswith((".py", ".md")):
                full = os.path.join(root, name)
                files[os.path.relpath(full, config.REPO_DIR)] = open(full).read()
    return dict(sorted(files.items()))


def diff(path, old, new):
    """A unified diff of one file, as in a pull request."""
    return "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                        f"a/{path}", f"b/{path}"))


def write_repo(out_dir, patches=()):
    """Copy the repository to out_dir and apply patches, each a dict with 'path' and 'code'."""
    shutil.rmtree(out_dir, ignore_errors=True)
    shutil.copytree(config.REPO_DIR, out_dir, ignore=shutil.ignore_patterns("__pycache__"))
    for patch in patches:
        target = os.path.realpath(os.path.join(out_dir, patch["path"]))
        if not target.startswith(os.path.realpath(out_dir) + os.sep):
            raise ValueError(f"A patch tried to write outside the repository: {patch['path']}")
        with open(target, "w") as f:
            f.write(patch["code"])
    return out_dir
