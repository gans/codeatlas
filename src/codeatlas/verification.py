"""Compare local artifacts to independently approved SHA-256 inventories."""
import hashlib
import json
import re
from pathlib import Path


def verify_directory(directory: Path, manifest: Path | None = None) -> None:
    manifest = manifest or directory.with_suffix('.sha256.json')
    expected = json.loads(manifest.read_text())
    if not directory.is_dir() or directory.is_symlink() or not expected:
        raise ValueError(f'Missing or invalid artifact bundle: {directory}')
    actual = {}
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError(f'Symlink in artifact bundle: {path}')
        if path.is_file():
            with path.open('rb') as stream:
                actual[path.relative_to(directory).as_posix()] = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError(f'Artifact inventory mismatch for {directory}')


def verify_jar():
    verify_file(Path('verified/postgresql.jar'), Path('security/postgresql-42.7.14.sha256'))
    verify_file(Path('verified/hadoop/bundle-2.24.6.jar'), Path('security/aws-sdk-bundle-2.24.6.sha256'))


def verify_file(jar: Path, checksum: Path):
    approved = checksum.read_text().strip()
    with jar.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if not re.fullmatch('[a-f0-9]{64}', approved) or actual != approved:
        raise ValueError(f'Digest mismatch: {jar}')
