import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from .schemas import FILE
from .storage import write_rows

LANGUAGES = {'.java': 'java', '.kt': 'kotlin', '.ts': 'typescript', '.py': 'python'}


def generate(repo: Path, output: Path, when: datetime | None = None) -> Path:
    """Read tracked source files at HEAD, not the mutable working tree."""
    def git(*args: str) -> bytes:
        return subprocess.check_output(['git', '-C', str(repo), *args])
    commit = git('rev-parse', 'HEAD').decode().strip()
    paths = git('ls-tree', '-r', '--name-only', '-z', commit).decode().split('\0')
    rows = []
    for path in sorted(paths):
        language = LANGUAGES.get(Path(path).suffix)
        if not language:
            continue
        content = git('show', f'{commit}:{path}').decode('utf-8')
        rows.append(dict(repository=repo.resolve().name, commit=commit, path=path, language=language,
                         content=content, content_hash=hashlib.sha256(content.encode()).hexdigest()))
    date = (when or datetime.now(timezone.utc)).astimezone(timezone.utc)
    target = output / 'ingest_name=github_file_v2' / f'year={date:%Y}' / f'month={date:%m}' / f'day={date:%d}' / f'timestamp={date:%Y%m%dT%H%M%SZ}' / 'parquet-files' / 'part-00000.parquet'
    write_rows(target, rows, FILE)
    return target
