"""Collect committed Git evidence without altering the checkout."""
import hashlib
import subprocess

from .core import ContractError


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode:
        # Do not echo remote URLs, arbitrary command output or credentials.
        raise ContractError(f"Git evidence operation failed (exit {result.returncode})")
    try:
        return result.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ContractError("Evidence must be UTF-8 text") from exc


def collect(repo, base, head, documents):
    if any(not isinstance(ref, str) or ref.startswith("-") for ref in [base, head]):
        raise ContractError("Invalid Git reference")
    base_sha = git(repo, "rev-parse", "--verify", f"{base}^{{commit}}").strip()
    head_sha = git(repo, "rev-parse", "--verify", f"{head}^{{commit}}").strip()
    diff = git(repo, "diff", "--no-ext-diff", "--no-textconv", "--unified=8", base_sha, head_sha, "--")

    def entry(id_, kind, source, text):
        return {"id": id_, "kind": kind, "source": source, "text": text,
                "sha256": hashlib.sha256(text.encode()).hexdigest()}

    evidence = [entry("DIFF-001", "change_diff", f"{base_sha}..{head_sha}", diff)]
    for index, path in enumerate(sorted(set(documents)), 1):
        if not path or path.startswith(("/", "-")) or ".." in path.split("/"):
            raise ContractError("Document paths must be repository-relative")
        text = git(repo, "show", f"{head_sha}:{path}")
        evidence.append(entry(f"DOC-{index:03d}", "requirement_document", path, text))
    return {"version": 1, "base_commit": base_sha, "head_commit": head_sha, "evidence": evidence}
